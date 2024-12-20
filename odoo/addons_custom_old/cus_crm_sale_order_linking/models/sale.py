from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date

from dateutil.relativedelta import relativedelta
import json
import logging

_logger = logging.getLogger("*__addons_custom__*")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_show_fluctuation_remark = fields.Boolean(string='Fluctuation Remark?',
                                               compute="_compute_fluctuation_remarks", store=True)
    x_fluctuation_remark = fields.Text(string="Fluctuation Remarks", compute="_compute_fluctuation_remarks",
                                       store=True, tracking=True)

    x_update_crm_lead_stage = fields.Boolean(compute="update_crm_lead_stage")
    x_update_crm_lead_name = fields.Boolean(compute="update_crm_lead_name")
    x_update_crm_lead_values = fields.Boolean(compute="update_crm_lead_values")

    x_so_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency',
                                       related="pricelist_id.currency_id", tracking=True)
    x_currency_symbol = fields.Char(string='Symbol', related="currency_id.symbol", tracking=True)
    x_currency_rate = fields.Float(string='Currency Rate', compute="_compute_currency_rate", store=True, tracking=True)
    x_currency_date = fields.Date(string='Currency Date', default=date.today(), tracking=True)
    x_fluctuation_limit = fields.Float(string='Fluctuation Limit (%)', required=False, tracking=True)

    x_total_amount_usd = fields.Float(string='Total Amount ($)', compute="_compute_currency_amounts",
                                      store=True, tracking=True)

    x_fluctuated_amount_usd = fields.Float(string='Fluctuated Amount ($)', compute="_compute_currency_amounts",
                                           store=True, tracking=True)
    x_fluctuated_amount_per = fields.Float(string='Fluctuated Amount (%)', compute="_compute_currency_amounts",
                                           store=True, tracking=True)

    x_show_invalid_flag = fields.Boolean(string='Show Invalid Flag', required=False)
    
    x_crm_stage_id = fields.Many2one(comodel_name='crm.stage', string='CRM Stage',
                                     related="opportunity_id.stage_id", readonly=False)

    @api.depends('currency_id', 'x_currency_rate', 'x_fluctuation_limit')
    def _compute_fluctuation_remarks(self):
        for rec in self:
            rec.x_show_fluctuation_remark = True if rec.currency_id.name != 'USD' else False
            rec.x_fluctuation_remark = "Quoted prices are based on %s %s/USD rate of exchange and " \
                                       "shall be subject to adjustment in case of exchange rate changes " \
                                       "by more than %s%s." % (rec.x_currency_rate, rec.currency_id.name,
                                                               rec.x_fluctuation_limit, '%')

    @api.onchange('x_fluctuation_limit', 'x_fluctuated_amount_per')
    def get_flag_domain(self):
        for rec in self:
            rec.x_show_invalid_flag = False if rec.x_fluctuation_limit >= rec.x_fluctuated_amount_per else True

    @api.depends('currency_id', 'x_currency_date')
    def _compute_currency_rate(self):
        for rec in self:
            rec.x_currency_rate = rec.currency_id.with_context(date=rec.x_currency_date).rate

    @api.depends('amount_total', 'invoice_status', 'x_so_payment_state', 'x_currency_rate')
    def _compute_currency_amounts(self):
        for rec in self:
            total_amount_usd = 0
            fluctuated_amount_usd = 0
            fluctuated_amount_per = 0

            if rec.invoice_status != 'invoiced' and rec.x_so_payment_state != 'paid':
                total_amount_usd = rec.amount_total / rec.x_currency_rate if rec.x_currency_rate != 0 else 0

                today_currency_rate = rec.currency_id.with_context(date=date.today()).rate
                if today_currency_rate == 0:
                    today_currency_rate = rec.currency_id.with_context(date=date.today() - relativedelta(days=1)).rate

                if today_currency_rate != 0:
                    fluctuated_amount_usd = total_amount_usd * rec.x_currency_rate / today_currency_rate
                    if total_amount_usd != 0:
                        fluctuated_amount_per = (total_amount_usd - fluctuated_amount_usd) / total_amount_usd * 100

            rec.x_total_amount_usd = total_amount_usd
            rec.x_fluctuated_amount_usd = fluctuated_amount_usd
            rec.x_fluctuated_amount_per = fluctuated_amount_per

    @api.model
    def _update_currency_loss(self):
        order_ids = self.env['sale.order'].search([])
        # order_ids.update_crm_lead_amount_lines()

    @api.depends('state', 'x_so_payment_state', 'invoice_status', 'company_id')
    def update_crm_lead_stage(self):
        for rec in self:
            if rec.opportunity_id:
                rec.opportunity_id.company_id = rec.company_id.id
                if rec.state == 'cancel':
                    rec.opportunity_id.stage_id = 9
                elif rec.state in ['draft', 'sent']:
                    rec.opportunity_id.stage_id = 2
                elif rec.state in ['sale', 'done'] and rec.x_so_payment_state == 'paid' and rec.invoice_status == 'invoiced':
                    rec.opportunity_id.stage_id = 7
                elif rec.state in ['sale', 'done'] and rec.opportunity_id.stage_id.id in (2, 11, 3):
                    rec.opportunity_id.stage_id = 4
            else:
                rec.create_crm_lead()
            rec.x_update_crm_lead_stage = True

    @api.depends('x_folder_name', 'amount_total')
    def update_crm_lead_name(self):
        for rec in self:
            if rec.opportunity_id:
                if rec.currency_id.name != 'USD':
                    name = "%s (%s%s)" % (rec.x_folder_name, rec.currency_id.symbol, rec.amount_total)
                else:
                    name = rec.x_folder_name
                rec.opportunity_id.name = name
            else:
                rec.create_crm_lead()
            rec.x_update_crm_lead_name = True

    @api.depends('partner_id', 'user_id', 'team_id')
    def update_crm_lead_values(self):
        for rec in self:
            if rec.opportunity_id:
                rec.opportunity_id.partner_id = rec.partner_id.id
                rec.opportunity_id.user_id = rec.user_id.id
                rec.opportunity_id.team_id = rec.team_id.id
            else:
                rec.create_crm_lead()
            rec.x_update_crm_lead_values = True

    def update_crm_lead_amount_lines(self):
        for rec in self:
            if rec.opportunity_id:
                currency_rate = rec.x_currency_rate
                line_date = rec.date_order
                amount_total = round(rec.amount_total / currency_rate, 2) if rec.x_currency_rate != 0 else 0
                crm_lead_id = rec.opportunity_id
                crm_lead_id.x_sale_order_amount_ids = [(2, line.id) for line in crm_lead_id.x_sale_order_amount_ids]
                sale_order_amounts = [(0, 0, {
                    'x_name': 'Total',
                    'x_amount': round(amount_total, 2),
                    'x_date': line_date,
                    'x_currency_id': 2,
                    'x_amount_type': 'total',
                })]

                if rec.payment_term_id:
                    count = 1
                    term_len = len(rec.payment_term_id.line_ids)
                    invoice_ids = []
                    for line in rec.payment_term_id.line_ids:
                        add_line = True if term_len == 1 else True if line.value_amount != 0 else False
                        if not add_line:
                            continue

                        name_vals = (line.value_amount, '%', line.x_report_remark)
                        amount_type = 'receivable' if line.days == 0 else 'receivable' if term_len == 1 else 'deferred'
                        line_amount = amount_total * line.value_amount / 100

                        amount = rec.amount_total * line.value_amount / 100
                        invoice_id = False
                        for invoice in list(reversed(rec.invoice_ids)):
                            if invoice.state == 'cancel' or invoice.id in invoice_ids:
                                continue
                            elif round(invoice.amount_total, 0) == round(amount, 0):
                                invoice_ids.append(invoice.id)
                                invoice_id = invoice.id
                                break

                        sale_order_amounts.append((0, 0, {
                            'x_name': '%s%s %s' % name_vals if term_len != 1 else 'Receivable',
                            'x_amount': round(line_amount, 2) if term_len != 1 else amount_total,
                            'x_date': line_date + relativedelta(days=line.days),
                            'x_currency_id': 2,
                            'x_amount_type': amount_type,
                            'x_payment_count': count,
                            'x_invoice_id': invoice_id,
                        }))

                        if rec.pricelist_id.id not in [1, 2] and not rec.invoice_ids:
                            loss_per = rec.x_fluctuated_amount_per
                            loss = amount_total * line.value_amount * loss_per / 10000
                            loss = amount_total * loss_per / 100 if term_len == 1 else loss

                            sale_order_amounts.append((0, 0, {
                                'x_name': '%s @%s%s' % ('C. Loss', round(loss_per, 2), '%'),
                                'x_amount': round(loss, 2),
                                'x_date': line_date,
                                'x_currency_id': 2,
                                'x_amount_type': 'currency_loss',
                                'x_payment_count': count,
                            }))
                        count += 1

                if rec.pricelist_id.id not in [1, 2] and rec.invoice_ids:
                    usd = self.env['res.currency'].search([('name', '=', 'USD')])
                    amount_so = 0
                    amount_invoice = 0
                    for invoice in list(reversed(rec.invoice_ids)):
                        if invoice.state == 'cancel':
                            continue

                        cl_date = invoice.invoice_date
                        inv_amount_so = 0
                        inv_amount_invoice = 0
                        invoice_payments = []
                        if json.loads(invoice.invoice_payments_widget):
                            payments = json.loads(invoice.invoice_payments_widget)
                            for payment in payments['content']:
                                invoice_payments.append({'date': payment['date'], 'amount': payment['amount']})
                        if invoice_payments:
                            for payment in invoice_payments:
                                if payment['date']:
                                    cl_date = payment['date']
                                    inv_amount_so = payment['amount'] / currency_rate if currency_rate != 0 else 0
                                    inv_amount_invoice = rec.currency_id._convert(payment['amount'], usd,
                                                                                  self.env.company, payment['date'])
                        else:
                            cl_date = date.today() - relativedelta(days=1)
                            inv_amount_so = invoice.amount_total / currency_rate if currency_rate != 0 else 0
                            inv_amount_invoice = rec.currency_id._convert(invoice.amount_total, usd, self.env.company,
                                                                          date.today() - relativedelta(days=1))

                        loss = inv_amount_so - inv_amount_invoice
                        loss_per = loss / inv_amount_so * 100 if inv_amount_so != 0 else 0

                        sale_order_amounts.append((0, 0, {
                            'x_name': '%s @%s%s' % ('C. Loss', round(loss_per, 2), '%'),
                            'x_amount': round(loss, 2),
                            'x_date': cl_date,
                            'x_currency_id': 2,
                            'x_amount_type': 'currency_loss',
                            'x_invoice_id': invoice.id,
                        }))

                        amount_so += inv_amount_so
                        amount_invoice += inv_amount_invoice

                    if len(rec.invoice_ids) > 1:
                        loss = amount_so - amount_invoice
                        loss_per = loss / amount_so * 100 if amount_so != 0 else 0

                        sale_order_amounts.append((0, 0, {
                            'x_name': '%s @%s%s' % ('A.C. Loss', round(loss_per, 2), '%'),
                            'x_amount': round(loss, 2),
                            'x_date': line_date,
                            'x_currency_id': 2,
                            'x_amount_type': 'currency_loss',
                        }))

                crm_lead_id.x_sale_order_amount_ids = sale_order_amounts

    def create_crm_lead(self):
        for rec in self:
            currency_rate = rec.x_currency_rate
            line_date = rec.date_order
            amount_total = rec.amount_total / currency_rate if currency_rate != 0 else 0
            name_vals = (rec.x_folder_name,  rec.currency_id.symbol, round(rec.amount_total, 2))
            name = "%s (%s%s)" % name_vals if rec.currency_id.name != 'USD' else rec.x_folder_name

            vals = {
                'name': name,
                'partner_id': rec.partner_id.id,
                'user_id': rec.user_id.id,
                'team_id': rec.team_id.id,
                'type': 'opportunity',
                'planned_revenue': round(amount_total, 2),
                'stage_id': 2,
                'company_id': rec.company_id.id,
                'x_sale_order_amount_ids': [(0, 0, {
                    'x_name': 'Total',
                    'x_amount': round(amount_total, 2),
                    'x_date': line_date,
                    'x_currency_id': 2,
                    'x_amount_type': 'total',
                })],
            }

            if rec.payment_term_id:
                count = 1
                term_len = len(rec.payment_term_id.line_ids)
                invoice_ids = []
                for line in rec.payment_term_id.line_ids:
                    add_line = True if term_len == 1 else True if line.value_amount != 0 else False
                    if not add_line:
                        continue

                    name_vals = (line.value_amount, '%', line.x_report_remark)
                    amount_type = 'receivable' if line.days == 0 else 'receivable' if term_len == 1 else 'deferred'
                    line_amount = amount_total * line.value_amount / 100

                    amount = rec.amount_total * line.value_amount / 100
                    invoice_id = False
                    for invoice in list(reversed(rec.invoice_ids)):
                        if invoice.state == 'cancel' or invoice.id in invoice_ids:
                            continue
                        elif round(invoice.amount_total, 0) == round(amount, 0):
                            invoice_ids.append(invoice.id)
                            invoice_id = invoice.id
                            break

                    vals['x_sale_order_amount_ids'].append((0, 0, {
                        'x_name': '%s%s %s' % name_vals if term_len != 1 else 'Receivable',
                        'x_amount': round(line_amount, 2) if term_len != 1 else amount_total,
                        'x_date': line_date + relativedelta(days=line.days),
                        'x_currency_id': 2,
                        'x_amount_type': amount_type,
                        'x_payment_count': count,
                        'x_invoice_id': invoice_id,
                    }))

                    if rec.pricelist_id.id not in [1, 2] and not rec.invoice_ids:
                        loss_per = rec.x_fluctuated_amount_per
                        loss = amount_total * line.value_amount * loss_per / 10000
                        loss = amount_total * loss_per / 100 if term_len == 1 else loss

                        vals['x_sale_order_amount_ids'].append((0, 0, {
                            'x_name': '%s @%s%s' % ('C. Loss', round(loss_per, 2), '%'),
                            'x_amount': round(loss, 2),
                            'x_date': line_date,
                            'x_currency_id': 2,
                            'x_amount_type': 'currency_loss',
                            'x_payment_count': count,
                        }))
                    count += 1

            if rec.pricelist_id.id not in [1, 2] and rec.invoice_ids:
                usd = self.env['res.currency'].search([('name', '=', 'USD')])
                amount_so = 0
                amount_invoice = 0
                for invoice in list(reversed(rec.invoice_ids)):
                    if invoice.state == 'cancel':
                        continue

                    cl_date = invoice.invoice_date
                    inv_amount_so = 0
                    inv_amount_invoice = 0
                    invoice_payments = []
                    if json.loads(invoice.invoice_payments_widget):
                        payments = json.loads(invoice.invoice_payments_widget)
                        for payment in payments['content']:
                            invoice_payments.append({'date': payment['date'], 'amount': payment['amount']})
                    if invoice_payments:
                        for payment in invoice_payments:
                            if payment['date']:
                                cl_date = payment['date']
                                inv_amount_so = payment['amount'] / currency_rate if currency_rate != 0 else 0
                                inv_amount_invoice = rec.currency_id._convert(payment['amount'], usd,
                                                                              self.env.company, payment['date'])
                    else:
                        cl_date = date.today() - relativedelta(days=1)
                        inv_amount_so = invoice.amount_total / currency_rate if currency_rate != 0 else 0
                        inv_amount_invoice = rec.currency_id._convert(invoice.amount_total, usd, self.env.company,
                                                                      date.today() - relativedelta(days=1))

                    loss = inv_amount_so - inv_amount_invoice
                    loss_per = loss / inv_amount_so * 100 if inv_amount_so != 0 else 0

                    vals['x_sale_order_amount_ids'].append((0, 0, {
                        'x_name': '%s @%s%s' % ('C. Loss', round(loss_per, 2), '%'),
                        'x_amount': round(loss, 2),
                        'x_date': cl_date,
                        'x_currency_id': 2,
                        'x_amount_type': 'currency_loss',
                        'x_invoice_id': invoice.id,
                    }))

                    amount_so += inv_amount_so
                    amount_invoice += inv_amount_invoice

                if len(rec.invoice_ids) > 1:
                    loss = amount_so - amount_invoice
                    loss_per = loss / amount_so * 100 if amount_so != 0 else 0

                    vals['x_sale_order_amount_ids'].append((0, 0, {
                        'x_name': '%s @%s%s' % ('A.C. Loss', round(loss_per, 2), '%'),
                        'x_amount': round(loss, 2),
                        'x_date': line_date,
                        'x_currency_id': 2,
                        'x_amount_type': 'currency_loss',
                    }))

            crm_lead_id = self.env['crm.lead'].create(vals)
            rec.opportunity_id = crm_lead_id.id

    def unlink(self):
        self.opportunity_id.unlink()
        return super(SaleOrder, self).unlink()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_unit_price_usd = fields.Float(string='Unit Price ($)')
    x_subtotal_usd = fields.Float(string='Subtotal ($)', compute="_compute_price_unit", store=True)

    @api.onchange('product_id')
    def get_price_unit(self):
        for rec in self:
            rec.x_unit_price_usd = rec.product_id.lst_price

    @api.onchange('x_unit_price_usd', 'product_uom_qty', 'discount')
    def update_price_unit(self):
        for rec in self:
            if rec.order_id.state in ['draft', 'sent'] and rec.order_id.pricelist_id.id not in [1, 2]:
                currency_rate = rec.order_id.x_currency_rate
                rec.price_unit = rec.x_unit_price_usd * currency_rate
                rec.x_subtotal_usd = rec.price_subtotal / currency_rate if currency_rate != 0 else 0

    @api.depends('order_id.x_currency_rate')
    def _compute_price_unit(self):
        for rec in self:
            rec.update_price_unit()
