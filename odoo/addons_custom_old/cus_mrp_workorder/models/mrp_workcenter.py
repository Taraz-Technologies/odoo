from odoo import api, exceptions, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    user_id = fields.Many2one(comodel_name="res.users", string="Responsible")
    x_mounting_type = fields.Selection(selection=[
        ('smd', 'SMT'),
        ('th', 'THT'),
        ('other', 'OTHER')
    ], string='Component Type', tracking=True, track_visibility='always')

