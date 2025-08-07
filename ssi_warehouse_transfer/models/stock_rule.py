# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _name = "stock.rule"
    _inherit = ["stock.rule"]

    def _get_custom_move_fields(self):
        _super = super()
        result = _super._get_custom_move_fields()
        result += [
            "warehouse_transfer_line_ids",
        ]
        return result

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        _super = super()
        result = _super._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        move_dest_ids = result.get("move_dest_ids", False)
        warehouse_transfer_line_ids = []
        if move_dest_ids:
            for move_dest_tupple in move_dest_ids:
                move = self.env["stock.move"].browse(move_dest_tupple[1])
                if move.warehouse_transfer_line_ids:
                    warehouse_transfer_line_ids += move.warehouse_transfer_line_ids.ids
                    result.update(
                        {
                            "warehouse_transfer_line_ids": [
                                (6, 0, warehouse_transfer_line_ids)
                            ],
                        }
                    )
        return result
