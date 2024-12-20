from odoo import models, fields, api, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    x_duration_expected_days = fields.Char(string='Expected Duration (Days)', compute="_compute_duration_days")
    x_duration_days = fields.Char(string='Duration (Days)', compute="_compute_duration_days")
    x_code = fields.Char(related="workcenter_id.code")

    @api.depends('duration_expected', 'date_start', 'date_finished', 'state')
    def _compute_duration_days(self):
        for rec in self:
            if rec.duration_expected > 480:
                rec.x_duration_expected_days = '%sd' % round(rec.duration_expected / 480, 2)
            elif rec.duration_expected > 60:
                rec.x_duration_expected_days = '%sh' % round(rec.duration_expected / 60, 2)
            else:
                rec.x_duration_expected_days = '%sm' % round(rec.duration_expected, 2)
            duration = '0d'
            if rec.date_start and rec.date_finished:
                interval = rec.workcenter_id.resource_calendar_id.get_work_duration_data(
                    rec.date_start, rec.date_finished,
                    domain=[('time_type', 'in', ['leave', 'other'])]
                )
                if interval['hours'] > 8:
                    duration = '%sd' % round(interval['hours'] / 8, 2)
                elif interval['hours'] > 1:
                    duration = '%sh' % round(interval['hours'], 2)
                else:
                    duration = '%sm' % round(interval['hours'] * 60, 2)
            rec.x_duration_days = duration
