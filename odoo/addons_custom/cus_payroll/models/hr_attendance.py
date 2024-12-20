from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError

from datetime import date, datetime, time, timedelta, timezone
import pytz
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    x_type = fields.Selection(selection=[
        ('full_day', 'Full Day'), ('morning', 'Half Day (Morning)'), ('evening', 'Half Day (Evening)'),
        ('night_shift', 'Night Shift'), ('compensation', 'Compensation'),
    ], required=True, string='Type', default="full_day")

    x_break_from_1 = fields.Float(string='Break from 1', required=False)
    x_break_from_2 = fields.Float(string='Break from 2', required=False)
    x_break_from_3 = fields.Float(string='Break from 3', required=False)
    x_break_from_4 = fields.Float(string='Break from 4', required=False)
    x_break_from_5 = fields.Float(string='Break from 5', required=False)

    x_break_to_1 = fields.Float(string='Break to 1', required=False)
    x_break_to_2 = fields.Float(string='Break to 2', required=False)
    x_break_to_3 = fields.Float(string='Break to 3', required=False)
    x_break_to_4 = fields.Float(string='Break to 4', required=False)
    x_break_to_5 = fields.Float(string='Break to 5', required=False)

    x_work_from = fields.Float(string='Work from', compute="get_times", store=True, readonly=False)
    x_work_to = fields.Float(string='Work to', compute="get_times", store=True, readonly=False)
    x_break_from = fields.Float(string='Break from', compute="get_times", store=True, readonly=False)
    x_break_to = fields.Float(string='Break to', compute="get_times", store=True, readonly=False)
    x_working_hours = fields.Float(string='Work Hours (Taraz)', compute="_compute_worked_hours", store=True)
    x_balance = fields.Float(string='Balance', compute="_compute_worked_hours", store=True)

    x_apply_late_coming_fine = fields.Boolean(string='Apply (Late)', default=True)
    x_apply_early_going_fine = fields.Boolean(string='Apply (Early)', default=True)

    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=2)
    x_late_coming_fine = fields.Float(string='Fine (Late Coming)', compute="_compute_worked_hours", store=True)
    x_early_going_fine = fields.Float(string='Fine (Early Going)', compute="_compute_worked_hours", store=True)

    @api.depends('employee_id', 'x_type')
    def get_times(self):
        for rec in self:
            if rec.x_type in ['compensation']:
                rec.x_work_from = 0
                rec.x_work_to = 0
                rec.x_break_from = 0
                rec.x_break_to = 0
                rec.x_balance = rec.worked_hours
                continue

            day_of_week = rec.check_in.strftime('%A')

            resource_calendar_id = rec.employee_id.resource_calendar_id
            attendance_ids = resource_calendar_id.attendance_ids.filtered(lambda l: day_of_week in l.name)

            morning_shift = attendance_ids.filtered(lambda l: l.day_period == 'morning')
            evening_shift = attendance_ids.filtered(lambda l: l.day_period == 'afternoon')

            rec.x_work_from = morning_shift.hour_from if rec.x_type not in ['evening'] else evening_shift.hour_from
            rec.x_work_to = evening_shift.hour_to if evening_shift and rec.x_type not in [
                'morning'
            ] else morning_shift.hour_to

            add_break = True if morning_shift.hour_to != evening_shift.hour_from else False

            break_from = 0
            break_to = 0
            if add_break and evening_shift and rec.x_type not in ['evening', 'morning']:
                break_from = morning_shift.hour_to
                break_to = evening_shift.hour_from

            rec.x_break_from = break_from
            rec.x_break_to = break_to

    @api.depends(
        'check_in', 'check_out', 'x_type', 'x_currency_id', 'x_work_from', 'x_work_to',
        'x_break_from', 'x_break_from_1', 'x_break_from_2', 'x_break_from_3', 'x_break_from_4', 'x_break_from_5',
        'x_break_to', 'x_break_to_1', 'x_break_to_2', 'x_break_to_3', 'x_break_to_4', 'x_break_to_5',
        'x_apply_late_coming_fine', 'x_apply_early_going_fine',
    )
    def _compute_worked_hours(self):
        super(HrAttendance, self)._compute_worked_hours()
        for rec in self:
            if rec.check_out:
                break_0 = rec.x_break_to - rec.x_break_from if rec.x_break_to > rec.x_break_from else 0
                break_1 = rec.x_break_to_1 - rec.x_break_from_1 if rec.x_break_to_1 > rec.x_break_from_1 else 0
                break_2 = rec.x_break_to_2 - rec.x_break_from_2 if rec.x_break_to_2 > rec.x_break_from_2 else 0
                break_3 = rec.x_break_to_3 - rec.x_break_from_3 if rec.x_break_to_3 > rec.x_break_from_3 else 0
                break_4 = rec.x_break_to_4 - rec.x_break_from_4 if rec.x_break_to_4 > rec.x_break_from_4 else 0
                break_5 = rec.x_break_to_5 - rec.x_break_from_5 if rec.x_break_to_5 > rec.x_break_from_5 else 0
                rec.worked_hours -= break_0 + break_1 + break_2 + break_3 + break_4 + break_5

            rec.x_working_hours = rec.x_work_to - rec.x_work_from - rec.x_break_to + rec.x_break_from
            rec.x_balance = rec.worked_hours - rec.x_working_hours

            rec.x_late_coming_fine = 0
            rec.x_early_going_fine = 0

            if rec.x_type in ['compensation']:
                continue

            employee_salary = rec.employee_id.contract_id.x_gross
            fine_amount = 0

            resource_calendar_id = rec.employee_id.resource_calendar_id
            apply_fine = resource_calendar_id.x_late_coming_fine
            if resource_calendar_id.x_fine_by == 'amount':
                fine_amount = resource_calendar_id.x_late_coming_fine_amount if apply_fine else 0
            elif resource_calendar_id.x_fine_by == 'percentage':
                fine_amount = employee_salary * resource_calendar_id.x_late_coming_fine_percentage if apply_fine else 0
            check_in_threshold = timedelta(hours=rec.x_work_from + resource_calendar_id.x_minutes / 60)

            odoo_timezone = pytz.timezone('UTC')
            employee_timezone = pytz.timezone(rec.employee_id.tz)
            check_in_localize = odoo_timezone.localize(rec.check_in)
            check_in = check_in_localize.astimezone(employee_timezone)
            check_in_hours = int(check_in.strftime('%H'))
            check_in_minutes = int(check_in.strftime('%M'))
            check_in_time = timedelta(hours=check_in_hours, minutes=check_in_minutes)

            rec.x_late_coming_fine = fine_amount if check_in_threshold < check_in_time and rec.x_apply_late_coming_fine else 0

            if rec.check_out:
                apply_fine = resource_calendar_id.x_early_going_fine
                if resource_calendar_id.x_fine_by == 'amount':
                    fine_amount = resource_calendar_id.x_early_going_fine_amount if apply_fine else 0
                elif resource_calendar_id.x_fine_by == 'percentage':
                    fine_amount = employee_salary * resource_calendar_id.x_early_going_fine_percentage if apply_fine else 0
                rec.x_early_going_fine = fine_amount if rec.worked_hours < rec.x_working_hours and rec.x_apply_early_going_fine else 0
