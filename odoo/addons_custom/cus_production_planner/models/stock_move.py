from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_ref_des = fields.Char(string='RefDes')
    x_goods_type = fields.Selection(related="product_id.x_goods_type")
    x_description = fields.Text(related="product_id.description")
    x_mrp_demand_ids = fields.One2many(related="x_production_id.x_mrp_demand_ids")
    x_demand_batch_id = fields.Many2one(related="x_production_id.x_demand_batch_id", store=True)

    def _prepare_phantom_move_values(self, bom_line, product_qty, quantity_done):
        data = super(StockMove, self)._prepare_phantom_move_values(bom_line, product_qty, quantity_done)
        data['x_ref_des'] = bom_line.x_ref_des
        return data

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        vals['x_ref_des'] = self.x_ref_des
        return vals


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_ref_des = fields.Char(string='RefDes')
    x_image_128 = fields.Image(related='product_id.image_128', string='Image')






