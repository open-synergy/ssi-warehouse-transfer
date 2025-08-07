# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.ssi_decorator import ssi_decorator


class WarehouseTransfer(models.Model):
    _name = "warehouse_transfer"
    _description = "Warehouse Transfer"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_terminate",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_confirm",
        "mixin.many2one_configurator",
    ]

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_multiple_approval_page = True
    _automatically_insert_open_policy_fields = False
    _automatically_insert_open_button = False
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False

    _statusbar_visible_label = "draft,confirm,open,done"
    _policy_field_order = [
        "confirm_ok",
        "open_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "%(ssi_transaction_terminate_mixin.base_select_terminate_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_open",
        "dom_reject",
        "dom_done",
        "dom_terminate",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "open"

    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        comodel_name="warehouse_transfer_type",
        string="Type",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    outbound_warehouse_id = fields.Many2one(
        string="Outbound Warehouse",
        comodel_name="stock.warehouse",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    inbound_warehouse_id = fields.Many2one(
        string="Inbound Warehouse",
        comodel_name="stock.warehouse",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    route_id = fields.Many2one(
        string="Route",
        comodel_name="stock.location.route",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    outbound_location_id = fields.Many2one(
        string="Inbound Location",
        comodel_name="stock.location",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    inbound_location_id = fields.Many2one(
        string="Inbound Location",
        comodel_name="stock.location",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Allowed Products",
        compute="_compute_allowed_product_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_product_category_ids = fields.Many2many(
        comodel_name="product.category",
        string="Allowed Product Category",
        compute="_compute_allowed_product_category_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_inbound_warehouse_ids = fields.Many2many(
        comodel_name="stock.warehouse",
        string="Allowed Inbound Warehouses",
        compute="_compute_allowed_inbound_warehouse_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_route_ids = fields.Many2many(
        comodel_name="stock.location.route",
        string="Allowed Routes",
        compute="_compute_allowed_route_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_inbound_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Allowed Inbound Locations",
        compute="_compute_allowed_inbound_location_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_outbound_warehouse_ids = fields.Many2many(
        comodel_name="stock.warehouse",
        string="Allowed Outbound Warehouses",
        compute="_compute_allowed_outbound_warehouse_ids",
        store=False,
        compute_sudo=True,
    )
    allowed_outbound_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Allowed Outbound Locations",
        compute="_compute_allowed_outbound_location_ids",
        store=False,
        compute_sudo=True,
    )
    procurement_group_id = fields.Many2one(
        string="Procurement Group",
        comodel_name="procurement.group",
        readonly=True,
        copy=False,
    )
    line_ids = fields.One2many(
        comodel_name="warehouse_transfer_line",
        inverse_name="transfer_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    qty_to_receipt = fields.Float(
        string="Qty To Receipt",
        compute="_compute_qty_to_receipt",
        store=True,
    )
    qty_to_deliver = fields.Float(
        string="Qty To Deliver",
        compute="_compute_qty_to_deliver",
        store=True,
    )
    qty_received = fields.Float(
        string="Qty Received",
        compute="_compute_qty_received",
        store=True,
    )
    qty_delivered = fields.Float(
        string="Qty Delivered",
        compute="_compute_qty_delivered",
        store=True,
    )
    uom_quantity = fields.Float(
        string="UoM Quantity",
        compute="_compute_uom_quantity",
        store=True,
    )
    resolve_ok = fields.Boolean(
        string="Resolve Ok",
        compute="_compute_resolve_ok",
        store=True,
    )

    @api.depends(
        "qty_received",
        "uom_quantity",
        "qty_delivered",
        "state",
    )
    def _compute_resolve_ok(self):
        for record in self:
            result = False
            if record.uom_quantity == record.qty_received and record.state == "open":
                result = True
            record.resolve_ok = result

    @api.depends(
        "line_ids",
        "line_ids.uom_quantity",
    )
    def _compute_uom_quantity(self):
        for record in self:
            result = 0.0
            for line in record.line_ids:
                result += line.uom_quantity
            record.uom_quantity = result

    @api.depends(
        "line_ids",
        "line_ids.qty_to_receive",
    )
    def _compute_qty_to_receipt(self):
        for record in self:
            result = 0.0
            for line in record.line_ids:
                result += line.qty_to_receive
            record.qty_to_receipt = result

    @api.depends(
        "line_ids",
        "line_ids.qty_to_deliver",
    )
    def _compute_qty_to_deliver(self):
        for record in self:
            result = 0.0
            for line in record.line_ids:
                result += line.qty_to_deliver
            record.qty_to_deliver = result

    @api.depends(
        "line_ids",
        "line_ids.qty_received",
    )
    def _compute_qty_received(self):
        for record in self:
            result = 0.0
            for line in record.line_ids:
                result += line.qty_received
            record.qty_received = result

    @api.depends(
        "line_ids",
        "line_ids.qty_delivered",
    )
    def _compute_qty_delivered(self):
        for record in self:
            result = 0.0
            for line in record.line_ids:
                result += line.qty_delivered
            record.qty_delivered = result

    # @api.depends(
    #     "qty_to_receipt",
    #     "state",
    # )
    # def _compute_receipt_ok(self):
    #     for record in self:
    #         result = False
    #         if record.qty_to_receipt > 0.0 and record.state == "open":
    #             result = True
    #         record.receipt_ok = result

    # @api.depends(
    #     "qty_to_deliver",
    #     "state",
    # )
    # def _compute_deliver_ok(self):
    #     for record in self:
    #         result = False
    #         if record.qty_to_deliver > 0.0 and record.state == "open":
    #             result = True
    #         record.deliver_ok = result

    @api.depends("type_id")
    def _compute_allowed_product_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="product.product",
                    method_selection=record.type_id.product_selection_method,
                    manual_recordset=record.type_id.product_ids,
                    domain=record.type_id.product_domain,
                    python_code=record.type_id.product_python_code,
                )
            record.allowed_product_ids = result

    @api.depends("type_id")
    def _compute_allowed_product_category_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="product.category",
                    method_selection=record.type_id.product_category_selection_method,
                    manual_recordset=record.type_id.product_category_ids,
                    domain=record.type_id.product_category_domain,
                    python_code=record.type_id.product_category_python_code,
                )
            record.allowed_product_category_ids = result

    @api.depends("type_id")
    def _compute_allowed_inbound_warehouse_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.warehouse",
                    method_selection=record.type_id.inbound_warehouse_selection_method,
                    manual_recordset=record.type_id.inbound_warehouse_ids,
                    domain=record.type_id.inbound_warehouse_domain,
                    python_code=record.type_id.inbound_warehouse_python_code,
                )
            record.allowed_inbound_warehouse_ids = result

    @api.depends("type_id", "inbound_warehouse_id")
    def _compute_allowed_route_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.location.route",
                    method_selection=record.type_id.route_selection_method,
                    manual_recordset=record.type_id.route_ids,
                    domain=record.type_id.route_domain,
                    python_code=record.type_id.route_python_code,
                )
            record.allowed_route_ids = result

    @api.depends("type_id", "inbound_warehouse_id")
    def _compute_allowed_inbound_location_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.location",
                    method_selection=record.type_id.inbound_location_selection_method,
                    manual_recordset=record.type_id.inbound_location_ids,
                    domain=record.type_id.inbound_location_domain,
                    python_code=record.type_id.inbound_location_python_code,
                )
            record.allowed_inbound_location_ids = result

    @api.depends("type_id")
    def _compute_allowed_outbound_warehouse_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.warehouse",
                    method_selection=record.type_id.outbound_warehouse_selection_method,
                    manual_recordset=record.type_id.outbound_warehouse_ids,
                    domain=record.type_id.outbound_warehouse_domain,
                    python_code=record.type_id.outbound_warehouse_python_code,
                )
            record.allowed_outbound_warehouse_ids = result

    @api.depends("type_id", "outbound_warehouse_id")
    def _compute_allowed_outbound_route_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.location.route",
                    method_selection=record.type_id.outbound_route_selection_method,
                    manual_recordset=record.type_id.outbound_route_ids,
                    domain=record.type_id.outbound_route_domain,
                    python_code=record.type_id.outbound_route_python_code,
                )
            record.allowed_outbound_route_ids = result

    @api.depends("type_id", "outbound_warehouse_id")
    def _compute_allowed_outbound_location_ids(self):
        for record in self:
            result = False
            if record.type_id:
                result = record._m2o_configurator_get_filter(
                    object_name="stock.location",
                    method_selection=record.type_id.outbound_location_selection_method,
                    manual_recordset=record.type_id.outbound_location_ids,
                    domain=record.type_id.outbound_location_domain,
                    python_code=record.type_id.outbound_location_python_code,
                )
            record.allowed_outbound_location_ids = result

    @api.onchange(
        "type_id",
    )
    def onchange_outbound_warehouse_id(self):
        self.outbound_warehouse_id = False

    @api.onchange(
        "outbound_warehouse_id",
    )
    def onchange_outbound_location_id(self):
        self.outbound_location_id = False

    @api.onchange(
        "type_id",
    )
    def onchange_inbound_warehouse_id(self):
        self.inbound_warehouse_id = False

    @api.onchange(
        "inbound_warehouse_id",
    )
    def onchange_inbound_location_id(self):
        self.inbound_location_id = False

    @api.onchange(
        "inbound_warehouse_id",
    )
    def onchange_route_id(self):
        self.route_id = False

    @api.onchange(
        "type_id",
    )
    def onchange_policy_template_id(self):
        template_id = self._get_template_policy()
        self.policy_template_id = template_id

    def action_create_picking(self):
        for record in self.sudo():
            record._02_create_picking()

    @ssi_decorator.post_open_action()
    def _02_create_picking(self):
        self.ensure_one()
        for line in self.line_ids:
            line._create_picking()

    @ssi_decorator.post_open_action()
    def _01_create_procurement_group(self):
        self.ensure_one()

        if self.procurement_group_id:
            return True

        PG = self.env["procurement.group"]
        group = PG.create(self._prepare_create_procurement_group())
        self.write(
            {
                "procurement_group_id": group.id,
            }
        )

    def _prepare_create_procurement_group(self):
        self.ensure_one()
        return {
            "name": self.name,
        }

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "cancel_ok",
            "open_ok",
            "terminate_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch

    @ssi_decorator.pre_confirm_check()
    def _check_double_items(self):
        self.ensure_one()
        product_ids = self.line_ids.product_id
        for product_id in product_ids:
            current_product_ids = self.line_ids.filtered(
                lambda line: line.product_id.id == product_id.id
            )
            if len(current_product_ids) > 1:
                raise ValidationError(
                    _(
                        f"The same product cannot be entered twice: {product_id.display_name}."
                    )
                )
