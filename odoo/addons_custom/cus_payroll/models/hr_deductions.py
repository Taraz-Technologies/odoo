from odoo import api, fields, models, _
import logging

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger("*__addons_custom__*")


class HrDeductions(models.Model):
    _name = 'hr.deductions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Deductions'
    _rec_name = "x_date"
    _order = "x_date desc"

    x_date = fields.Date(string='Due Date', required=True, tracking=True,
                         default=lambda self: fields.Date.to_string(
                             (datetime.now() + relativedelta(months=0, day=1, days=-1)).date()
                         ), )
    x_date_from = fields.Date(string='Date from', required=True, tracking=True,
                              default=lambda self: fields.Date.to_string(
                                  (datetime.now() + relativedelta(months=-1, day=1, days=0)).date()
                              ), )
    x_date_to = fields.Date(string='Date to', required=True, tracking=True,
                            default=lambda self: fields.Date.to_string(
                                (datetime.now() + relativedelta(months=0, day=1, days=-1)).date()
                            ), )

    x_split = fields.Selection(selection=[
        ('manual', 'Manual'),
        ('equal', 'Equally'),
        ('percentage', 'By Percentage'),
        ('share', 'By Share'),
        ('salary', 'By Salary'),
    ], required=True, string='Split', default='equal', tracking=True)

    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True,
                                    default=lambda self: self.env.company.currency_id)
    x_amount = fields.Float(string='Deduction Amount', compute="compute_amount", store=True)

    x_note = fields.Text(
        string='Note', required=False, tracking=True,
        default="Residence Bills to be attached"
                "\n1) Rent Bill"
                "\n2) WHT Rent Bill"
                "\n3) Electricity Bill"
                "\n4) Maintenance Bill"
                "\n5) Gas Bill"
    )

    x_bill_ids = fields.Many2many(comodel_name='account.move', string='Bills', domain=[('type', '=', 'in_invoice')])

    x_deduction_ids = fields.One2many(
        comodel_name='hr.allowances.details', inverse_name='x_deduction_id', string='Deductions', readonly=False,
    )

    x_compute_deductions = fields.Boolean(compute="_compute_deductions")

    @api.model
    def default_get(self, fields_list):
        res = super(HrDeductions, self).default_get(fields_list)
        employee_ids = self.env['hr.employee'].search([
            ('contract_warning', '=', False), ('contract_id.x_deductions', '=', True),
        ])
        deduction_ids = []
        for employee in employee_ids:
            deduction_ids.append((0, 0, {'x_employee_id': employee.id}))
        res['x_deduction_ids'] = deduction_ids
        return res

    @api.onchange('x_date_from', 'x_date_to')
    def get_bills_data(self):
        for rec in self:
            if rec.x_date_from and rec.x_date_to:
                rec.x_bill_ids = self.env['account.move'].search([
                    ('type', '=', 'in_invoice'), ('x_item_type', '=', 'Residence'), ('state', '=', 'posted'),
                    ('invoice_date', '<=', rec.x_date_to), ('invoice_date', '>=', rec.x_date_from),
                ]).ids

    @api.depends('x_bill_ids', 'x_currency_id')
    def compute_amount(self):
        for rec in self:
            amount = 0
            for bill in rec.x_bill_ids:
                amount += bill.currency_id.round(
                    bill.amount_total * bill.currency_id._get_conversion_rate(
                        bill.currency_id, rec.x_currency_id, bill.company_id, bill.invoice_date
                    )
                )
            rec.x_amount = amount

    @api.depends('x_split', 'x_amount', 'x_deduction_ids.x_share')
    def _compute_deductions(self):
        for rec in self:
            if rec.x_split == 'equal':
                total_employees = len(rec.x_deduction_ids)
                for line in rec.x_deduction_ids:
                    line.x_deduction_amount = round(rec.x_amount * 1 / total_employees, 0) if total_employees != 0 else 0
            elif rec.x_split == 'percentage':
                for line in rec.x_deduction_ids:
                    line.x_deduction_amount = rec.x_amount * line.x_percentage
            elif rec.x_split == 'salary':
                total_salary = sum(rec.x_deduction_ids.mapped('x_gross_salary'))
                for line in rec.x_deduction_ids:
                    line.x_deduction_amount = round(rec.x_amount * line.x_gross_salary / total_salary, 0) if total_salary != 0 else 0
            elif rec.x_split == 'share':
                total_share = sum(rec.x_deduction_ids.mapped('x_share'))
                for line in rec.x_deduction_ids:
                    line.x_deduction_amount = round(rec.x_amount * line.x_share / total_share, 0) if total_share != 0 else 0
            rec.x_compute_deductions = True

    def unlink(self):
        self.x_deduction_ids.unlink()
        return super(HrDeductions, self).unlink()


class HrAllowancesDetails(models.Model):
    _name = 'hr.allowances.details'
    _description = 'Allowances Details'
    _rec_name = "x_employee_id"

    x_deduction_id = fields.Many2one(comodel_name='hr.deductions', string='Deduction', required=False)
    x_date = fields.Date(related="x_deduction_id.x_date")
    x_split = fields.Selection(related="x_deduction_id.x_split")
    x_bill_ids = fields.Many2many(related="x_deduction_id.x_bill_ids")
    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True)
    x_currency_id = fields.Many2one(related="x_deduction_id.x_currency_id")
    x_gross_salary = fields.Float(string='Gross Salary', compute="compute_gross_salary", store=True)
    x_percentage = fields.Float(string='Percentage', required=False)
    x_share = fields.Float(string='Share', required=False)
    x_deduction_amount = fields.Float(string='Deduction Amount', required=False)

    @api.depends('x_employee_id')
    def compute_gross_salary(self):
        for rec in self:
            rec.x_gross_salary = rec.x_employee_id.contract_id.wage + rec.x_employee_id.contract_id.x_allowances

    @api.onchange('x_percentage')
    def onchange_percentage(self):
        for rec in self:
            rec.x_deduction_amount = rec.x_deduction_id.x_amount * rec.x_percentage
