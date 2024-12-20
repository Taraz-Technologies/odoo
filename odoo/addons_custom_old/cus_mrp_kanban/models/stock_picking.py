from odoo import models, fields, api, SUPERUSER_ID
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Picking(models.Model):
    _inherit = 'stock.picking'

    def action_view_related_production(self):
        action = self.env.ref('cus_mrp_kanban.action_mrp_production_kanban_view_cus_mrp_kanban').read()[0]
        action['context'] = {
            "search_default_group_by_x_stage_id": 1,
            'search_default_name': self.x_sale_id.name,
        }
        return action
