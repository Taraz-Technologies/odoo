from odoo import fields, models, api

from datetime import date
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    x_job_title_id = fields.Many2one(comodel_name='hr.job.title', string='Job Title', required=False)
    x_job_level_id = fields.Many2one(comodel_name='hr.job.level', string='Job Level', required=False)

    x_leave_allocation = fields.Boolean(string="Leave Allocation", )

    x_resource_calendar_id = fields.Many2one(
        comodel_name='resource.calendar', string='Last Working Hours', compute="_compute_schedule", store=True
    )
    x_employee_schedule_log = fields.One2many(
        'employee.schedule.log', 'x_employee_id', 'Employee Schedule Log',
        compute="_compute_schedule", store=True
    )


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    @api.depends('resource_calendar_id')
    def _compute_schedule(self):
        for rec in self:
            if rec.resource_calendar_id:
                vals = {
                    'x_start_date': date.today(),
                    'x_resource_calendar_id': rec.resource_calendar_id.id,
                }
                rec.x_employee_schedule_log = [(0, 0, vals)]
            else:
                rec.x_employee_schedule_log = False
            rec.x_resource_calendar_id = rec.resource_calendar_id.id

    @api.onchange('x_job_title_id', 'job_id')
    def update_job_position(self):
        for rec in self:
            rec.job_title = '%s (%s)' % (rec.x_job_title_id.x_name, rec.job_id.name)


class HrJobTitle(models.Model):
    _name = "hr.job.title"
    _description = 'Job Title'
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)


class HrJobLevel(models.Model):
    _name = "hr.job.level"
    _description = 'Job Level'
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)









