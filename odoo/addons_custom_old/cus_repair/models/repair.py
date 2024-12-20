from odoo import models,fields,api
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    x_repair_type = fields.Selection([
        ('single', 'Single Product'),
        ('multiple', 'Multiple Products'),
    ], string='Repair Type', default='single')
    x_product_ids = fields.Many2many('product.product', string='Products')
    x_sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    x_stock_picking_ids = fields.Many2many(
        'stock.picking',
        relation='repair_order_stock_picking_relation',
        column1='repair_order_id',
        column2='stock_picking_id',
        string="Sale Order Repairs",
    )

    x_move_line_ids = fields.One2many(related='x_stock_picking_ids.move_line_ids_without_package')

    @api.onchange(
        'x_repair_type'
    )
    def onchange_repair_type(self):
        if self.x_repair_type == 'single':
            self.update({
                'x_product_ids': [(5, 0, 0)]
            })
        elif self.x_repair_type == 'multiple':
            self.product_id = False
        else:
            pass

    @api.onchange('x_sale_order_id')
    def _compute_pickings(self):
        for rec in self:
            if rec.x_sale_order_id:
                picking_ids = self.env['stock.picking'].search([('sale_id', '=', self.x_sale_order_id.id), ('picking_type_code', '=', 'incoming')])
                rec.x_stock_picking_ids = False
                if picking_ids:
                    rec.x_stock_picking_ids = [(4, picking_id.id) for picking_id in picking_ids]
            # rec.x_compute_pickings = False

    # def action_create_delivery(self):
    #     action = self.env.ref('act_stock_return_picking').read()[0]
    #     if not action:
    #         raise UserError("Action Not Found!")


