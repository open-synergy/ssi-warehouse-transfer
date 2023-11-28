# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move"]

    warehouse_transfer_line_ids = fields.Many2many(
        string="Warehouse Transfer Line",
        comodel_name="warehouse_transfer_line",
        relation="rel_warehouse_transfer_line_2_stock_move",
        column1="move_id",
        column2="line_id",
    )
