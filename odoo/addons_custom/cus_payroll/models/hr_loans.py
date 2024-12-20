from odoo import api, fields, models, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrLoans(models.Model):
    _name = "hr.loans"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Contracts"
    _rec_name = "x_number"
    _order = "x_payment_date desc"

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('in_progress', 'Running'), ('paid', 'Fully Paid'), ('cancel', 'Cancelled'),
    ], string='Status', default='draft', store=True, tracking=True, required=True)

    x_number = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: _('New'))
    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', tracking=True, readonly=True,
                                   states={'draft': [('readonly', False)]})

    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True, tracking=True,
                                    readonly=True, states={'draft': [('readonly', False)]})
    x_payment_date = fields.Date(string='Payment Date', required=True, tracking=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    x_amount_currency = fields.Float(string='Amount Currency', required=True, tracking=True,
                                     readonly=True, states={'draft': [('readonly', False)]})
    x_amount_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', tracking=True, default=165,
                                           readonly=True, states={'draft': [('readonly', False)]})
    x_payroll_rate_id = fields.Many2one(comodel_name='payroll.currency.rate', string='Conversion Rate', required=False,
                                        readonly=True, tracking=True, states={'draft': [('readonly', False)]})
    x_rate = fields.Float(related="x_payroll_rate_id.rate", store=True, tracking=True,
                          readonly=True, states={'draft': [('readonly', False)]})
    x_amount = fields.Float(string='Amount', required=True, tracking=True,
                            readonly=True, states={'draft': [('readonly', False)]})
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', tracking=True, default=2,
                                    readonly=True, states={'draft': [('readonly', False)]})
    x_description = fields.Char(string='Description', required=True, store=True, tracking=True,
                                readonly=True, states={'draft': [('readonly', False)]})
    x_installments = fields.Float(string='Total Installments', required=True, tracking=True,
                                  readonly=True, states={'draft': [('readonly', False)]})
    x_start_date = fields.Date(string='Start Date', required=True, tracking=True,
                               readonly=True, states={'draft': [('readonly', False)]})
    x_interval_number = fields.Float(string='Interval Number', required=True, tracking=True, default=1,
                                     readonly=True, states={'draft': [('readonly', False)]})

    x_interval_type = fields.Selection(selection=[
        ('days', 'Days'),
        ('months', 'Months'),
    ], string='Interval Unit', default='months',
        required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})

    x_amount_due = fields.Float(string='Amount Due', required=True, tracking=True,
                                readonly=True, states={'draft': [('readonly', False)]})
    x_installment_ids = fields.One2many(comodel_name='hr.loans.installments',
                                        inverse_name='x_loan_id', string='Loan Installments')

    @api.onchange('x_payroll_rate_id')
    def onchange_rate_id(self):
        for rec in self:
            rec.x_rate = rec.x_payroll_rate_id.rate

    @api.onchange('x_amount_currency', 'x_rate')
    def onchange_rate(self):
        for rec in self:
            rec.x_amount = rec.x_amount_currency / rec.x_rate if rec.x_rate else 0

    @api.onchange('x_amount')
    def onchange_amount(self):
        for rec in self:
            rec.x_amount_due = rec.x_amount

    @api.model
    def create(self, vals):
        if 'x_number' not in vals or vals['x_number'] == _('New'):
            vals['x_number'] = self.env['ir.sequence'].next_by_code('employee.loan') or _('New')
        return super(HrLoans, self).create(vals)

    def create_installments(self):
        for rec in self:
            if rec.x_installment_ids.filtered(lambda l: l.x_payslip_id):
                raise UserError('Installments are linked to payslips.')

            rec.x_installment_ids.unlink()
            vals = {
                'x_employee_id': rec.x_employee_id.id,
                'x_description': rec.x_description,
            }

            amount = rec.x_amount
            installments = rec.x_installments
            installment_amount = amount / installments
            start_date = rec.x_start_date
            interval = rec.x_interval_number

            for x in range(round(rec.x_installments - 1)):
                vals['x_payment_date'] = start_date
                installment_amount = amount if amount < installment_amount else installment_amount
                vals['x_amount'] = installment_amount
                rec.x_installment_ids = [(0, 0, vals)]

                if rec.x_interval_type in ['days']:
                    start_date += relativedelta(days=interval)
                elif rec.x_interval_type in ['months']:
                    start_date += relativedelta(months=interval)
                if amount > installment_amount:
                    amount -= installment_amount
                else:
                    break

            if amount != 0:
                vals['x_payment_date'] = start_date
                vals['x_amount'] = amount
                rec.x_installment_ids = [(0, 0, vals)]

            rec.state = 'in_progress'
            if rec.x_payslip_id:
                rec.x_payslip_id.employee_id = rec.x_employee_id.id
                rec.x_payslip_id.x_payment_date = rec.x_payment_date
                rec.x_payslip_id.date = rec.x_payment_date
                rec.x_payslip_id.x_loan = rec.x_amount
                rec.x_payslip_id.compute_sheet()

    def create_payslip(self):
        for rec in self:
            if not rec.x_payslip_id:
                vals = {
                    'employee_id': rec.x_employee_id.id,
                    'x_payment_date': rec.x_payment_date,
                    'x_slip_type': 'Loan',
                    'date': rec.x_payment_date,
                    'x_payroll_rate_id': rec.x_payroll_rate_id.id,
                    'x_rate': rec.x_rate,
                    'x_loan': rec.x_amount,
                    'x_loan_contract_id': rec._origin.id,
                }
                payslip_id = self.env['hr.payslip'].create(vals)
                payslip_id.onchange_employee()
                payslip_id.compute_sheet()
                rec.x_payslip_id = payslip_id.id

            return {
                'name': _('Loan Payslip'),
                'view_mode': 'form',
                'view_id': self.env.ref('om_hr_payroll.view_hr_payslip_form').id,
                'res_model': 'hr.payslip',
                'type': 'ir.actions.act_window',
                'res_id': rec.x_payslip_id.id,
            }

    def action_loan_draft(self):
        if self.x_installment_ids.filtered(lambda l: l.x_payslip_id):
            raise UserError('Installments are linked to payslips.')
        self.x_payslip_id.action_payslip_draft()
        self.x_installment_ids.write({'state': 'draft'})
        return self.write({'state': 'draft'})

    def action_loan_cancel(self):
        if self.x_installment_ids.filtered(lambda l: l.x_payslip_id):
            raise UserError('Installments are linked to payslips.')
        self.x_payslip_id.action_payslip_cancel()
        self.x_installment_ids.unlink()
        return self.write({'state': 'cancel'})

    def action_loan_done(self):
        self.x_installment_ids.write({'state': 'in_progress'})
        return self.write({'state': 'in_progress'})

    def action_loan_paid(self):
        return self.write({'state': 'paid'})

    def unlink(self):
        for rec in self:
            if rec.x_payslip_id:
                raise UserError(_("You can not delete a loan which is linked to payslip."))
            elif rec.state != 'draft':
                raise UserError(_("You can not delete a loan which is not in draft."))
        self.x_installment_ids.unlink()
        return super(HrLoans, self).unlink()


class HrLoansInstallments(models.Model):
    _name = "hr.loans.installments"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Installments"
    _rec_name = "x_number"
    _order = "x_payment_date desc"

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('in_progress', 'Running'), ('paid', 'Fully Paid'), ('cancel', 'Cancelled'),
    ], string='Status', default='draft', store=True, tracking=True)

    x_loan_id = fields.Many2one(comodel_name='hr.loans', string='Loan Contract', readonly=True, tracking=True)
    x_currency_id = fields.Many2one(related="x_loan_id.x_currency_id")

    x_number = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: _('New'))
    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', readonly=True, tracking=True,
                                   states={'draft': [('readonly', False)]})

    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', readonly=True, tracking=True)
    x_payment_date = fields.Date(string='Payment Date', tracking=True, readonly=False)
    x_amount = fields.Float(string='Amount', readonly=True, tracking=True)
    x_description = fields.Char(string='Description', readonly=True, tracking=True)
    x_amount_due = fields.Float(string='Amount Due', required=True, related="x_loan_id.x_amount_due")

    @api.model
    def create(self, vals):
        if 'x_number' not in vals or vals['x_number'] == _('New'):
            vals['x_number'] = self.env['ir.sequence'].next_by_code('employee.loan.installments') or _('New')
        return super(HrLoansInstallments, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'paid':
                raise UserError(_("You can not delete an installment which is already paid."))
        return super(HrLoansInstallments, self).unlink()
