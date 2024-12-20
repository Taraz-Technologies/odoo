from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrContractSalary(models.Model):
    _name = "hr.contract.salary"
    _description = "HR Contract Salary"
    _order = "x_effective_date desc"

    x_contract_id = fields.Many2one(comodel_name='hr.contract', string='Contract', required=False)
    x_job_id = fields.Many2one(comodel_name='hr.job', string='Job', required=False)

    x_effective_date = fields.Date(string='Effective from', required=True)
    x_working_hours_company = fields.Float(string='W.H. Company', default=8)
    x_working_hours_employee = fields.Float(string='W.H. Employee', default=8)

    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True)
    x_target = fields.Float(string='Target', required=False)
    x_factor = fields.Float(string='Factor', required=False)
    x_wage = fields.Float(string='Wage', required=False)
    x_note = fields.Char(string='Note', required=False)

    # x_trans_allowance = fields.Float(string='Transport Allowance', required=False)
    # x_rnd_allowance = fields.Float(string='R&D Allowance', required=False)
    # x_total_salary = fields.Float(string='Gross', required=False)

    @api.onchange('x_target', 'x_factor')
    def calculate_salary(self):
        for rec in self:
            rec.x_wage = rec.x_target * rec.x_factor


class SalaryDetails(models.Model):
    _name = "salary.details"
    _description = "Salary Details"
    _rec_name = "x_name"

    x_slip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', required=False)
    x_name = fields.Char(string='Name', required=False)
    x_category = fields.Char(string='Category', required=False)

    currency_id = fields.Many2one(related="x_slip_id.currency_id")
    x_amount = fields.Float(string='Amount', required=False)
    x_currency_id = fields.Many2one(related='x_slip_id.x_currency_id')
    x_amount_currency = fields.Float(string='Amount Currency', compute="compute_amount_currency", store=True)

    @api.depends('x_amount', 'x_slip_id.x_rate')
    def compute_amount_currency(self):
        for rec in self:
            rec.x_amount_currency = round(rec.x_amount * rec.x_slip_id.x_rate, 0)




