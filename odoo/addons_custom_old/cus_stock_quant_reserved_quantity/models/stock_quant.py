from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_stock_quant_reserved_quantity(self):
        return {
            'name': _('Update Reserved Quantity'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant.reserved.quantity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_stock_quant_id': self.id,
                'default_reserved_quantity': self.reserved_quantity,
            },
        }
