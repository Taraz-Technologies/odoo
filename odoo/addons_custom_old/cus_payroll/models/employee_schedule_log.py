from odoo import api, fields, models, tools, _


class EmployeeScheduleLog(models.Model):
    _name = 'employee.schedule.log'
    _description = 'Employee Schedule Log'
    _rec_name = 'x_employee_id'

    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=False)
    x_start_date = fields.Date(string='Start Date', required=False)
    x_resource_calendar_id = fields.Many2one(comodel_name='resource.calendar', string='Working Hours')