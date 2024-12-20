from odoo import api, fields, models, _
from odoo.exceptions import UserError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrFines(models.Model):
    _name = "hr.fines"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Fines"
    _rec_name = "x_employee_id"

    x_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'), ('paid', 'Paid'), ('cancel', 'Cancelled'),
    ], string='Status', default='not_paid', compute="compute_state", store=True, tracking=True)

    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=False, tracking=True)
    x_amount = fields.Float(string='Amount', required=False, tracking=True)
    x_due_date = fields.Date(string='Due Date', required=False, tracking=True)
    x_note = fields.Char(string='Note', required=False, tracking=True)

    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', required=False, tracking=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=165, tracking=True)

    x_batch_id = fields.Many2one(comodel_name='hr.fines.batch', string='Batch', required=False)
    x_percentage = fields.Float(string='Percentage', required=False)
    x_salary = fields.Float(string='Salary', compute="_compute_salary", store=True)
    x_hours = fields.Float(string='Hours', compute="_compute_hours", store=True)

    @api.depends('x_employee_id')
    def _compute_salary(self):
        for rec in self:
            contract_id = rec.x_employee_id.contract_id
            rec.x_salary = contract_id.x_gross

    @api.depends('x_batch_id.x_date_from', 'x_batch_id.x_date_to')
    def _compute_hours(self):
        for rec in self:
            if not rec.x_batch_id.x_date_from or not rec.x_batch_id.x_date_to:
                continue
            date_from = datetime.combine(rec.x_batch_id.x_date_from, datetime.min.time())
            date_to = datetime.combine(rec.x_batch_id.x_date_to, datetime.max.time())
            attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.x_employee_id.id), ('check_in', '>=', date_from), ('check_in', '<=', date_to)])
            rec.x_hours = sum(attendance_ids.mapped('worked_hours'))

    @api.depends('x_payslip_id')
    def compute_state(self):
        for rec in self:
            if not rec.x_payslip_id:
                rec.x_state = 'not_paid'

    @api.onchange('x_percentage')
    def update_amount(self):
        for rec in self:
            rec.x_amount = round(rec.x_batch_id.x_amount * rec.x_percentage / 100, 2)

    def unlink(self):
        for rec in self:
            if rec.x_state == 'paid':
                raise UserError(_("You can not delete a fine once it is paid."))
        return super(HrFines, self).unlink()


class HrFinesBatch(models.Model):
    _name = "hr.fines.batch"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fines Batch"
    _rec_name = "x_name"

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    x_name = fields.Char(string='Name', required=True, tracking=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=165, tracking=True)
    x_amount = fields.Float(string='Amount', required=True, tracking=True)
    x_note = fields.Char(string='Note', required=False, tracking=True)
    x_payment_date = fields.Date(string='Payment Date', required=True, tracking=True,
                                 default=lambda self: fields.Date.to_string(date.today()))

    x_split = fields.Selection(selection=[
        ('equal', 'Equally'),
        ('percentage', 'By Percentage'),
        ('salary', 'By Salary'),
        ('hours', 'By Working Hours'),
    ], required=True, string='Split', default='equal', tracking=True)
    x_date_from = fields.Date(string='Date from', required=False, tracking=True,
                              default=lambda self: fields.Date.to_string(date.today().replace(day=1)),)
    x_date_to = fields.Date(string='Date to', required=False, tracking=True,
                            default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),)

    x_fines_ids = fields.One2many(comodel_name='hr.fines', inverse_name='x_batch_id', string='Fines')

    x_default_values = fields.Boolean(string='Default Values', required=False)

    @api.onchange('x_default_values')
    def get_default(self):
        for rec in self:
            employee_ids = self.env['hr.employee'].search([('contract_warning', '=', False)])
            for employee in employee_ids:
                rec.x_fines_ids = [(0, 0, {'x_employee_id': employee.id, 'x_due_date': rec.x_payment_date})]

    @api.onchange('x_payment_date')
    def onchange_payment_date(self):
        for rec in self:
            for line in rec.x_fines_ids:
                line.x_due_date = rec.x_payment_date

    @api.onchange('x_note')
    def onchange_note(self):
        for rec in self:
            for line in rec.x_fines_ids:
                line.x_note = rec.x_note

    @api.onchange('x_amount', 'x_split', 'x_fines_ids')
    def compute_bonuses(self):
        for rec in self:
            amount = rec.x_amount
            for line in rec.x_fines_ids:
                if rec.x_split == 'equal':
                    total = len(rec.x_fines_ids)
                    line.x_amount = round(amount / total, 2) if total != 0 else 0
                elif rec.x_split == 'percentage':
                    line.x_amount = round(amount * line.x_percentage / 100, 2)
                elif rec.x_split == 'salary':
                    total = sum(rec.x_fines_ids.mapped('x_salary'))
                    line.x_amount = round(amount * line.x_salary / total, 2) if total != 0 else 0
                elif rec.x_split == 'hours':
                    total = sum(rec.x_fines_ids.mapped('x_hours'))
                    line.x_amount = round(amount * line.x_hours / total, 2) if total != 0 else 0

    def action_batch_draft(self):
        return self.write({'state': 'draft'})

    def action_batch_cancel(self):
        return self.write({'state': 'cancel'})

    def action_batch_done(self):
        return self.write({'state': 'done'})

    def unlink(self):
        self.x_fines_ids.unlink()
        return super(HrFinesBatch, self).unlink()


class HrPayslipFines(models.Model):
    _name = "hr.payslip.fines"
    _description = "Payslip Fines"

    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', required=False, tracking=True)
    x_name = fields.Char(string='Description', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', related="x_payslip_id.journal_id.currency_id")
    x_amount = fields.Float(string='Fine Amount', required=False)







