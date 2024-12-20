from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrBenefits(models.Model):
    _name = "hr.benefits"
    _description = "Employee Benefits"
    _rec_name = "x_payslip_id"

    x_payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip', required=False)

    x_employee_id = fields.Many2one(related="x_payslip_id.employee_id", store=True)
    x_currency_id = fields.Many2one(related="x_payslip_id.x_currency_id")

    x_type = fields.Selection(selection=[
        ('sal', 'Salary'),
        ('sinc', 'Skill Increments'),
        ('alw', 'Allowance'),
        ('inc', 'Other Increments'),
        ('bon', 'Bonus'),
        ('lon', 'Loan')
    ], string='Type', required=False, )

    x_amount = fields.Float(string='Amount', compute="compute_benefits", store=True)

    @api.depends('x_payslip_id.line_ids')
    def compute_benefits(self):
        for rec in self:
            if rec.x_type == 'sal':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Basic'
                ).mapped('x_amount_currency'))
            elif rec.x_type == 'sinc':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Skill Increments'
                ).mapped('x_amount_currency'))
            elif rec.x_type == 'alw':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Allowance'
                ).mapped('x_amount_currency'))
            elif rec.x_type == 'inc':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Increments'
                ).mapped('x_amount_currency'))
            elif rec.x_type == 'bon':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Bonus'
                ).mapped('x_amount_currency'))
            elif rec.x_type == 'lon':
                rec.x_amount = sum(rec.x_payslip_id.line_ids.filtered(
                    lambda l: l.category_id.name == 'Loan'
                ).mapped('x_amount_currency'))




