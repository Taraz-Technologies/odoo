from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_mrp_demand_ids = fields.One2many(
        comodel_name='mrp.source.details',
        inverse_name='x_picking_id',
        string='Source Details',
        domain=[('x_manufacturing_id.state', '!=', 'cancel')],
        required=False,
    )
    x_expected_date = fields.Datetime(
        compute='_compute_expected_date',
        store=True,
        tracking=True,
        copy=False,
    )
    x_manufacturing_type = fields.Selection(
        selection=[
            ('proc', 'Procurement'),
            ('mrp', 'Manufacturing'),
        ],
        string='Order Type',
        required=True,
        default='proc',
        tracking=True,
    )
    x_manufacturing_id = fields.Many2one(
        comodel_name='mrp.production',
        string="Manufacturing Order",
        compute="_compute_manufacturing_data",
        store=True,
    )
    x_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        compute="_compute_manufacturing_data",
        store=True,
    )
    x_bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string="Bill of Material",
        compute="_compute_manufacturing_data",
        store=True,
    )

    x_sale_order_ids = fields.One2many(related="x_manufacturing_id.x_mrp_demand_ids")

    x_production_status = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], compute="_compute_manufacturing_status", string="MO Status", store=True)

    x_mo_deadline = fields.Datetime(compute="_compute_manufacturing_deadline", string="MO Deadline", store=True)

    x_product_delivery_status_ids = fields.One2many(
        comodel_name='product.delivery.status',
        inverse_name='x_picking_id',
        string='Product Delivery Status',
        compute='_compute_product_delivery_status_ids',
        store=True,
    )

    x_compute_delivery_order_state = fields.Boolean(compute='_compute_delivery_order_state')
    x_image_128 = fields.Image(related='product_id.image_128', string='Image')

    @api.depends('move_lines', 'move_lines.product_id', 'move_lines.product_uom_qty')
    def _compute_product_delivery_status_ids(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                rec.x_product_delivery_status_ids = [(2, line.id) for line in rec.x_product_delivery_status_ids]
                product_delivery_status_ids = [(0, 0, {
                    'x_picking_id': rec.id,
                    'x_move_id': line.id,
                    'x_product_id': line.product_id.id,
                    'x_quantity': line.product_uom_qty,
                    'x_completion': 0,
                    'x_status': False,
                }) for line in rec.move_lines if line.product_id]
                rec.x_product_delivery_status_ids = product_delivery_status_ids

    @api.depends('x_product_delivery_status_ids', 'x_product_delivery_status_ids.x_status')
    def _compute_delivery_order_state(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                product_delivery_status = rec.x_product_delivery_status_ids.mapped('x_status')
                if rec.state == 'done':
                    rec.x_delivery_order_state = 'shipped'
                elif any(status == 'production' for status in product_delivery_status):
                    rec.x_delivery_order_state = 'production'
                elif any(not status for status in product_delivery_status):
                    rec.x_delivery_order_state = 'new'
                elif any(status == 'procurement' for status in product_delivery_status):
                    rec.x_delivery_order_state = 'procurement'
                elif any(status == 'quality' for status in product_delivery_status):
                    rec.x_delivery_order_state = 'quality'
                elif any(status == 'packing' for status in product_delivery_status):
                    rec.x_delivery_order_state = 'packing'
                else:
                    rec.x_delivery_order_state = 'new'

                if any(status != 'packing' for status in
                       product_delivery_status) and rec.x_delivery_order_state == 'packing':
                    rec.color = 9
                elif any(status != 'quality' for status in
                         product_delivery_status) and rec.x_delivery_order_state == 'quality':
                    rec.color = 9
                elif any(status != 'production' for status in
                         product_delivery_status) and rec.x_delivery_order_state == 'production':
                    rec.color = 9
                elif any(status != 'procurement' for status in
                         product_delivery_status) and rec.x_delivery_order_state == 'procurement':
                    rec.color = 9
                else:
                    rec.color = 0
            rec.x_compute_delivery_order_state = False

    @api.depends('origin')
    def _compute_manufacturing_data(self):
        for rec in self:
            manufacturing_id = False
            if rec.picking_type_code == 'internal' and rec.origin:
                manufacturing_id = self.env['mrp.production'].search([('name', '=', rec.origin)], limit=1).id
            rec.x_manufacturing_id = manufacturing_id
            rec.x_product_id = rec.x_manufacturing_id.product_id.id or False
            rec.x_bom_id = rec.x_manufacturing_id.bom_id.id or False

    @api.depends('x_manufacturing_id', 'x_manufacturing_id.state')
    def _compute_manufacturing_status(self):
        for rec in self:
            rec.x_production_status = rec.x_manufacturing_id.state

    @api.depends('x_manufacturing_id', 'x_manufacturing_id.date_deadline')
    def _compute_manufacturing_deadline(self):
        for rec in self:
            rec.x_mo_deadline = rec.x_manufacturing_id.date_deadline

    def action_view_manufacturing_order(self):
        self.ensure_one()
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
        action['res_id'] = self.x_manufacturing_id.id
        return action

    def action_view_picking_lines(self):
        self.ensure_one()
        self.env['stock.move'].search([
            ('product_uom_qty', '>', 0),
            '|', ('picking_id.name', 'ilike', 'WH/PC/'), ('picking_id.name', 'ilike', 'WTR/PC/'),
            ('state', 'in', ('confirmed', 'partially_available')),
        ]).get_prc_details()
        action = self.env.ref('cus_production_planner.short_parts_manufacturing_stock_move_action').read()[0]
        action['context'] = {
            'search_default_raw_material': 1,
            'search_default_origin': self.name,
        }
        return action

    @api.depends(
        'x_tracking_id',
        'x_tracking_id.x_sub_route_id',
        'x_tracking_id.x_consolidation_id.x_sub_route_id',
        'x_product_delivery_status_ids',
        'x_product_delivery_status_ids.x_expected_date',
    )
    def _compute_expected_date(self):
        for rec in self:
            expected_date = False
            if rec.picking_type_code == 'outgoing':
                expected_dates = rec.x_product_delivery_status_ids.filtered(
                    lambda p: p.x_expected_date
                ).mapped('x_expected_date')
                if len(expected_dates) > 1:
                    expected_date = max(expected_dates)
                elif len(expected_dates) == 1:
                    expected_date = expected_dates[0]
                else:
                    expected_date = False
            elif rec.picking_type_code == 'incoming':
                if not rec.x_tracking_id and rec.create_date:
                    expected_date = rec.create_date + timedelta(days=30)
                elif rec.x_tracking_id.x_is_forwarder and rec.x_tracking_id.x_consolidation_id.x_sub_route_id:
                    from_date = rec.x_tracking_id.x_consolidation_id.x_tracking_id.create_date or rec.create_date
                    sub_route_ids = rec.x_tracking_id.x_consolidation_id.x_route_id.x_sub_route_ids
                    sub_route_id_index = sub_route_ids.ids.index(rec.x_tracking_id.x_consolidation_id.x_sub_route_id.id)
                    sub_route_ids_list = sub_route_ids.ids[sub_route_id_index:len(sub_route_ids.ids)]
                    sub_route_ids = self.env['logistics.sub.route'].browse(sub_route_ids_list)
                    expected_date = from_date + timedelta(
                        days=sum(sub_route_ids.mapped('x_delivery_days'))
                    )
                elif rec.x_tracking_id.x_sub_route_id:
                    from_date = rec.x_tracking_id.create_date or rec.create_date
                    sub_route_ids = rec.x_tracking_id.x_route_id.x_sub_route_ids
                    sub_route_id_index = sub_route_ids.ids.index(rec.x_tracking_id.x_sub_route_id.id)
                    sub_route_ids_list = sub_route_ids.ids[sub_route_id_index:len(sub_route_ids.ids)]
                    sub_route_ids = self.env['logistics.sub.route'].browse(sub_route_ids_list)
                    expected_date = from_date + timedelta(
                        days=sum(sub_route_ids.mapped('x_delivery_days'))
                    )
            rec.x_expected_date = expected_date

    def update_move_raw_ids(self):
        for rec in self:
            if rec.picking_type_code == 'internal' and rec.origin:
                production_id = self.env['mrp.production'].search([('name', '=', rec.origin)])
                production_id.update_move_raw_ids()
