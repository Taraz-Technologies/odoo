from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', readonly=True, store=True)
