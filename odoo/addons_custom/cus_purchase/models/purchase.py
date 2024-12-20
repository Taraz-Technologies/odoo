from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

import datetime
import pytz
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    x_payment_invoice_ids = fields.Many2many(comodel_name='account.move', string='Payment Invoices',
                                             relation="account_move_purchase_order_rel_00", column1="id1", column2="id2")
    x_bill_count = fields.Integer(compute='_compute_bill_count', store=True)
    x_product_tag = fields.Many2many(comodel_name="product.tags", relation="purchase_order_product_tags_rel",
                                     column1="purchase_order_id", column2="product_tags_id", string="Product Tags", )
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')
    x_internal_notes = fields.Text(string="Internal Notes", tracking=True)

    x_is_commented = fields.Boolean(string="Has Notes", compute="_compute_is_commented")

    @api.depends('x_internal_notes')
    def _compute_is_commented(self):
        for record in self:
            record.x_is_commented = bool(record.x_internal_notes)

    def action_show_notes(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.id,
        }

    @api.constrains('partner_id', 'partner_ref')
    def check_vendor_uniqueness(self):
        # vendors = self.env['purchase.order'].search([('partner_ref', '!=', False)]).mapped('partner_ref')
        for record in self:
            if record.partner_id and record.partner_ref:
                # Search for any record with the same partner_id and partner_ref
                existing_record = self.search([
                    ('partner_id', '=', record.partner_id.id),
                    ('partner_ref', '=', record.partner_ref),
                ])
                if len(existing_record) != 1:
                    raise ValidationError('The Vendor Reference must be unique for the same Vendor.')

    def write(self, vals):
        for rec in self:
            for line in rec.order_line:
                line.product_id.x_product_tag = [(3, tag) for tag in rec.x_product_tag.ids]
        old_values = self.x_tag_ids.ids
        res = super(PurchaseOrder, self).write(vals)
        new_values = self.x_tag_ids.ids
        if 'x_tag_ids' in vals:
            self.x_tag_ids._track_many2many_changes(
                self, 'x_tag_ids', old_values=old_values, new_values=new_values
            )
        for rec in self:
            for line in rec.order_line:
                line.product_id.x_product_tag = [(4, tag) for tag in rec.x_product_tag.ids]
        return res

    @api.depends('picking_ids.x_bill_count')
    def _compute_bill_count(self):
        for rec in self:
            rec.x_bill_count = sum(rec.picking_ids.mapped('x_bill_count'))

    # def button_confirm(self):
    #     for rec in self:
    #         rec.partner_id.commercial_partner_id.create_related_accounts()
    #     return super(PurchaseOrder, self).button_confirm()

    def action_create_payment_bills(self):
        for rec in self:
            if rec.company_id.id != self.env.company.id:
                raise UserError("Odoo selected company is not same as the order company!")
            account_inv_obj = self.env['account.move']
            if self.currency_id == rec.company_id.currency_id:
                currency = False
            else:
                currency = rec.currency_id

            service_lines = rec.order_line.filtered(lambda l: not l.display_type and l.product_id.type == 'service' and l.qty_invoiced <= 0)
            service_lines_amount = sum(service_lines.mapped('price_subtotal'))

            invoice_ids = []
            for line in rec.payment_term_id.line_ids.filtered(lambda l: l.value_amount > 0):
                vals = {
                    'type': 'in_invoice',
                    'invoice_origin': rec.name,
                    'invoice_date': datetime.date.today(),
                    'journal_id': rec.company_id.x_payment_bill_journal_id.id,
                    'partner_id': rec.partner_id.id,
                    'currency_id': rec.currency_id.id,
                    'purchase_id': rec.id,
                    'ref': rec.partner_ref,
                    'x_operation_type': rec.x_operation_type,
                    'x_document': rec.x_attachment,
                    'x_related_po_s': rec.x_related_po_s.ids,
                    'x_related_so_s': rec.x_related_so_s.ids,
                    'invoice_incoterm_id': rec.incoterm_id.id,
                    'invoice_payment_term_id': rec.payment_term_id.id,
                    'x_payment_method': rec.x_payment_method.id,
                    'x_purchase_type': rec.x_purchase_type,
                    'x_item_type': rec.x_item_type,
                    'x_import_method': rec.x_import_method,
                    'x_weboc_gd': rec.x_weboc_gd,
                    'x_assessed_value': rec.x_assessed_value,
                    'x_comments': rec.x_comments,
                    'invoice_line_ids': [(0, 0, {
                        'name': '%s of %s%%' % (rec.company_id.x_product_id.name, line.value_amount),
                        'price_unit': (rec.amount_untaxed * line.value_amount / 100) - (service_lines_amount * line.value_amount / 100),
                        'quantity': 1,
                        'product_id': rec.company_id.x_product_id.id,
                        'discount': 0,
                        'account_id': rec.partner_id.commercial_partner_id.x_vendor_advance_account_id.id,
                        'product_uom_id': rec.company_id.x_product_id.uom_id.id,
                        'currency_id': currency and currency.id or False,
                    }), (0, 0, {
                        'name': 'Tax %s of %s%%' % (rec.company_id.x_product_id.name, line.value_amount),
                        'price_unit': (rec.amount_tax * line.value_amount / 100),
                        'quantity': 1,
                        'product_id': rec.company_id.x_product_id.id,
                        'discount': 0,
                        'account_id': rec.partner_id.commercial_partner_id.x_vendor_advance_account_id.id,
                        'product_uom_id': rec.company_id.x_product_id.uom_id.id,
                        'currency_id': currency and currency.id or False,
                    })],
                }
                res = account_inv_obj.sudo().create(vals)
                new_lines = []
                for service_line in service_lines:
                    qty = service_line.product_qty * line.value_amount / 100
                    if float_compare(qty, 0.0, precision_rounding=service_line.product_uom.rounding) <= 0:
                        qty = 0.0

                    if service_line.currency_id == res.company_id.currency_id:
                        currency = False
                    else:
                        currency = res.currency_id
                    if qty != 0:
                        new_lines.append((0, 0, {
                            'name': '%s [Qty: %s]\n%s' % (service_line.product_id.name, qty, service_line.name),
                            'move_id': res.id,
                            'currency_id': currency and currency.id or False,
                            'purchase_line_id': service_line.id,
                            'date_maturity': res.invoice_date_due,
                            'product_uom_id': service_line.product_uom.id,
                            'product_id': service_line.product_id.id,
                            'price_unit': service_line.price_unit,
                            'quantity': qty,
                            'partner_id': res.partner_id.id,
                            'analytic_account_id': service_line.account_analytic_id.id,
                            'analytic_tag_ids': [(6, 0, service_line.analytic_tag_ids.ids)],
                            'tax_ids': [(6, 0, service_line.taxes_id.ids)],
                            'display_type': service_line.display_type,
                            'is_landed_costs_line': service_line.product_id.landed_cost_ok,
                        }))
                res.write({
                    'invoice_line_ids': new_lines,
                    # 'purchase_id': False
                })
                for invoice_line in res.invoice_line_ids.filtered(lambda l: l.is_landed_costs_line):
                    invoice_line._onchange_is_landed_costs_line()
                invoice_ids.append(res.id)
            rec.x_payment_invoice_ids = invoice_ids
            # # Service Bill
            # service_lines = rec.order_line.filtered(lambda l: not l.display_type and l.product_id.type == 'service' and l.qty_invoiced <= 0)
            # if service_lines:
            #     vals = {
            #         'type': 'in_invoice',
            #         'invoice_origin': rec.name,
            #         'invoice_date': datetime.date.today(),
            #         'journal_id': rec.company_id.x_service_bill_journal_id.id,
            #         'partner_id': rec.partner_id.id,
            #         'currency_id': rec.currency_id.id,
            #     }
            #     res = account_inv_obj.sudo().create(vals)
            #     new_lines = []
            #     for line in service_lines.filtered(lambda l: not l.display_type and l.product_id.type == 'service' and l.qty_invoiced <= 0):
            #         if line._prepare_account_move_line(res)['quantity'] != 0:
            #             new_lines.append((0, 0, line._prepare_account_move_line(res)))
            #             new_lines.append((0, 0, line._prepare_advance_account_move_line(res)))
            #     res.write({
            #         'invoice_line_ids': new_lines,
            #         # 'purchase_id': False
            #     })
            #     for line in res.invoice_line_ids.filtered(lambda l: l.is_landed_costs_line):
            #         line._onchange_is_landed_costs_line()

    @api.depends('order_line.invoice_lines.move_id', 'x_payment_invoice_ids.state')
    def _compute_invoice(self):
        super(PurchaseOrder, self)._compute_invoice()
        for order in self:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            order.invoice_ids = invoices + order.x_payment_invoice_ids
            order.invoice_count = len(order.invoice_ids)

    def action_create_related_bill(self):
        for rec in self:
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': rec.picking_ids.ids,
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                'default_invoice_date': datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'default_x_purchase_type': 'Forwarding',
                'default_x_item_type': 'Landed Cost',
                'default_x_related_po_s': [rec.id],
            }
            return dict(action, view_mode='form', views=[(False, 'form')])

    def action_view_related_bills(self):
        for rec in self:
            action = self.env.ref('cus_logistics_tracking.view_picking_related_bills_action').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': rec.picking_ids.ids,
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                'default_invoice_date': datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'default_x_purchase_type': 'Forwarding',
                'default_x_item_type': 'Landed Cost',
                'default_x_related_po_s': [rec.id],
            }
            action['domain'] = [('x_picking_ids', 'ilike', rec.picking_ids.ids)]
            return action

    def action_view_free_zone_operations(self):
        self.ensure_one()
        action = self.env.ref('cus_logistics_tracking.free_zone_operations_action').read()[0]
        operation_ids = self.env['free.zone.receipts'].search([('x_purchase_id', '=', self.id)]).mapped('x_operation_id')
        domain = [('id', 'in', operation_ids.ids)]
        views = [(self.env.ref('cus_logistics_tracking.free_zone_operations_view_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, views=views)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_original_price_unit = fields.Float(string='ORG Unit', required=False)
    x_original_price_subtotal = fields.Float(string='ORG Ext.', compute="compute_original_price_subtotal", store=True)

    x_name_translation = fields.Char(related="product_id.x_name_translation")
    x_description_translation = fields.Text(related="product_id.x_description_translation")

    def _get_product_purchase_description(self, product_lang):
        super(PurchaseOrderLine, self)._get_product_purchase_description(product_lang)
        name = product_lang.display_name
        if product_lang.description:
            name = product_lang.description
        return name

    @api.depends('x_original_price_unit', 'product_qty')
    def compute_original_price_subtotal(self):
        for rec in self:
            rec.x_original_price_subtotal = rec.x_original_price_unit * rec.product_qty

    @api.model
    def create(self, vals):
        tag_name = self.env['purchase.order'].browse(vals.get('order_id')).name
        tag_id = self.env['account.analytic.tag'].search([('name', '=', tag_name)])
        if not tag_id:
            tag_id = self.env['account.analytic.tag'].create({
                'name': tag_name,
                # 'company_id': vals.get('company_id'),
                # 'color': 1,
            })
        vals['analytic_tag_ids'] = [(4, tag_id.id)]
        return super(PurchaseOrderLine, self).create(vals)

    def _prepare_advance_account_move_line(self, move):
        self.ensure_one()
        if self.product_id.purchase_method == 'purchase':
            qty = self.product_qty - self.qty_invoiced
        else:
            qty = self.qty_received - self.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        return {
            'name': '%s: %s' % (self.company_id.x_product_id.name, self.name),
            'price_unit': self.price_unit,
            'quantity': - qty,
            'product_id': self.company_id.x_product_id.id,
            'discount': self.x_discount,
            'account_id': move.partner_id.commercial_partner_id.x_vendor_advance_account_id.id,
            'product_uom_id': self.company_id.x_product_id.uom_id.id,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'move_id': move.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
        }




