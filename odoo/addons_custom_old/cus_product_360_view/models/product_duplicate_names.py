from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductDuplicateName(models.Model):
    _name = "product.duplicate.names"
    _description = "Product Duplicate Name"
    _rec_name = "x_product_id"

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product', required=False)
    x_description = fields.Text(related="x_product_id.description")
    x_other_name_tag_ids = fields.Many2many(comodel_name='product.other.name.tags', string='Other Names',
                                            relation='product_other_name_tags_product_duplicate_names_rel_1',
                                            column1='product_other_name_tags_id', column2='product_duplicate_names_id')
    x_product_ids = fields.Many2many(comodel_name='product.product', string='Duplicate Products')

    @api.onchange('x_other_name_tag_ids')
    def update_product_other_names(self):
        for rec in self:
            rec.x_product_id.x_other_name_tag_ids = rec.x_other_name_tag_ids.ids

    def move_other_products_data(self):
        for rec in self:
            other_names = rec.x_other_name_tag_ids.mapped('x_name')
            product_ids = self.env['product.product'].search([('name', 'in', other_names)])
            product_ids = product_ids.filtered(lambda l: l.qty_available != 0)
            for product in product_ids:
                # Update Purchase & Consumption History
                if product.id not in rec.x_product_ids.ids:
                    rec.x_product_ids = [(4, product.id)]

                    for history in product.product_tmpl_id.x_purchase_history_ids:
                        history.copy({'x_product_id': rec.x_product_id.id})

                    for history in product.product_tmpl_id.x_consumption_history_ids:
                        history.copy({'x_component_id': rec.x_product_id.id})

                # Compute Move Quantity
                quantity = 0
                domain = [('product_id', '=', product.id), ('on_hand', '=', True)]
                stock_quant_ids = self.env['stock.quant'].search(domain)
                for stock_quant in stock_quant_ids:
                    quantity = stock_quant.quantity - stock_quant.reserved_quantity
                    if quantity <= 0:
                        continue
                    else:
                        break
                if quantity <= 0:
                    continue

                # Create BOM
                bom_id = self.env['mrp.bom'].create({
                    'product_tmpl_id': rec.x_product_id.id,
                    'product_qty': quantity,
                    'code': 'Duplicate Component Move',
                    'bom_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'product_qty': quantity,
                    })]
                })

                # Create Manufacturing Order
                product_id = self.env['product.product'].search([('product_tmpl_id', '=', rec.x_product_id.id)])
                production_id = self.env['mrp.production'].create({
                    'product_id': product_id.id,
                    'product_qty': quantity,
                    'product_uom_id': product_id.uom_id.id,
                    'bom_id': bom_id.id,
                    'location_dest_id': stock_quant.location_id.id,
                })
                production_id._onchange_bom_id()
                production_id._onchange_move_raw()
                production_id.action_confirm()
                production_id.action_assign()

                action = self.env.ref('mrp.mrp_production_action').read()[0]
                form_view = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
                if 'views' in action:
                    action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
                else:
                    action['views'] = form_view
                action['res_id'] = production_id.id
                return action


class ProductOtherNameTags(models.Model):
    _name = "product.other.name.tags"
    _description = "Product Other Name Tags"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)










