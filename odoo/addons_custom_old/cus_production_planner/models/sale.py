from odoo import api, fields, models, _
from odoo.tools import html_escape as escape
from odoo.exceptions import UserError


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     def action_confirm(self):
#         res = super(SaleOrder, self).action_confirm()
#         for rec in self:
#             order_list_ids = self.env['sale.order.list'].search([('x_sale_order_number', '=', rec.id)])
#             for line in rec.order_line.filtered(
#                     lambda l: 'Finished Goods' in l.product_id.categ_id.name and l.product_id.virtual_available < 0
#             ):
#
#                 order_list_id = order_list_ids.filtered(
#                     lambda l: l.x_manufacturing_id.product_id.id == line.product_id.id
#                 )
#
#                 if not order_list_id:
#                     vals = {
#                         'product_id': line.product_id.id,
#                         'product_qty': - line.product_id.virtual_available,
#                         'product_uom_id': line.product_uom.id,
#                         'location_src_id': 17,
#                     }
#                     bom_id = self.env['bom.tool'].search(
#                         [('x_base_product_id.product_variant_ids', '=', line.product_id.id)]
#                     ).x_bom_id
#                     if not bom_id:
#                         bom_id = self.env['product.variant'].search(
#                             [('x_product_id.product_variant_ids', '=', line.product_id.id),
#                              ('x_bom_tool_id', '!=', False)]
#                         ).x_product_bom_id
#
#                     if bom_id:
#                         vals['bom_id'] = bom_id.id
#                         production_id = self.env['mrp.production'].create(vals)
#                         production_id._onchange_bom_id()
#                         production_id.product_qty = line.product_uom_qty
#                         production_id._onchange_move_raw()
#                         production_id.action_confirm()
#                         picking_id = self.env['stock.picking'].search([('origin', '=', production_id.name)])
#                         picking_id.action_assign()
#                         if picking_id.show_check_availability:
#                             production_id.x_production_status = 'proc_required'
#                         else:
#                             production_id.x_production_status = 'can_be_manufactured_full'
#                         production_id.x_sale_order_list = [(0, 0, {
#                             'x_sale_order_number': rec.id, 'x_quantity': - line.product_id.virtual_available,
#                         })]
#                     else:
#                         bom_id = self.env['mrp.bom'].search([
#                             ('product_tmpl_id.product_variant_ids', '=', line.product_id.id)
#                         ])[0]
#                         if bom_id:
#                             vals['bom_id'] = bom_id.id
#                             vals['x_production_status'] = 'bom_tool_not_defined'
#                             production_id = self.env['mrp.production'].create(vals)
#                             production_id.x_sale_order_list = [(0, 0, {
#                                 'x_sale_order_number': rec.id, 'x_quantity': - line.product_id.virtual_available,
#                             })]
#         return res

