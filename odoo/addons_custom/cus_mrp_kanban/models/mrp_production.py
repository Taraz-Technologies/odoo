from odoo import models, fields, api, SUPERUSER_ID
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    x_stage_id = fields.Many2one(
        comodel_name='mrp.production.stage', string='Stage', tracking=True, copy=False,
        group_expand='_read_group_stage_ids', compute='_compute_stage_id', store=True,
    )

    @api.depends('state')
    def _compute_stage_id(self):
        for rec in self:
            rec.x_stage_id = self.env['mrp.production.stage'].search([
                ('x_manufacturing_state', '=', rec.state)
            ], limit=1).id

    x_need_attention = fields.Boolean(compute="_compute_need_attention", store=True)

    @api.depends('workorder_ids', 'workorder_ids.x_need_attention')
    def _compute_need_attention(self):
        for rec in self:
            if any(workorder.x_need_attention for workorder in rec.workorder_ids):
                rec.x_need_attention = True
            else:
                rec.x_need_attention = False
