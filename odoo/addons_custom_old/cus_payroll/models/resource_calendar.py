from odoo import api, fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    x_fine_by = fields.Selection(selection=[
        ('amount', 'Fix Amount'),
        ('percentage', 'By Percentage of Salary'),
    ], required=False, string='Fine By',)

    x_late_coming_fine = fields.Boolean(string='Late Coming Fine?', required=False)
    x_early_going_fine = fields.Boolean(string='Early Going Fine?', required=False)

    x_late_coming_fine_percentage = fields.Float(string='Fine (Late Coming)', required=False)
    x_early_going_fine_percentage = fields.Float(string='Fine (Early Going)', required=False)

    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=165, required=False)
    x_late_coming_fine_amount = fields.Float(string='Fine (Late Coming)', required=False)
    x_early_going_fine_amount = fields.Float(string='Fine (Early Going)', required=False)

    x_minutes = fields.Integer(string='Minutes', required=False)


