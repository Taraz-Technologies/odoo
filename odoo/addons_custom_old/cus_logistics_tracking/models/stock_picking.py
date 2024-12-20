from odoo import api, fields, models, _
from odoo.exceptions import UserError

import datetime
import pytz
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    color = fields.Integer(string='Color Index', compute="_compute_color", store=True)

    x_backorder = fields.Selection(selection=[('backorder', 'Backorder')], string='Backorder Tag',
                                   compute="_compute_backorder_tag", store=True, tracking=True)

    x_tracking_id = fields.Many2one(comodel_name='logistics.tracking', string='Tracking Ref/BOL', tracking=True)

    x_consolidation_ids = fields.Many2many(comodel_name='consolidation.tracking', string='Consolidations')
    x_consolidation_count = fields.Integer(string='Consolidation Count',
                                           compute="_compute_consolidations_count", store=True)
    x_forwarder_tracking_id = fields.Many2one(comodel_name='logistics.tracking', string='Forwarder Tracking')

    x_route_id = fields.Many2one(comodel_name='logistics.route', string='Route',
                                 compute="_compute_logistics_info", tracking=True, store=True)
    x_sub_route_id = fields.Many2one(comodel_name='logistics.sub.route', string='Sub-Route',
                                     compute="_compute_logistics_info", tracking=True, store=True)
    x_tracking_state = fields.Selection(selection=[
        ('pending', 'Pending'), ('in_transit', 'In Transit'), ('done', 'Done'),
    ], string='Tracking Status', compute="_compute_logistics_info", tracking=True, store=True)

    x_auto_fill_done_quantity = fields.Boolean(string='Auto-fill Done Qty', required=False)

    x_related_incoming_id = fields.Many2one(
        comodel_name='stock.picking', string='Related Incoming',
        domain="[('group_id', '=', group_id), ('picking_type_code', '=', 'internal')]"
    )
    x_related_warehousing_id = fields.Many2one(
        comodel_name='stock.picking', string='Related Warehousing',
        domain="[('state', '!=', 'done'), ('group_id', '=', group_id), ('picking_type_code', '=', 'internal')]"
    )
    x_landed_cost_ids = fields.Many2many(comodel_name='stock.landed.cost', string='Related Landed Costs',
                                         compute="_compute_related_landed_cost", store=True)
    x_landed_cost_count = fields.Integer(string='Landed Cost Count',
                                         compute="_compute_landed_cost_count", store=True)

    x_tracking_status = fields.Selection(selection=[
        ('backorder', 'Backorder'),
        ('new', 'New'),
        ('in_transit', 'In Transit'),
        ('arrived', 'Arrived'),
        # ('start_warehousing', 'Start Warehousing'),
        ('in_stock', 'In Stock'),
        ('cancelled', 'Cancelled'),
    ], string='Tracking', default='new', group_expand='_expand_states', tracking=True, store=True)

    x_mark_tracking_as_in_stock = fields.Boolean(string='Mark tracking as In Stock',
                                                 compute="mark_tracking_as_in_stock", store=True)

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags', store=True, tracking=True)

    x_delivery_order_state = fields.Selection(selection=[
        ('new', 'New'),
        ('procurement', 'Procurement'),
        ('production', 'Production'),
        ('quality', 'Quality Control'),
        ('packing', 'Packing'),
        ('shipped', 'Shipped'),
    ], string='Delivery Order Status', default='new', group_expand='_expand_delivery_order_state', tracking=True)

    x_sale_id = fields.Many2one(related="move_ids_without_package.sale_line_id.order_id")
    x_folder_name = fields.Char(related="x_sale_id.x_folder_name")

    x_remaining_days = fields.Integer(string='Remaining Days', compute="_compute_remaining_days", store=True)
    x_bill_ids = fields.Many2many(
        comodel_name='account.move', string='Related Bills', relation="account_move_stock_picking_rel_1",
        column1="stock_picking_id", column2="account_move_id", domain="[('type', '=', 'in_invoice')]"
    )
    x_bill_count = fields.Integer(compute='_compute_bill_count', store=True)

    x_operation_type = fields.Selection(selection=[
        ('free', 'FZ Operation'), ('otb', 'OTB Operation'),
    ], string='Operation (FZ/OTB)', help="Free Zone or OTB Operation")

    x_attachment_name = fields.Char(
        string='Download File Name')
    x_attachment = fields.Binary(
        string='Download File',
        copy=False,
        tracking=True, )
    x_form_field_01 = fields.Char(
        string='Form No.',
        copy=False,
        tracking=True)
    x_form_field_02 = fields.Selection(
        string='İŞLEM YÖNÜ',
        selection=[
            ("from_turkey", "Bölgeye Türkiye'den Mal-Hizmet Girişi"),
            ("from_abroad", "Bölgeye Yurt Dışından Mal-Hizmet Girişi"), ],
        copy=False,
        tracking=True)
    x_form_field_03 = fields.Selection(
        string='İŞLEM KONUSU',
        selection=[
            ("Ticari-Mal", "Ticari-Mal"),
            ("Ticari Olmayan-Demirbaş", "Ticari Olmayan-Demirbaş"),
            ("Ticari Olmayan-Sarf Malzemesi", "Ticari Olmayan-Sarf Malzemesi"),
            ("Ticari Olmayan-Yatırım ve Tesis", "Ticari Olmayan-Yatırım ve Tesis"),
            ("Ticari Olmayan-Hizmet Alımı", "Ticari Olmayan-Hizmet Alımı"), ],
        copy=False,
        tracking=True)
    x_form_field_04 = fields.Selection(
        string='İŞLEM TÜRÜ',
        selection=[
            ("Kesin Alış/Satış", "Kesin Alış/Satış"),
            ("Diğer İşlem Türleri-5000$ Altı", "Diğer İşlem Türleri-5000$ Altı"), ],
        copy=False,
        tracking=True)
    x_form_field_05 = fields.Char(
        string='SEVKİYAT ŞEKLİ',
        copy=False,
        tracking=True)
    x_form_field_06 = fields.Char(
        string='TAŞIT CİNSİ',
        copy=False,
        tracking=True)
    x_form_field_07 = fields.Float(
        string='Mal Bedeli Toplamları',
        copy=False,
        tracking=True)
    x_form_field_08 = fields.Float(
        string='CIF Toplamı',
        copy=False,
        tracking=True)
    x_form_field_09 = fields.Datetime(
        string='GİRİŞ / ÇIKIŞ Tarih',
        copy=False,
        tracking=True)
    x_form_field_10 = fields.Float(
        string='Brüt Ağırlık Toplamı',
        copy=False,
        tracking=True)
    x_form_field_11 = fields.Date(
        string='Formu Tarih',
        copy=False,
        tracking=True)
    x_form_field_12 = fields.Float(
        string='KAP',
        copy=False,
        tracking=True)
    x_form_field_13 = fields.Many2one(
        comodel_name='res.currency',
        string='Mal Bedeli Toplamları Currency',
        copy=False,
        tracking=True)
    x_form_field_14 = fields.Many2one(
        comodel_name='res.currency',
        string='CIF Toplamı Currency',
        copy=False,
        tracking=True)
    x_push_data = fields.Boolean(compute='push_form_data_to_account_moves', store=True)

    def write(self, vals):
        old_values = self.x_tag_ids.ids
        res = super(StockPicking, self).write(vals)
        new_values = self.x_tag_ids.ids
        if 'x_tag_ids' in vals:
            self.x_tag_ids._track_many2many_changes(
                self, 'x_tag_ids', old_values=old_values, new_values=new_values
            )
        return res

    @api.onchange('x_form_field_09')
    def check_in_out_date(self):
        for rec in self:
            if rec.x_form_field_09:
                if rec.x_form_field_09 > datetime.datetime.now():
                    raise UserError("You cannot enter future date in 'In/Out Date' field!")


    def change_picking_effective_date_to_in_out_date(self):
        for rec in self:
            if rec.picking_type_code not in ('incoming', 'outgoing'):
                return
            rec.date_done = rec.x_form_field_09

            # Update Stock Move and Stock Move Lines
            rec.move_lines.update({'date': rec.x_form_field_09})
            rec.move_line_ids.update({'date': rec.x_form_field_09})

            if rec.picking_type_code == 'incoming':
                for move in rec.move_lines:
                    if move.purchase_line_id and move.product_id.id == move.purchase_line_id.product_id.id:
                        line = move.purchase_line_id
                        order = line.order_id
                        price_unit = line.price_unit
                        if line.taxes_id:
                            price_unit = line.taxes_id.with_context(round=False).compute_all(
                                price_unit, currency=line.order_id.currency_id, quantity=1.0
                            )['total_void']
                        if line.product_uom.id != line.product_id.uom_id.id:
                            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
                        if order.currency_id != order.company_id.currency_id:
                            price_unit = order.currency_id._convert(
                                price_unit,
                                order.company_id.currency_id,
                                order.company_id,
                                move.date.date(),
                                round=False
                            )
                        move.price_unit = price_unit

            # Update Stock Valuation Layer (SVL) of LC
            svl_ids = rec.move_lines.mapped('stock_valuation_layer_ids').filtered(
                lambda m: m.stock_landed_cost_id
            ).sorted(lambda m: m.id)
            for svl_id in svl_ids:
                self.env.cr.execute(
                    "UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (rec.x_form_field_09, svl_id.id)
                )
            # val_ids = svl_ids.mapped('stock_landed_cost_id').mapped('valuation_adjustment_lines').filtered(
            #     lambda v: v.product_id.id in svl_ids.mapped('product_id').ids
            # ).sorted(lambda v: v.id).mapped('additional_landed_cost')
            # for idx, svl_id in enumerate(svl_ids):
            #     svl_id.update({
            #         'value': val_ids[idx],
            #         'unit_cost': 0,
            #     })

            # Update Stock Valuation Layer (SVL)
            svl_ids = rec.move_lines.mapped('stock_valuation_layer_ids').filtered(
                lambda m: not m.stock_landed_cost_id
            )
            for svl_id in svl_ids:
                self.env.cr.execute(
                    "UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (rec.x_form_field_09, svl_id.id)
                )
                if rec.picking_type_code == 'incoming':
                    vals = {
                        'value': svl_id.stock_move_id.price_unit * svl_id.quantity,
                        'unit_cost': svl_id.stock_move_id.price_unit,
                    }
                    if svl_id.product_id.cost_method in ('average', 'fifo'):
                        vals['remaining_value'] = svl_id.stock_move_id.price_unit * svl_id.remaining_qty
                        val_ids = svl_id.stock_move_id.stock_valuation_layer_ids.filtered(
                            lambda s: s.stock_landed_cost_id
                        )
                        lc_adjustment_value = sum(val_ids.mapped('value'))
                        for val_id in val_ids:
                            val_id.value *= svl_id.remaining_qty / svl_id.quantity
                        vals['remaining_value'] = (
                                (vals.get('value') + lc_adjustment_value) * svl_id.remaining_qty / svl_id.quantity
                        ) if svl_id.quantity != 0 else 0
                    svl_id.update(vals)

            # Update Account Move
            account_move_ids = rec.move_lines.mapped('account_move_ids')
            if account_move_ids:
                currency_ids = account_move_ids.mapped('line_ids').mapped('currency_id')
                account_move_ids.update({
                    'invoice_date': rec.x_form_field_09.date(),
                    'date': rec.x_form_field_09.date(),
                    'currency_id': currency_ids[0].id if currency_ids else self.env.ref('base.USD').id,
                })
                for account_move_id in account_move_ids:
                    account_move_id._onchange_invoice_date()
                if rec.picking_type_code == 'incoming':
                    line_ids = account_move_ids.mapped('line_ids')
                    for line in line_ids:
                        company_currency = line.account_id.company_id.currency_id
                        balance = line.amount_currency
                        if line.currency_id and company_currency and line.currency_id != company_currency:
                            balance = line.currency_id._convert(
                                balance, company_currency, line.account_id.company_id, line.move_id.date
                            )
                            self.env.cr.execute(
                                "UPDATE account_move_line set debit = '%s', credit = '%s', balance = %s WHERE id=%s" % (
                                    balance > 0 and balance or 0.0,
                                    balance < 0 and -balance or 0.0,
                                    balance or 0.0,
                                    line.id,
                                )
                            )


    @api.depends('x_attachment_name', 'x_attachment', 'x_form_field_01', 'x_form_field_02', 'x_form_field_03',
                 'x_form_field_04', 'x_form_field_05', 'x_form_field_06', 'x_form_field_07', 'x_form_field_08',
                 'x_form_field_09', 'x_form_field_10', 'x_form_field_11', 'x_form_field_12', 'x_form_field_13',
                 'x_form_field_14')
    def push_form_data_to_account_moves(self):
        for rec in self:
            if rec.picking_type_code != 'incoming' or rec.company_id.id != 2:
                continue
            # Change Receipt Entry Date to Form Date
            if rec.x_form_field_09:
                rec.move_ids_without_package.mapped('account_move_ids').update({'date': rec.x_form_field_09})
            # Receipt Entry
            rec.move_ids_without_package.mapped('account_move_ids').update({
                'date': rec.x_form_field_09,
                'x_move_type': 'receipt_entry',
                'x_related_purchase_id': rec.purchase_id.id,
                'x_attachment_name': rec.x_attachment_name,
                'x_attachment': rec.x_attachment,
                'x_form_field_01': rec.x_form_field_01,
                'x_form_field_02': rec.x_form_field_02,
                'x_form_field_03': rec.x_form_field_03,
                'x_form_field_04': rec.x_form_field_04,
                'x_form_field_05': rec.x_form_field_05,
                'x_form_field_06': rec.x_form_field_06,
                'x_form_field_07': rec.x_form_field_07,
                'x_form_field_08': rec.x_form_field_08,
                'x_form_field_09': rec.x_form_field_09,
                'x_form_field_10': rec.x_form_field_10,
                'x_form_field_11': rec.x_form_field_11,
                'x_form_field_12': rec.x_form_field_12,
                'x_form_field_13': rec.x_form_field_13.id,
                'x_form_field_14': rec.x_form_field_14.id,
            })
            # Receipt Invoice
            invoice_id = self.env['account.move'].search([('picking_id', '=', rec.id)])
            if invoice_id:
                invoice_id.x_attachment_name = rec.x_attachment_name
                invoice_id.x_attachment = rec.x_attachment
                invoice_id.x_form_field_01 = rec.x_form_field_01
                invoice_id.x_form_field_02 = rec.x_form_field_02
                invoice_id.x_form_field_03 = rec.x_form_field_03
                invoice_id.x_form_field_04 = rec.x_form_field_04
                invoice_id.x_form_field_05 = rec.x_form_field_05
                invoice_id.x_form_field_06 = rec.x_form_field_06
                invoice_id.x_form_field_07 = rec.x_form_field_07
                invoice_id.x_form_field_08 = rec.x_form_field_08
                invoice_id.x_form_field_09 = rec.x_form_field_09
                invoice_id.x_form_field_10 = rec.x_form_field_10
                invoice_id.x_form_field_11 = rec.x_form_field_11
                invoice_id.x_form_field_12 = rec.x_form_field_12
                invoice_id.x_form_field_13 = rec.x_form_field_13.id
                invoice_id.x_form_field_14 = rec.x_form_field_14.id
            # Related Invoices
            related_invoice_ids = self.env['account.move'].search([('x_picking_ids', 'ilike', rec.id)])
            if related_invoice_ids:
                related_invoice_ids.update({
                    'x_attachment_name': rec.x_attachment_name,
                    'x_attachment': rec.x_attachment,
                    'x_form_field_01': rec.x_form_field_01,
                    'x_form_field_02': rec.x_form_field_02,
                    'x_form_field_03': rec.x_form_field_03,
                    'x_form_field_04': rec.x_form_field_04,
                    'x_form_field_05': rec.x_form_field_05,
                    'x_form_field_06': rec.x_form_field_06,
                    'x_form_field_07': rec.x_form_field_07,
                    'x_form_field_08': rec.x_form_field_08,
                    'x_form_field_09': rec.x_form_field_09,
                    'x_form_field_10': rec.x_form_field_10,
                    'x_form_field_11': rec.x_form_field_11,
                    'x_form_field_12': rec.x_form_field_12,
                    'x_form_field_13': rec.x_form_field_13.id,
                    'x_form_field_14': rec.x_form_field_14.id,
                })


    @api.depends('x_bill_ids.x_picking_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.x_bill_ids = [(6, 0, self.env['account.move'].search([('x_picking_ids', 'ilike', rec.id)]).ids)]
            rec.x_bill_count = len(rec.x_bill_ids)


    @api.depends('scheduled_date')
    def _compute_remaining_days(self):
        current_data = datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz))
        for rec in self:
            rec.x_remaining_days = (rec.scheduled_date.date() - current_data.date()).days


    @api.model
    def get_remaining_days(self):
        current_data = datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz))
        picking_ids = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'), ('state', 'not in', ('cancel', 'done'))
        ])
        for picking_id in picking_ids:
            picking_id.x_remaining_days = (picking_id.scheduled_date.date() - current_data.date()).days


    @api.model
    def _expand_delivery_order_state(self, states, domain, order):
        return [key for key, val in type(self).x_delivery_order_state.selection]


    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).x_tracking_status.selection]


    def action_create_landed_cost_bill(self):
        for rec in self:
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': [rec.id],
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                # 'default_partner_id': rec.partner_id.id if rec.picking_type_code == 'incoming' else False,
                # 'default_partner_shipping_id': rec.partner_id.id if rec.picking_type_code == 'incoming' else False,
                'default_invoice_date': datetime.datetime.now(
                    pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'default_x_purchase_type': 'Forwarding' if rec.picking_type_code == 'incoming' else False,
                'default_x_item_type': 'Landed Cost' if rec.picking_type_code == 'incoming' else False,
                'default_x_related_po_s': [rec.purchase_id.id] if rec.picking_type_code == 'incoming' else [],

                'default_x_attachment_name': rec.x_attachment_name if rec.company_id.id == 2 else False,
                'default_x_attachment': rec.x_attachment if rec.company_id.id == 2 else False,
                'default_x_form_field_01': rec.x_form_field_01 if rec.company_id.id == 2 else False,
                'default_x_form_field_02': rec.x_form_field_02 if rec.company_id.id == 2 else False,
                'default_x_form_field_03': rec.x_form_field_03 if rec.company_id.id == 2 else False,
                'default_x_form_field_04': rec.x_form_field_04 if rec.company_id.id == 2 else False,
                'default_x_form_field_05': rec.x_form_field_05 if rec.company_id.id == 2 else False,
                'default_x_form_field_06': rec.x_form_field_06 if rec.company_id.id == 2 else False,
                'default_x_form_field_07': rec.x_form_field_07 if rec.company_id.id == 2 else False,
                'default_x_form_field_08': rec.x_form_field_08 if rec.company_id.id == 2 else False,
                'default_x_form_field_09': rec.x_form_field_09 if rec.company_id.id == 2 else False,
                'default_x_form_field_10': rec.x_form_field_10 if rec.company_id.id == 2 else False,
                'default_x_form_field_11': rec.x_form_field_11 if rec.company_id.id == 2 else False,
                'default_x_form_field_12': rec.x_form_field_12 if rec.company_id.id == 2 else False,
                'default_x_form_field_13': rec.x_form_field_13.id if rec.company_id.id == 2 else False,
                'default_x_form_field_14': rec.x_form_field_14.id if rec.company_id.id == 2 else False,
            }
            return dict(action, view_mode='form', views=[(False, 'form')])


    def action_view_bills(self):
        for rec in self:
            action = self.env.ref('cus_logistics_tracking.view_picking_related_bills_action').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': [rec.id],
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                'default_partner_id': rec.partner_id.id if rec.picking_type_code == 'incoming' else False,
                'default_partner_shipping_id': rec.partner_id.id if rec.picking_type_code == 'incoming' else False,
                'default_invoice_date': datetime.datetime.now(
                    pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'default_x_purchase_type': 'Forwarding' if rec.picking_type_code == 'incoming' else False,
                'default_x_item_type': 'Landed Cost' if rec.picking_type_code == 'incoming' else False,
                'default_x_related_po_s': [rec.purchase_id.id] if rec.picking_type_code == 'incoming' else [],

                'default_x_attachment_name': rec.x_attachment_name if rec.company_id.id == 2 else False,
                'default_x_attachment': rec.x_attachment if rec.company_id.id == 2 else False,
                'default_x_form_field_01': rec.x_form_field_01 if rec.company_id.id == 2 else False,
                'default_x_form_field_02': rec.x_form_field_02 if rec.company_id.id == 2 else False,
                'default_x_form_field_03': rec.x_form_field_03 if rec.company_id.id == 2 else False,
                'default_x_form_field_04': rec.x_form_field_04 if rec.company_id.id == 2 else False,
                'default_x_form_field_05': rec.x_form_field_05 if rec.company_id.id == 2 else False,
                'default_x_form_field_06': rec.x_form_field_06 if rec.company_id.id == 2 else False,
                'default_x_form_field_07': rec.x_form_field_07 if rec.company_id.id == 2 else False,
                'default_x_form_field_08': rec.x_form_field_08 if rec.company_id.id == 2 else False,
                'default_x_form_field_09': rec.x_form_field_09 if rec.company_id.id == 2 else False,
                'default_x_form_field_10': rec.x_form_field_10 if rec.company_id.id == 2 else False,
                'default_x_form_field_11': rec.x_form_field_11 if rec.company_id.id == 2 else False,
                'default_x_form_field_12': rec.x_form_field_12 if rec.company_id.id == 2 else False,
                'default_x_form_field_13': rec.x_form_field_13.id if rec.company_id.id == 2 else False,
                'default_x_form_field_14': rec.x_form_field_14.id if rec.company_id.id == 2 else False,
            }
            action['domain'] = [('x_picking_ids', 'ilike', rec.id)]
            return action


    def action_view_picking_sale_order(self):
        for rec in self:
            action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
            return dict(action, view_mode='form', res_id=rec.x_sale_id.id, views=[(False, 'form')])


    def action_view_picking_purchase_order(self):
        for rec in self:
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            return dict(action, view_mode='form', res_id=rec.purchase_id.id, views=[(False, 'form')])


    def _compute_related_landed_cost(self):
        for rec in self:
            if rec.picking_type_id.code in ('incoming', 'outgoing'):
                rec.x_landed_cost_ids = self.env['stock.landed.cost'].search([('picking_ids', 'ilike', rec.id)]).ids
                rec.x_landed_cost_count = len(rec.x_landed_cost_ids)
            else:
                rec.x_landed_cost_ids = False
                rec.x_landed_cost_count = 0


    @api.depends('x_landed_cost_ids')
    def _compute_landed_cost_count(self):
        for rec in self:
            rec.x_landed_cost_count = len(rec.x_landed_cost_ids.ids)


    def action_view_landed_costs(self):
        self.ensure_one()
        action = self.env.ref('stock_landed_costs.action_stock_landed_cost').read()[0]
        domain = [('id', 'in', self.x_landed_cost_ids.ids)]
        context = dict(self.env.context, default_vendor_bill_id=self.id)
        views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree').id, 'tree'), (False, 'form'),
                 (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)


    @api.depends('x_consolidation_ids')
    def _compute_consolidations_count(self):
        for rec in self:
            rec.x_consolidation_count = len(rec.x_consolidation_ids.ids)


    def action_view_consolidations(self):
        self.ensure_one()
        action = self.env.ref('cus_logistics_tracking.action_consolidation_tracking').read()[0]
        domain = [('id', 'in', self.x_consolidation_ids.ids)]
        context = dict(self.env.context, default_vendor_bill_id=self.id)
        views = [(self.env.ref('cus_logistics_tracking.consolidation_tracking_view_tree').id, 'tree'), (False, 'form'),
                 (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)


    @api.depends('x_related_warehousing_id.state')
    def mark_tracking_as_in_stock(self):
        for rec in self:
            if rec.x_related_warehousing_id.state == 'done' and rec.state != 'cancel':
                rec.x_tracking_status = 'in_stock'


    # def action_start_warehousing(self):
    #     for rec in self:
    #         if rec.x_landed_cost_ids.filtered(lambda l: l.state == 'draft'):
    #             raise UserError("Cannot start warehousing. Some landed costs are in draft!")
    #         rec.x_tracking_status = 'start_warehousing'
    #         action = self.env.ref('stock.action_picking_tree_all').read()[0]
    #         form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
    #         if 'views' in action:
    #             action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
    #         else:
    #             action['views'] = form_view
    #         action['res_id'] = rec.x_related_incoming_id.id
    #         action['context'] = dict(self._context, default_origin=self.name, create=False)
    #         return action

    def open_url(self):
        for rec in self:
            if rec.carrier_id.x_tracking_url and rec.carrier_tracking_ref:
                return {
                    'type': 'ir.actions.act_url',
                    'url': rec.carrier_id.x_tracking_url.replace('{Tracking Ref}', rec.carrier_tracking_ref),
                    'target': 'new',
                }


    def mark_as_backorder(self):
        for rec in self:
            rec.x_backorder_products = True
            rec.x_backorder = 'backorder'
            rec.x_tracking_status = 'backorder'
            rec.move_ids_without_package.write({'quantity_done': 0})


    def mark_as_regular_order(self):
        for rec in self:
            rec.x_backorder_products = False
            rec.x_backorder = False
            rec.x_tracking_status = 'new'


    def action_cancel(self):
        for rec in self:
            rec.x_tracking_status = 'cancelled'
        return super(StockPicking, self).action_cancel()


    def action_done(self):
        for rec in self:
            if rec.picking_type_code in ('incoming', 'outgoing') and not rec.x_form_field_09:
                raise UserError("Please enter In/Out Date!")
        res = super(StockPicking, self).action_done()
        for rec in self:
            if rec.x_form_field_09:
                rec.change_picking_effective_date_to_in_out_date()
            if rec.picking_type_code != 'incoming':
                continue
            rec.x_tracking_status = 'arrived'
            rec.partner_id = rec.purchase_id.partner_id.id or rec.partner_id.id
            picking_id = self.env['stock.picking'].search([
                ('group_id', '=', rec.group_id.id), ('picking_type_code', '=', 'internal')
            ], limit=1, order='id desc')
            # ], limit=2, order='id desc')
            # if len(picking_ids) > 1:
            #     rec.x_related_warehousing_id, rec.x_related_incoming_id = picking_ids.ids
            #     rec.x_purchase_id = rec.purchase_id.id
            #     rec.x_related_warehousing_id.x_purchase_id = rec.purchase_id.id
            #     rec.x_related_incoming_id.x_purchase_id = rec.purchase_id.id
            # elif len(picking_ids) == 1:
            rec.x_related_warehousing_id = picking_id.id
            rec.x_purchase_id = rec.purchase_id.id
            rec.x_related_warehousing_id.x_purchase_id = rec.purchase_id.id
            account_move_ids = rec.move_ids_without_package.mapped('account_move_ids')
            if rec.company_id.id == 2 and rec.picking_type_code == 'incoming' and rec.x_form_field_09:
                account_move_ids.update({
                    'date': rec.x_form_field_09,
                    'x_move_type': 'receipt_entry',
                    'x_related_purchase_id': rec.purchase_id.id,
                    'x_attachment_name': rec.x_attachment_name,
                    'x_attachment': rec.x_attachment,
                    'x_form_field_01': rec.x_form_field_01,
                    'x_form_field_02': rec.x_form_field_02,
                    'x_form_field_03': rec.x_form_field_03,
                    'x_form_field_04': rec.x_form_field_04,
                    'x_form_field_05': rec.x_form_field_05,
                    'x_form_field_06': rec.x_form_field_06,
                    'x_form_field_07': rec.x_form_field_07,
                    'x_form_field_08': rec.x_form_field_08,
                    'x_form_field_09': rec.x_form_field_09,
                    'x_form_field_10': rec.x_form_field_10,
                    'x_form_field_11': rec.x_form_field_11,
                    'x_form_field_12': rec.x_form_field_12,
                    'x_form_field_13': rec.x_form_field_13.id,
                    'x_form_field_14': rec.x_form_field_14.id,
                })
        return res


    @api.onchange('x_tracking_id')
    def update_logistics_info(self):
        for rec in self:
            if rec.x_tracking_id:
                rec.carrier_id = rec.x_tracking_id.x_carrier_id.id
                rec.carrier_tracking_ref = rec.x_tracking_id.x_tracking_ref
                rec.x_awb = rec.x_tracking_id.x_tracking_ref


    @api.onchange('x_auto_fill_done_quantity')
    def update_done_quantity(self):
        for rec in self:
            if rec.state not in ['done', 'cancel']:
                for line in rec.move_ids_without_package:
                    line.quantity_done = line.product_uom_qty if rec.x_auto_fill_done_quantity else 0


    @api.depends('backorder_id')
    def _compute_backorder_tag(self):
        for rec in self:
            rec.x_backorder = 'backorder' if rec.backorder_id else False
            rec.x_tracking_status = 'backorder' if rec.backorder_id else 'new'


    @api.depends('x_tracking_id.x_route_id', 'x_tracking_id.x_sub_route_id', 'x_tracking_id.x_state',
                 'x_forwarder_tracking_id.x_route_id', 'x_forwarder_tracking_id.x_sub_route_id',
                 'x_forwarder_tracking_id.x_state')
    def _compute_logistics_info(self):
        for rec in self:
            if not rec.x_forwarder_tracking_id:
                rec.x_route_id = rec.x_tracking_id.x_route_id.id
                rec.x_sub_route_id = rec.x_tracking_id.x_sub_route_id.id
                rec.x_tracking_state = rec.x_tracking_id.x_state
            elif rec.x_forwarder_tracking_id:
                rec.x_route_id = rec.x_forwarder_tracking_id.x_route_id.id
                rec.x_sub_route_id = rec.x_forwarder_tracking_id.x_sub_route_id.id
                rec.x_tracking_state = rec.x_forwarder_tracking_id.x_state

            tracking_status = rec.x_tracking_status
            if rec.x_tracking_id or rec.x_forwarder_tracking_id and rec.state != 'done':
                tracking_status = 'in_transit'
            if rec.x_sub_route_id.x_to.id == rec.company_id.partner_id.id and rec.x_tracking_state == 'done':
                tracking_status = 'arrived'
            rec.x_tracking_status = tracking_status


    @api.depends('state', 'scheduled_date')
    def _compute_color(self):
        for rec in self:
            current_data = datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz))
            if rec.state == 'draft':
                rec.color = 8
            elif rec.state == 'cancel':
                rec.color = 3
            elif rec.state not in ('cancel', 'done') and rec.scheduled_date.date() < current_data.date():
                rec.color = 9
            else:
                rec.color = 0


    @api.model
    def update_picking_color(self):
        self.env['stock.picking'].search([])._compute_color()
