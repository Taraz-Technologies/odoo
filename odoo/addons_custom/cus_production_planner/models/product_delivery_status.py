from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductDeliveryStatus(models.Model):
    _name = 'product.delivery.status'
    _description = 'Delivery Product Status'
    _rec_name = 'display_name'
    _order = 'x_expected_date'

    x_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string="Picking",
        required=False,
    )
    x_move_id = fields.Many2one(
        comodel_name='stock.move',
        string="Stock Move",
        required=False,
    )
    x_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        required=False,
    )
    x_manufacturing_id = fields.Many2one(
        comodel_name='mrp.production',
        string="Manufacturing",
        compute="_compute_manufacturing",
        store=True,
    )
    x_mrp_demand_id = fields.Many2one(
        comodel_name='mrp.source.details',
        string="MRP Demand",
        required=False,
        compute="_compute_manufacturing",
        store=True,
    )
    x_expected_date = fields.Datetime(
        string="Expected Date",
        compute='_compute_expected_date',
        store=True,
    )
    x_quantity = fields.Float(string="Quantity", required=False)
    x_completion = fields.Float(string="Completion", required=False)
    x_status = fields.Selection(selection=[
        ('bom', 'BOM'),
        ('procurement', 'PRC'),
        ('production', 'PRD'),
        ('quality', 'QCT'),
        ('packing', 'PAC'),
    ], string="Status", compute="_compute_status", store=True)

    display_name = fields.Char(compute='_compute_display_name', string="Display Name", store=True)

    @api.depends(
        'x_manufacturing_id',
        'x_manufacturing_id.x_planned_finish_date',
        'x_manufacturing_id.date_planned_finished',
    )
    def _compute_expected_date(self):
        for rec in self:
            if rec.x_manufacturing_id.state in ('draft', 'confirmed'):
                rec.x_expected_date = rec.x_manufacturing_id.x_planned_finish_date
            elif rec.x_manufacturing_id.state in ('planned', 'progress', 'to_close', 'done'):
                rec.x_expected_date = rec.x_manufacturing_id.date_planned_finished
            else:
                rec.x_expected_date = False

    @api.depends(
        'x_picking_id.x_mrp_demand_ids', 'x_picking_id.x_mrp_demand_ids.x_manufacturing_id',
    )
    def _compute_manufacturing(self):
        for rec in self:
            mrp_demand_ids = rec.x_picking_id.x_mrp_demand_ids.filtered(
                lambda x: x.x_child_product_id == rec.x_product_id and x.x_manufacturing_id.state != 'cancel'
            )
            if mrp_demand_ids:
                rec.x_mrp_demand_id = mrp_demand_ids[0].id
                rec.x_manufacturing_id = mrp_demand_ids.mapped('x_manufacturing_id')[0].id
            else:
                rec.x_mrp_demand_id = False
                rec.x_manufacturing_id = False

    @api.depends(
        'x_move_id.product_uom_qty',
        'x_move_id.reserved_availability',
        'x_mrp_demand_id',
        'x_mrp_demand_id.x_reserved',
        'x_mrp_demand_id.x_demand',
        'x_manufacturing_id',
        'x_manufacturing_id.state',
        'x_manufacturing_id.x_bom_tool_status',
        'x_manufacturing_id.x_production_status',
        'x_manufacturing_id.workorder_ids',
        'x_manufacturing_id.workorder_ids.state',
        'x_manufacturing_id.workorder_ids.workcenter_id',
    )
    def _compute_status(self):
        for rec in self:
            # Go to cus_mrp_children for the code
            rec.x_status = False

    @api.depends('x_product_id', 'x_quantity', 'x_completion', 'x_status')
    def _compute_display_name(self):
        for rec in self:
            status = dict(self._fields['x_status'].selection).get(rec.x_status) if rec.x_status else False
            rec.display_name = f"{rec.x_product_id.name} - QTY:{rec.x_quantity} - {rec.x_completion * 100}% - {status}"
