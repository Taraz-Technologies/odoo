from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
from datetime import date

_logger = logging.getLogger("*__addons_custom__*")


class HrContract(models.Model):
    _inherit = 'hr.contract'

    x_loan_structure = fields.Many2one('hr.payroll.structure', string='Loan Structure')
    x_bonus_structure = fields.Many2one('hr.payroll.structure', string='Bonus Structure')

    x_prohibition_date = fields.Date(string='Probation Date', required=True)

    x_skill_increment = fields.Monetary(string='Skill Increments', compute="compute_salary", store=True, tracking=True)
    x_allowances = fields.Monetary(string='Allowances', compute="compute_salary", store=True, tracking=True)
    x_increments = fields.Monetary(string='Other Increments', compute="compute_salary", store=True, tracking=True)

    x_gross = fields.Monetary(string='Gross', compute="compute_salary", store=True, tracking=True)

    x_deductions = fields.Boolean(string='Deductions', required=False, tracking=True)
    x_bonus = fields.Boolean(string='Bonus', required=False, tracking=True)

    x_salary_detail_ids = fields.One2many(comodel_name='hr.contract.salary', inverse_name='x_contract_id', string='Salary Details')

    x_skill_increment_ids = fields.One2many(comodel_name='hr.increments', inverse_name='x_contract_id', string='Skills Details')

    x_allowance_ids = fields.Many2many(comodel_name='hr.allowances', relation="hr_contract_hr_allowances_rel",
                                       column1="hr_contract_id", column2="hr_allowances_id", string='Allowances')
    x_increment_ids = fields.Many2many(comodel_name='hr.increments', relation="hr_contract_hr_increments_rel",
                                       column1="hr_contract_id", column2="hr_increments_id", string='Increments')

    x_custom_tag_ids = fields.Many2many('custom.tags', string='Tags')

    def write(self, vals):
        old_values = self.x_custom_tag_ids.ids
        res = super(HrContract, self).write(vals)
        new_values = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_values, new_values=new_values
            )
        return res

    @api.onchange('job_id')
    def onchange_job_id(self):
        for rec in self:
            rec.wage = rec.job_id.x_wage
            salary_detail_ids = rec.job_id.x_salary_detail_ids.filtered(
                lambda s: s.id == max(rec.job_id.x_salary_detail_ids.ids)
            )
            for line in salary_detail_ids:
                line.copy({
                    'x_effective_date': date.today(),
                    'x_job_id': False,
                    'x_contract_id': rec._origin.id,
                })
            rec.x_gross = rec.wage + rec.x_skill_increment + rec.x_allowances + rec.x_increments

    @api.depends(
        'x_skill_increment_ids.x_status',
        'x_skill_increment_ids.x_amount',
        'x_allowance_ids.x_amount',
        'x_increment_ids.x_amount',
    )
    def compute_salary(self):
        for rec in self:
            rec.x_skill_increment = sum(rec.x_skill_increment_ids.filtered(lambda l: l.x_status == 'pass').mapped('x_amount'))
            rec.x_allowances = sum(rec.x_allowance_ids.mapped('x_amount'))
            rec.x_increments = sum(rec.x_increment_ids.mapped('x_amount'))
            rec.x_gross = rec.wage + rec.x_skill_increment + rec.x_allowances + rec.x_increments

    def get_job_skill_increment(self):
        for rec in self:
            rec.x_skill_increment_ids = [(2, skill.id) for skill in rec.x_skill_increment_ids]
            for skill_increment in rec.job_id.x_skill_increment_ids:
                skill_increment_id = skill_increment.copy({'x_job_id': False, 'x_contract_id': rec.id})
                for skill in skill_increment.x_skill_ids:
                    skill.copy({'x_increment_id': skill_increment_id.id})
