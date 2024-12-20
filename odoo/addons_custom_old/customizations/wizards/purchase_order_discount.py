from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrderDiscount(models.TransientModel):
    _name = 'purchase.order.discount'
    _description = 'Purchase Order Discount'

    x_order_id = fields.Many2one(comodel_name='purchase.order', required=True, ondelete="cascade")
    x_discount = fields.Float(string='Discount', required=False)

    def button_confirm(self):
        for line in self.x_order_id.order_line:
            line.x_discount = self.x_discount
