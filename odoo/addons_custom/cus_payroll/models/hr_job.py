from odoo import fields, models, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Job(models.Model):
    _inherit = "hr.job"

    x_currency_id = fields.Many2one(related="company_id.currency_id")
    x_wage = fields.Float(string='Wage', compute="compute_salary", store=True)

    x_salary_detail_ids = fields.One2many(comodel_name='hr.contract.salary', inverse_name='x_job_id', string='Salary Details')
    x_skill_increment_ids = fields.One2many(comodel_name='hr.increments', inverse_name='x_job_id', string='Skills Details')

    @api.depends('x_salary_detail_ids')
    def compute_salary(self):
        for rec in self:
            salary_id = rec.x_salary_detail_ids.filtered(
                lambda l: l.x_effective_date == max(rec.x_salary_detail_ids.mapped('x_effective_date'))
            )
            if len(salary_id) > 1:
                raise UserError("Salary with same effective date already exist!")
            else:
                wh_c = salary_id.x_working_hours_company
                wh_e = salary_id.x_working_hours_employee
                hours_factor = wh_e / wh_c if wh_c != 0 else wh_e
                rec.x_wage = salary_id.x_wage * hours_factor
                self.env['hr.contract'].search([('job_id', '=', rec.id)]).onchange_job_id()
