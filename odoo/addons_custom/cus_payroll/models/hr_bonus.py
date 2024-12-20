from odoo import api, fields, models, _
from odoo.exceptions import UserError

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrBonus(models.Model):
    _name = "hr.bonus"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Bonus"
    _rec_name = "x_employee_id"
    _order = 'x_employee_id'

    x_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'), ('paid', 'Paid'), ('cancel', 'Cancelled'),
    ], string='Status', default='not_paid', compute="compute_state", store=True, tracking=True)

    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=False, tracking=True)
    x_amount = fields.Float(string='Amount', required=False, tracking=True)
    x_due_date = fields.Date(string='Due Date', required=False, tracking=True,
                             default=lambda self: fields.Date.to_string(
                                 (datetime.now() + relativedelta(months=0, day=1, days=-1)).date()
                             ))
    x_note = fields.Char(string='Note', required=False, tracking=True)

    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', required=False, tracking=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=165, tracking=True)

    x_batch_id = fields.Many2one(comodel_name='hr.bonus.batch', string='Batch', required=False)
    x_percentage = fields.Float(string='Percentage', required=False)
    x_salary = fields.Float(string='Salary', compute="_compute_salary", store=True)
    x_hours = fields.Float(string='Hours')

    @api.depends('x_employee_id')
    def _compute_salary(self):
        for rec in self:
            contract_id = rec.x_employee_id.contract_id
            rec.x_salary = contract_id.wage + contract_id.x_skill_increment

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
                raise UserError(_("You can not delete a bonus once it is paid."))
        return super(HrBonus, self).unlink()


class HrBonusBatch(models.Model):
    _name = "hr.bonus.batch"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bonus Batch"
    _rec_name = "x_name"
    _order = "x_payment_date desc"

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    x_name = fields.Char(string='Name', required=True, tracking=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency',
                                    default=lambda self: self.env.company.currency_id, required=True, tracking=True)
    x_amount = fields.Float(string='Amount', required=False, tracking=True)
    x_note = fields.Char(string='Note', required=False, tracking=True)
    x_payment_date = fields.Date(string='Due Date', required=True, tracking=True,
                                 default=lambda self: fields.Date.to_string(
                                     (datetime.now() + relativedelta(months=0, day=1, days=-1)).date()
                                 ))

    x_split = fields.Selection(selection=[
        ('manual', 'Manual'),
        ('equal', 'Equally'),
        ('percentage', 'By Percentage'),
        ('salary', 'By Salary'),
        ('hours', 'By Working Hours'),
    ], required=True, string='Split', default='equal', tracking=True)
    x_working_hours = fields.Float(string='Working Hours', compute="_compute_hours", store=True, readonly=False)

    @api.depends('x_date_from', 'x_date_to')
    def _compute_hours(self):
        for rec in self:
            if rec.x_date_from and rec.x_date_to:
                # Get days between two dates while skipping Sunday and first Saturday of the month
                days = (rec.x_date_to - rec.x_date_from).days
                sundays = sum(1 for i in range(days) if (rec.x_date_from + relativedelta(days=i)).weekday() == 6)
                rec.x_working_hours = (days - sundays) * 8
            else:
                rec.x_working_hours = 0

    x_date_from = fields.Date(string='Date from', required=False, tracking=True,
                              default=lambda self: fields.Date.to_string(
                                  (datetime.now() + relativedelta(months=-1, day=1, days=0)).date()
                              ), )
    x_date_to = fields.Date(string='Date to', required=False, tracking=True,
                            default=lambda self: fields.Date.to_string(
                                (datetime.now() + relativedelta(months=0, day=1, days=-1)).date()
                            ), )

    x_bonus_ids = fields.One2many(comodel_name='hr.bonus', inverse_name='x_batch_id', string='Bonuses')

    x_date = fields.Date(string='Payment Date', readonly=False, required=True,
                         default=lambda self: fields.Date.to_string(date.today()), tracking=True, )

    x_letter_head_report = fields.Boolean(string='Letter Head Report?', required=False)

    x_bank_id = fields.Many2one(comodel_name='res.bank', string='Bank', default=2)
    x_cheque_number = fields.Char(string='Cheque #', required=False)
    x_amount_in_words = fields.Char(string='Amount in Words', required=False)

    x_company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                   default=lambda self: self.env.company, tracking=True)

    @api.onchange('x_split', 'x_bonus_ids', 'x_bonus_ids.x_hours')
    def onchange_split_method(self):
        if self.x_split == 'hours':
            self.x_amount = sum(self.x_bonus_ids.mapped('x_amount'))


    @api.model
    def default_get(self, fields_list):
        res = super(HrBonusBatch, self).default_get(fields_list)
        employee_ids = self.env['hr.employee'].search([
            ('contract_warning', '=', False), ('contract_id.x_bonus', '=', True),
        ])

        bonus_ids = []
        for employee in employee_ids:
            salary = employee.contract_id.wage + employee.contract_id.x_skill_increment
            bonus_ids.append((0, 0, {
                'x_employee_id': employee.id,
                'x_due_date': res.get('x_payment_date'),
                'x_salary': salary,
            }))
        res['x_bonus_ids'] = bonus_ids
        return res

    @api.onchange('x_currency_id')
    def onchange_currency_id(self):
        for rec in self:
            rec.x_bonus_ids.write({'x_currency_id': rec.x_currency_id.id})

    @api.onchange('x_payment_date')
    def onchange_payment_date(self):
        for rec in self:
            rec.x_bonus_ids.write({'x_due_date': rec.x_payment_date})

    @api.onchange('x_note')
    def onchange_note(self):
        for rec in self:
            rec.x_bonus_ids.write({'x_note': rec.x_note})

    @api.onchange('x_amount', 'x_split', 'x_working_hours', 'x_bonus_ids', 'x_bonus_ids.x_hours')
    def compute_bonuses(self):
        for rec in self:
            amount = rec.x_amount
            for line in rec.x_bonus_ids:
                if rec.x_split == 'equal':
                    total = len(rec.x_bonus_ids)
                    line.x_amount = round(amount / total, 2) if total != 0 else 0
                elif rec.x_split == 'percentage':
                    line.x_amount = round(amount * line.x_percentage / 100, 2)
                elif rec.x_split == 'salary':
                    total = sum(rec.x_bonus_ids.mapped('x_salary'))
                    line.x_amount = round(amount * line.x_salary / total, 2) if total != 0 else 0
                elif rec.x_split == 'hours':
                    line.x_amount = round(
                        line.x_salary * 1.5 * line.x_hours / rec.x_working_hours, 2
                    ) if rec.x_working_hours != 0 else 0

    def action_batch_draft(self):
        return self.write({'state': 'draft'})

    def action_batch_cancel(self):
        return self.write({'state': 'cancel'})

    def action_batch_done(self):
        return self.write({'state': 'done'})

    def unlink(self):
        self.x_bonus_ids.unlink()
        return super(HrBonusBatch, self).unlink()
