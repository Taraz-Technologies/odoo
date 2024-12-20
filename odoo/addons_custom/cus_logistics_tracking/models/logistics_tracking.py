from odoo import _, api, fields, models

import pytz
import datetime
import http.client
import json


class LogisticsTracking(models.Model):
    _name = "logistics.tracking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Logistics Tracking"
    _rec_name = 'display_name'

    x_state = fields.Selection(selection=[
        ('pending', 'Pending'), ('in_transit', 'In Transit'), ('done', 'Done'),
    ], string='Status', default="pending", required=False, tracking=True)
    x_type = fields.Selection(selection=[
        ('incoming', 'Receipts'), ('outgoing', 'Delivery'),
    ], string='Type', compute="_compute_type", store=True, tracking=True)

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)

    x_route_id = fields.Many2one(comodel_name='logistics.route', string='Route', required=True, tracking=True)
    x_sub_route_ids = fields.Many2many(related="x_route_id.x_sub_route_ids")
    x_sub_route_id = fields.Many2one(comodel_name='logistics.sub.route', string='Sub-Route',
                                     domain="[('id', 'in', x_sub_route_ids)]", required=True, tracking=True)
    x_shipping_type = fields.Selection(selection=[
        ('air', 'Air'),
        ('land', 'Land'),
        ('sea', 'Sea'),
    ], string='Shipping Type', required=True, )

    x_carrier_id = fields.Many2one(comodel_name='delivery.carrier', string='Carrier', required=True, tracking=True)
    x_shipment_type = fields.Selection(selection=[
        ('clear', 'Clearing'),
        ('forward', 'Forwarding'),
        ('self', 'Shipping (Self Pickup)'),
        ('export', 'Shipping (Export)'),
    ], string='Shipping Type', required=True, )
    x_average_delivery_days = fields.Integer(related='x_carrier_id.x_average_delivery_days')
    x_tracking_ref = fields.Char(string='Tracking Ref/BOL', required=True, tracking=True)

    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=2)

    x_length = fields.Float(string='Length (cm)', required=False, tracking=True)
    x_width = fields.Float(string='Width (cm)', required=False, tracking=True)
    x_height = fields.Float(string='Height (cm)', required=False, tracking=True)
    x_weight = fields.Float(string='Weight', required=False, tracking=True)
    x_volume = fields.Float(string='Volume', compute="_compute_volume", store=True)
    x_freight = fields.Float(string="Freight", required=False, tracking=True)
    x_estimated_freight = fields.Float(string="Estimated Freight", required=False, tracking=True)

    x_shipping_date = fields.Date(string='Shipping Date', required=False)
    x_delivery_date = fields.Date(string='Delivery Date', required=False)
    x_delivery_days = fields.Integer(string='Delivery Days', compute="_get_delivery_days", store=True)

    x_paid_by = fields.Selection(selection=[
        ('sender', 'Sender'), ('receiver', 'Receiver'),
    ], string='Paid by', required=False, tracking=True)

    x_company_from = fields.Many2one(comodel_name='res.partner', string='From', required=True, tracking=True,
                                     compute="_compute_from_to", store=True, readonly=False)
    x_company_to = fields.Many2one(comodel_name='res.partner', string='To', required=True, tracking=True,
                                   compute="_compute_from_to", store=True, readonly=False)
    x_country_from = fields.Many2one(related="x_company_from.country_id")
    x_country_to = fields.Many2one(related="x_company_to.country_id")

    x_is_forwarder = fields.Boolean(related="x_company_from.x_is_forwarder", store=True, tracking=True)
    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Related Consolidation')
    x_forwarder_ref = fields.Char(related="x_consolidation_id.x_forwarder_ref")

    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Rel. Receipt/Delivery', tracking=True,
                                   domain="[('picking_type_id.code', 'in', ['incoming', 'outgoing'])]")
    x_picking_type_id = fields.Many2one(related="x_picking_id.picking_type_id")
    x_purchase_order_id = fields.Many2one(related="x_picking_id.purchase_id")

    x_sale_order_id = fields.Many2one(related="x_picking_id.sale_id")
    x_total_freight = fields.Float(string="Estimated Freight", related="x_sale_order_id.x_total_freight")
    x_total_weight = fields.Float(string="Estimated Weight", related="x_sale_order_id.x_total_weight")
    x_freight_per_kg = fields.Float(string="Freight / kg", related="x_sale_order_id.x_freight_per_kg")

    x_notes = fields.Text(string="Notes", required=False)

    x_detained = fields.Boolean(string="Detained")
    x_clearing_agent = fields.Many2one('res.partner', string="Clearing Agent")

    x_actual_value = fields.Float(string='Actual Value', compute="_compute_values")
    x_declared_value = fields.Float(string='Declared Value', compute="_compute_values")

    @api.depends(
        'x_picking_id',
        'x_picking_id.move_lines.purchase_line_id.order_id.amount_total',
        'x_picking_id.move_lines.sale_line_id.order_id.amount_total',
        'x_picking_id.x_total_amount',
        'x_consolidation_id',
        'x_consolidation_id.x_product_ids.x_subtotal',
        'x_consolidation_id.x_product_ids.x_uv_subtotal',
    )
    def _compute_values(self):
        for rec in self:
            if not rec.x_company_from.x_is_forwarder and rec.x_picking_id:
                if rec.x_picking_id.move_lines.purchase_line_id.order_id:
                    rec.x_actual_value = rec.x_picking_id.move_lines.purchase_line_id.order_id.amount_total
                    rec.x_declared_value = rec.x_picking_id.move_lines.purchase_line_id.order_id.amount_total
                elif rec.x_picking_id.move_ids_without_package.sale_line_id.order_id:
                    rec.x_actual_value = rec.x_picking_id.move_lines.sale_line_id.order_id.amount_total
                    rec.x_declared_value = rec.x_picking_id.x_total_amount
                else:
                    rec.x_actual_value = 0
                    rec.x_declared_value = 0
            elif rec.x_company_from.x_is_forwarder and rec.x_consolidation_id:
                rec.x_actual_value = sum(rec.x_consolidation_id.x_product_ids.mapped('x_subtotal'))
                rec.x_declared_value = sum(rec.x_consolidation_id.x_product_ids.mapped('x_uv_subtotal'))
            else:
                rec.x_actual_value = 0
                rec.x_declared_value = 0


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = ['|', '|', ('display_name', operator, name), ('x_picking_id.name', operator, name),
                      ('x_consolidation_id.x_name', operator, name)]
            tracking_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            tracking_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(tracking_ids).with_user(name_get_uid))

    @api.model
    def get_tracking_dates_from_url(self):
        tracking_ids = self.filtered(lambda l: l.x_tracking_ref and l.x_state in ['pending', 'in_transit'])
        for tracking in tracking_ids:
            if tracking.x_carrier_id.id == 2:
                conn = http.client.HTTPSConnection("api-eu.dhl.com")
                headers = {'DHL-API-Key': "0UfccdTN4MhlGbzBDiRfQibJAzpqzwyU"}
                conn.request("GET", "/track/shipments?trackingNumber=" + tracking.x_tracking_ref, headers=headers)

                res = conn.getresponse()
                data = res.read()
                data_dic = data.decode("utf-8")
                if 'shipments' in data_dic and 'events' in data_dic and 'description' in data_dic:
                    data_dic = json.loads(data_dic)
                    for events in data_dic['shipments'][0]['events']:
                        if events['description'] == 'Shipment picked up':
                            tracking.x_shipping_date = events['timestamp'][0:10]
                        if events['description'] == 'Delivered':
                            tracking.x_delivery_date = events['timestamp'][0:10]

    def open_url(self):
        for rec in self:
            if rec.x_carrier_id.x_tracking_url and rec.x_tracking_ref:
                return {
                    'type': 'ir.actions.act_url',
                    'url': rec.x_carrier_id.x_tracking_url.replace('{Tracking Ref}', rec.x_tracking_ref),
                    'target': 'new',
                }

    @api.depends('x_picking_id')
    def _compute_type(self):
        for rec in self:
            if rec.x_picking_id:
                rec.x_type = rec.x_picking_id.picking_type_id.code

    @api.depends('x_sub_route_id')
    def _compute_from_to(self):
        for rec in self:
            if rec.x_sub_route_id.x_from:
                rec.x_company_from = rec.x_sub_route_id.x_from
            if rec.x_sub_route_id.x_to:
                rec.x_company_to = rec.x_sub_route_id.x_to

    @api.depends('x_carrier_id', 'x_tracking_ref')
    def _compute_display_name(self):
        for rec in self:
            if rec.x_carrier_id and rec.x_tracking_ref:
                rec.display_name = '%s: %s' % (rec.x_carrier_id.name, rec.x_tracking_ref)
            elif rec.x_carrier_id:
                rec.display_name = rec.x_carrier_id.name
            elif rec.x_tracking_ref:
                rec.display_name = rec.x_tracking_ref

            rec.x_shipping_date = datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date()
            if rec.x_picking_id:
                rec.x_picking_id.carrier_id = rec.x_carrier_id.id
                rec.x_picking_id.carrier_tracking_ref = rec.x_tracking_ref
                
    @api.depends('x_shipping_date', 'x_delivery_date')
    def _get_delivery_days(self):
        for rec in self:
            if rec.x_delivery_date and rec.x_shipping_date:
                rec.x_delivery_days = (rec.x_delivery_date - rec.x_shipping_date).days + 1
            if rec.x_delivery_date:
                rec.x_state = 'done'
            elif rec.x_shipping_date:
                rec.x_state = 'in_transit'
            else:
                rec.x_state = 'pending'

            if rec.x_picking_id.state not in ('done', 'cancel') and rec.x_average_delivery_days != 0:
                rec.x_picking_id.scheduled_date = rec.x_shipping_date + datetime.timedelta(days=rec.x_average_delivery_days)

    @api.depends('x_length', 'x_width', 'x_height')
    def _compute_volume(self):
        for rec in self:
            rec.x_volume = rec.x_length * rec.x_width * rec.x_height

    # @api.depends('x_state', 'x_type', 'x_picking_id', 'x_purchase_order_id.x_forwarder_ref')
    # def update_po_ro_task_status(self):
    #     for rec in self:
    #         if rec.x_type == 'incoming' and rec.x_purchase_order_id:
    #             if rec.x_purchase_order_id.x_task_id:
    #                 if rec.x_state == 'pending':
    #                     rec.x_purchase_order_id.x_task_id.stage_id = 30
    #                 elif rec.x_state == 'in_transit':
    #                     rec.x_purchase_order_id.x_task_id.stage_id = 60
    #                 elif rec.x_state == 'done':
    #                     if rec.x_purchase_order_id.x_forwarder_ref:
    #                         rec.x_purchase_order_id.x_task_id.stage_id = 61
    #                     else:
    #                         rec.x_purchase_order_id.x_task_id.stage_id = 64
    #             if rec.x_picking_id:
    #                 if rec.x_picking_id.x_task_id:
    #                     if rec.x_state == 'pending':
    #                         rec.x_picking_id.x_task_id.stage_id = 30
    #                     elif rec.x_state == 'in_transit':
    #                         rec.x_picking_id.x_task_id.stage_id = 60
    #                     elif rec.x_state == 'done':
    #                         if rec.x_purchase_order_id.x_forwarder_ref:
    #                             rec.x_picking_id.x_task_id.stage_id = 61
    #                         else:
    #                             rec.x_picking_id.x_task_id.stage_id = 64
    #         rec.update_task_status = True
