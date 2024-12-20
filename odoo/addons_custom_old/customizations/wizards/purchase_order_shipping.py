from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrderShipping(models.TransientModel):
    _name = 'purchase.order.shipping'
    _description = 'Purchase Order Shipping'

    x_order_id = fields.Many2one(comodel_name='purchase.order', required=True, ondelete="cascade")
    x_carrier_id = fields.Many2one(comodel_name='delivery.carrier', string='Shipping Method', required=True)
    x_shipping_cost = fields.Float(string='Cost', required=True)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True, default=19819)

    def button_confirm(self):
        if self.x_product_id.taxes_id:
            taxes_id = [self.x_product_id.taxes_id.id]
        else:
            taxes_id = []
        values = {
            'order_id': self.x_order_id.id,
            'product_id': self.x_product_id.id,
            'name': self.x_carrier_id.name,
            'product_qty': 1,
            'product_uom': self.x_product_id.uom_id.id,
            'price_unit': self.x_shipping_cost,
            'taxes_id': [(6, 0, taxes_id)],
            'date_planned': self.x_order_id.date_order,
            'x_is_shipping': True,
        }
        self.x_order_id.order_line = [(0, 0, values)]


