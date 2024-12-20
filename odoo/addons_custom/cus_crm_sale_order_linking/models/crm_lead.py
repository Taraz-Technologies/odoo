from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger("*__addons_custom__*")


class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_sale_order_amount_ids = fields.One2many(
        comodel_name='sale.order.amounts', inverse_name='x_crm_lead_id', string='Sale Order Amounts'
    )

    def action_update_crm_lead_amount_lines(self):
        for rec in self:
            rec.order_ids.update_crm_lead_amount_lines()


class Stage(models.Model):
    _inherit = "crm.stage"

    x_is_done = fields.Boolean(string='Is Done Stage?', required=False)
    x_amount_type = fields.Selection(selection=[
        ('total', 'Total'),
        ('received', 'Received'),
        ('receivable', 'Receivable'),
        ('deferred', 'Deferred'),
        ('currency_loss', 'Currency Loss'), ], string='Amount Type', required=False, )


class SaleOrderAmounts(models.Model):
    _name = "sale.order.amounts"
    _description = 'Sale Order Amounts'
    _rec_name = "display_name"

    x_crm_lead_id = fields.Many2one(comodel_name='crm.lead', string='CRM Lead', required=False)

    x_invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', required=False)
    x_invoice_payment_state = fields.Selection(
        selection=[
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid')
        ], string='Payment', store=True, related="x_invoice_id.invoice_payment_state"
    )

    x_name = fields.Char(string='Name', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', defualt=2, required=False)
    x_amount = fields.Float(string='Amount', required=False)
    x_date = fields.Date(string='Date', required=False)
    x_amount_type = fields.Selection(selection=[
        ('total', 'Total'),
        ('received', 'Received'),
        ('receivable', 'Receivable'),
        ('deferred', 'Deferred'),
        ('currency_loss', 'Currency Loss'),
    ], string='Amount Type', )
    x_compute_amount_status = fields.Boolean(compute="_compute_amount_status")
    display_name = fields.Char(compute="_compute_display_name", store=True)
    x_current_amount = fields.Boolean(string='Current Amount', compute="_compute_current_amounts", store=True)
    x_payment_count = fields.Integer(string='Count', required=False)

    @api.depends('x_invoice_id.invoice_payment_state')
    def _compute_amount_status(self):
        for rec in self:
            if rec.x_amount_type not in ['total', 'currency_loss']:
                if rec.x_invoice_id.invoice_payment_state == 'paid':
                    rec.x_amount_type = 'received'
                elif rec.x_invoice_id.invoice_payment_state in ('in_payment', 'not_paid'):
                    rec.x_amount_type = 'receivable'
            rec.x_compute_amount_status = True

    @api.depends('x_crm_lead_id.stage_id', 'x_amount_type')
    def _compute_current_amounts(self):
        for rec in self:
            rec.x_current_amount = True if rec.x_crm_lead_id.stage_id.x_amount_type == rec.x_amount_type else False
            planned_revenue = 0
            for line in rec.x_crm_lead_id.x_sale_order_amount_ids:
                if line.x_amount_type == rec.x_crm_lead_id.stage_id.x_amount_type:
                    planned_revenue += line.x_amount
            rec.x_crm_lead_id.planned_revenue = planned_revenue

    @api.depends('x_amount_type', 'x_amount', 'x_payment_count')
    def _compute_display_name(self):
        for rec in self:
            amount_type = dict(rec._fields['x_amount_type'].selection).get(rec.x_amount_type)
            if rec.x_amount_type == 'currency_loss':
                rec.display_name = '%s ($%s) - [%s]' % (rec.x_name, rec.x_amount, rec.x_payment_count)
            elif rec.x_payment_count > 0:
                rec.display_name = '%s ($%s) - [%s]' % (amount_type, rec.x_amount, rec.x_payment_count)
            else:
                rec.display_name = '%s ($%s)' % (amount_type, rec.x_amount)
