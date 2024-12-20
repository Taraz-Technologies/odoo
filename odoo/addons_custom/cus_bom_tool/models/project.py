from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Task(models.Model):
    _inherit = "project.task"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)

    def action_view_bom_tool(self):
        action = self.env.ref('cus_bom_tool.action_view_bom_tool').read()[0]
        form_view = [(self.env.ref('cus_bom_tool.bom_tool_form_view').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_bom_tool_id.id
        return action


