from odoo import models, fields, api, SUPERUSER_ID


class MrpWorkorderStage(models.Model):
    _name = 'mrp.workorder.stage'
    _description = 'Workorder Kanban Stage'
    # _rec_name = 'name'
    # _order = 'sequence, id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    #
    # name = fields.Char(string='Stage Name', required=True, translate=True)
    # sequence = fields.Integer(default=1)
    # fold = fields.Boolean(
    #     string='Folded in Kanban',
    #     help='This stage is folded in the kanban view when there are no records in that stage to display.')
    # workcenter_id = fields.Many2one(comodel_name='mrp.workcenter', string='Work Center')
