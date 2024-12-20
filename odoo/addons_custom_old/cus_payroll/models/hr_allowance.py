from odoo import api, fields, models, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrAllowances(models.Model):
    _name = 'hr.allowances'
    _description = 'HR Allowances'
    _rec_name = "display_name"
    _order = "x_date desc"

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)

    x_date = fields.Date(string='Effective from', required=True)
    x_name = fields.Char(string="Name", required=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True)
    x_target = fields.Float(string='Target', required=False)
    x_factor = fields.Float(string='Factor', required=False)
    x_amount = fields.Float(string='Amount', required=False)
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    @api.depends('x_name', 'x_currency_id', 'x_amount')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s - %s %s' % (rec.x_name, rec.x_currency_id.symbol, rec.x_amount)

    @api.onchange('x_target', 'x_factor')
    def calculate_allowances_amount(self):
        for rec in self:
            rec.x_amount = rec.x_target * rec.x_factor


class HrIncrements(models.Model):
    _name = 'hr.increments'
    _description = 'HR Increments'
    _rec_name = "x_name"
    _order = "x_name"

    x_job_id = fields.Many2one(comodel_name='hr.job', string='Job Position', required=False)
    x_contract_id = fields.Many2one(comodel_name='hr.contract', string='Contract', required=False)

    x_name = fields.Char(string="Name", required=True)
    x_description = fields.Text(string="Description", required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True)
    x_target = fields.Float(string='Target', required=False)
    x_factor = fields.Float(string='Factor', required=False)
    x_amount = fields.Float(string='Amount', required=False)
    x_status = fields.Selection(selection=[
        ('pass', 'Pass'), ('pending', 'Pending')
    ], string='Status', default='pending', required=True)
    x_passed_on = fields.Date(string='Passed on', required=False)

    x_skill_ids = fields.One2many(comodel_name='hr.increments.skill', inverse_name='x_increment_id', string='Skills')

    # @api.onchange('x_target', 'x_factor')
    # def calculate_increments_amount(self):
    #     for rec in self:
    #         rec.x_amount = rec.x_target * rec.x_factor

    def unlink(self):
        for rec in self:
            rec.x_skill_ids.unlink()
        return super(HrIncrements, self).unlink()


class HrIncrementsSkill(models.Model):
    _name = 'hr.increments.skill'
    _description = "Skill"
    _rec_name = "x_name"
    _order = "x_name"

    x_increment_id = fields.Many2one(comodel_name='hr.increments', string='Increment', required=False)

    x_name = fields.Char(string="Name", required=True)
    x_description = fields.Text(string="Description", required=False)
    x_level = fields.Selection(selection=[
        ('basic', 'Beginner'), ('intermediate', 'Intermediate'), ('expert', 'Expert'), ('super', 'Super')
    ], string='Level', default='basic', required=True)
    x_status = fields.Selection(selection=[
        ('pass', 'Pass'), ('pending', 'Pending')
    ], string='Status', default='pending', required=True)







