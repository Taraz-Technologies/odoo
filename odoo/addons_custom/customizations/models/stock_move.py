from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_purchase_order_id = fields.Many2one(related='picking_id.purchase_id',)
    x_partner_id = fields.Many2one(related='x_purchase_order_id.partner_id',)
    x_sale_order_id = fields.Many2one(related='picking_id.sale_id',)
    x_production_id = fields.Many2one(
        comodel_name='mrp.production', compute="_compute_production_order", store=True, string='Manufacturing Order'
    )
    x_finished_product_id = fields.Many2one(related="x_production_id.product_id", store=True)

    @api.depends('reference', 'origin', 'created_production_id', 'raw_material_production_id', 'production_id')
    def _compute_production_order(self):
        for rec in self:
            production_id = (
                rec.created_production_id or rec.raw_material_production_id or rec.production_id or
                self.env['mrp.production'].search(['|', ('name', '=', rec.reference), ('name', '=', rec.origin)], limit=1)
            )
            rec.x_production_id = production_id.id
