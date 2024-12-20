from odoo import models, fields, api, _


class StockQuantReservedQuantity(models.TransientModel):
    _name = 'stock.quant.reserved.quantity'
    _description = 'Stock Quant Reserved Quantity'

    stock_quant_id = fields.Many2one(comodel_name='stock.quant', string='Product Quantity', required=True)
    reserved_quantity = fields.Float(string='Reserved Quantity', required=True)

    def action_confirm(self):
        self.stock_quant_id.sudo().update({'reserved_quantity': self.reserved_quantity})
        return {'type': 'ir.actions.act_window_close'}
