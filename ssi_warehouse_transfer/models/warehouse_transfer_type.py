# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WarehouseTransferType(models.Model):
    _name = "warehouse_transfer_type"
    _description = "Warehouse Transfer Type"
    _inherit = [
        "mixin.master_data",
        "mixin.inbound_stock_warehouse_m2o_configurator",
        "mixin.outbound_stock_warehouse_m2o_configurator",
        "mixin.stock_route_m2o_configurator",
        "mixin.stock_route_m2o_configurator",
        "mixin.inbound_stock_location_m2o_configurator",
        "mixin.outbound_stock_location_m2o_configurator",
        "mixin.product_category_m2o_configurator",
        "mixin.product_product_m2o_configurator",
    ]

    _inbound_stock_warehouse_m2o_configurator_insert_form_element_ok = True
    _inbound_stock_warehouse_m2o_configurator_form_xpath = "//page[@name='inventory']"
    _outbound_stock_warehouse_m2o_configurator_insert_form_element_ok = True
    _outbound_stock_warehouse_m2o_configurator_form_xpath = "//page[@name='inventory']"
    _stock_route_m2o_configurator_insert_form_element_ok = True
    _stock_route_m2o_configurator_form_xpath = "//page[@name='inventory']"
    _outbound_stock_location_m2o_configurator_insert_form_element_ok = True
    _outbound_stock_location_m2o_configurator_form_xpath = "//page[@name='inventory']"
    _inbound_stock_location_m2o_configurator_insert_form_element_ok = True
    _inbound_stock_location_m2o_configurator_form_xpath = "//page[@name='inventory']"
    _product_category_m2o_configurator_insert_form_element_ok = True
    _product_category_m2o_configurator_form_xpath = "//page[@name='product']"
    _product_product_m2o_configurator_insert_form_element_ok = True
    _product_product_m2o_configurator_form_xpath = "//page[@name='product']"

    inbound_warehouse_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_inbound_warehouse",
        column1="type_id",
        column2="warehouse_id",
    )
    outbound_warehouse_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_outbound_warehouse",
        column1="type_id",
        column2="warehouse_id",
    )
    route_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_route",
        column1="type_id",
        column2="route_id",
    )
    inbound_location_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_inbound_location",
        column1="type_id",
        column2="location_id",
    )
    outbound_location_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_outbound_location",
        column1="type_id",
        column2="location_id",
    )
    product_category_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_product_category",
        column1="type_id",
        column2="category_id",
    )
    product_ids = fields.Many2many(
        relation="rel_warehouse_transfer_type_2_product_product",
        column1="type_id",
        column2="product_id",
    )
