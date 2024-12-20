from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    @api.model
    def allocate_time_off_paid(self):
        employees = self.env['hr.employee'].search([('active', '=', True), ('x_leave_allocation', '=', True)])
        for employee in employees:
            vals = {
                'name': 'Paid Time Off',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'holiday_status_id': self.env.ref('hr_holidays.holiday_status_cl').id,
                'allocation_type': 'regular',
                'number_of_days': 1.50,
                'state': 'validate',
            }
            self.create(vals)
            self.action_approve()
            self.action_validate()

    @api.model
    def allocate_time_off_sick(self):
        employees = self.env['hr.employee'].search([('active', '=', True), ('x_leave_allocation', '=', True)])
        for employee in employees:
            vals = {
                'name': 'Sick Time Off',
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'holiday_status_id': self.env.ref('hr_holidays.holiday_status_sl').id,
                'allocation_type': 'regular',
                'number_of_days': 6,
                'state': 'validate',
            }
            self.create(vals)
            self.action_approve()
            self.action_validate()