# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestWarehouseTransfer(YamlTransactionCase):
    def _make_transfer(self, code, with_line=True, uom_quantity=5.0):
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        location = self.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1
        )
        route = self.env["stock.location.route"].create(
            {"name": "Test Route %s" % code}
        )
        transfer_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type %s" % code, "code": code[:10]}
        )
        admin = self.env.ref("base.user_admin")
        vals = {
            "date": fields.Date.today(),
            "type_id": transfer_type.id,
            "outbound_warehouse_id": warehouse.id,
            "inbound_warehouse_id": warehouse.id,
            "route_id": route.id,
            "outbound_location_id": location.id,
            "inbound_location_id": location.id,
        }
        if with_line:
            uom = self.env.ref("uom.product_uom_unit")
            product = self.env["product.product"].create({"name": "Product %s" % code})
            vals["line_ids"] = [
                (
                    0,
                    0,
                    {
                        "name": "Line %s" % code,
                        "product_id": product.id,
                        "uom_id": uom.id,
                        "uom_quantity": uom_quantity,
                        "sequence": 10,
                    },
                )
            ]
        return self.env["warehouse_transfer"].with_user(admin).create(vals)

    def test_warehouse_transfer(self):
        self.run_yaml_scenario("test_data_warehouse_transfer.yaml")

    def test_check_line_ids_raises_validation_error(self):
        transfer = self._make_transfer("NOLINES", with_line=False)
        admin = self.env.ref("base.user_admin")
        with self.assertRaises(ValidationError):
            transfer.with_user(admin).with_context(
                bypass_policy_check=True
            ).action_confirm()

    def test_check_double_items_raises_validation_error(self):
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        location = self.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1
        )
        route = self.env["stock.location.route"].create({"name": "Test Route Dup"})
        product = self.env["product.product"].create({"name": "Test Dup Product WT"})
        uom = self.env.ref("uom.product_uom_unit")
        transfer_type = self.env["warehouse_transfer_type"].create(
            {"name": "Dup Type", "code": "DUPTW"}
        )
        admin = self.env.ref("base.user_admin")
        transfer = (
            self.env["warehouse_transfer"]
            .with_user(admin)
            .create(
                {
                    "date": fields.Date.today(),
                    "type_id": transfer_type.id,
                    "outbound_warehouse_id": warehouse.id,
                    "inbound_warehouse_id": warehouse.id,
                    "route_id": route.id,
                    "outbound_location_id": location.id,
                    "inbound_location_id": location.id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Line 1",
                                "product_id": product.id,
                                "uom_id": uom.id,
                                "uom_quantity": 5.0,
                                "sequence": 10,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Line 2",
                                "product_id": product.id,
                                "uom_id": uom.id,
                                "uom_quantity": 5.0,
                                "sequence": 20,
                            },
                        ),
                    ],
                }
            )
        )
        with self.assertRaises(ValidationError):
            transfer.with_user(admin).with_context(
                bypass_policy_check=True
            ).action_confirm()

    def test_procurement_group_creation(self):
        transfer = self._make_transfer("PGTEST")
        transfer.sudo()._01_create_procurement_group()
        transfer.invalidate_cache()
        self.assertTrue(transfer.procurement_group_id)
        self.assertEqual(transfer.procurement_group_id.name, transfer.name)

    def test_action_done_from_open(self):
        transfer = self._make_transfer("DONETEST")
        admin = self.env.ref("base.user_admin")
        transfer.sudo().write({"state": "open"})
        transfer.invalidate_cache()
        self.assertEqual(transfer.state, "open")
        transfer.with_user(admin).with_context(bypass_policy_check=True).action_done()
        self.assertEqual(transfer.state, "done")

    def test_onchange_type_id_clears_outbound_warehouse(self):
        transfer_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type OC1", "code": "TOC1"}
        )
        new_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type OC2", "code": "TOC2"}
        )
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        form = Form(self.env["warehouse_transfer"])
        form.type_id = transfer_type
        if warehouse:
            form.outbound_warehouse_id = warehouse
        form.type_id = new_type
        self.assertFalse(form.outbound_warehouse_id._origin)

    def test_onchange_type_id_clears_inbound_warehouse(self):
        transfer_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type OC3", "code": "TOC3"}
        )
        new_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type OC4", "code": "TOC4"}
        )
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        form = Form(self.env["warehouse_transfer"])
        form.type_id = transfer_type
        if warehouse:
            form.inbound_warehouse_id = warehouse
        form.type_id = new_type
        self.assertFalse(form.inbound_warehouse_id._origin)

    def test_onchange_outbound_warehouse_clears_outbound_location(self):
        transfer_type = self.env["warehouse_transfer_type"].create(
            {"name": "Type OC5", "code": "TOC5"}
        )
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        location = self.env["stock.location"].search(
            [("usage", "=", "internal")], limit=1
        )
        form = Form(self.env["warehouse_transfer"])
        form.type_id = transfer_type
        if warehouse:
            form.outbound_warehouse_id = warehouse
        if location:
            form.outbound_location_id = location
        if warehouse:
            new_warehouse = self.env["stock.warehouse"].create(
                {"name": "Test WH OC", "code": "TWHOC"}
            )
            form.outbound_warehouse_id = new_warehouse
        self.assertFalse(form.outbound_location_id._origin)
