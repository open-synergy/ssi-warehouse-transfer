# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class WarehouseTransferLIne(models.Model):
    _name = "warehouse_transfer_line"
    _description = "Warehouse Transfer Line"
    _inherit = [
        "mixin.product_line",
    ]

    transfer_id = fields.Many2one(
        comodel_name="warehouse_transfer",
        string="# Warehouse Transfer",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    stock_move_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Stock Moves",
        relation="rel_warehouse_transfer_line_2_stock_move",
        column1="line_id",
        column2="move_id",
        copy=False,
    )
    product_id = fields.Many2one(
        required=True,
    )
    uom_id = fields.Many2one(
        required=True,
    )
    qty_to_receive = fields.Float(
        string="Qty to Receive", compute="_compute_qty_to_receive", store=True
    )
    qty_incoming = fields.Float(
        string="Qty Incoming",
        compute="_compute_qty_incoming",
    )
    qty_received = fields.Float(
        string="Qty Received", compute="_compute_qty_received", store=True
    )
    qty_to_deliver = fields.Float(
        string="Qty to Deliver", compute="_compute_qty_to_deliver", store=True
    )
    qty_outgoing = fields.Float(
        string="Qty Outgoing",
        compute="_compute_qty_outgoing",
    )
    qty_delivered = fields.Float(
        string="Qty Delivered", compute="_compute_qty_delivered", store=True
    )

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "qty_delivered",
        "qty_received",
        "qty_incoming",
        "transfer_id.state",
    )
    def _compute_qty_to_receive(self):
        for record in self:
            record.qty_to_receive = (
                record.qty_delivered - record.qty_incoming - record.qty_received
            )

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "transfer_id.state",
    )
    def _compute_qty_incoming(self):
        for record in self:
            states = [
                "draft",
                "confirmed",
                "partially_available",
                "assigned",
            ]
            record.qty_incoming = record._get_move_qty(states, "in")

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "transfer_id.state",
    )
    def _compute_qty_received(self):
        for record in self:
            states = [
                "done",
            ]
            record.qty_received = record._get_move_qty(states, "in")

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "uom_quantity",
        "qty_delivered",
        "qty_outgoing",
        "qty_incoming",
        "qty_received",
        "qty_to_receive",
        "transfer_id.state",
    )
    def _compute_qty_to_deliver(self):
        for record in self:
            record.qty_to_deliver = (
                record.uom_quantity - record.qty_outgoing - record.qty_delivered
            )

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "transfer_id.state",
    )
    def _compute_qty_outgoing(self):
        for record in self:
            states = [
                "draft",
                "confirmed",
                "partially_available",
                "assigned",
            ]
            record.qty_outgoing = record._get_move_qty(states, "out")

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.state",
        "stock_move_ids.product_qty",
        "transfer_id.state",
    )
    def _compute_qty_delivered(self):
        for record in self:
            states = [
                "done",
            ]
            record.qty_delivered = record._get_move_qty(states, "out")

    def _get_move_qty(self, states, direction):
        result = 0.0
        outbound_location = self.transfer_id.outbound_location_id
        inbound_location = self.transfer_id.inbound_location_id
        if direction == "in":
            for move in self.stock_move_ids.filtered(
                lambda m: m.state in states and m.location_dest_id == inbound_location
            ):
                result += move.product_qty
        else:
            for move in self.stock_move_ids.filtered(
                lambda m: m.state in states and m.location_id == outbound_location
            ):
                result += move.product_qty
        return result

    def _create_picking(self):
        self.ensure_one()
        group = self.transfer_id.procurement_group_id
        qty = self.qty_to_deliver
        values = self._get_procurement_data()

        procurements = []
        try:
            procurement = group.Procurement(
                self.product_id,
                qty,
                self.uom_id,
                values.get("location_id"),
                values.get("origin"),
                values.get("origin"),
                self.env.company,
                values,
            )

            procurements.append(procurement)
            self.env["procurement.group"].with_context(rma_route_check=[True]).run(
                procurements
            )
        except UserError as error:
            raise UserError(error)

    def _get_procurement_data(self):
        group = self.transfer_id.procurement_group_id
        origin = self.transfer_id.name
        warehouse = self.transfer_id.inbound_warehouse_id
        location = self.transfer_id.inbound_location_id
        route = self.transfer_id.route_id
        result = {
            "name": origin,
            "group_id": group,
            "origin": origin,
            "warehouse_id": warehouse,
            "date_planned": fields.Datetime.now(),
            "product_id": self.product_id.id,
            "product_qty": self.qty_to_deliver,
            "partner_id": False,
            "product_uom": self.uom_id.id,
            "location_id": location,
            "route_ids": route,
            "warehouse_transfer_line_ids": [(4, self.id)],
        }
        return result
