from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_investment_value = fields.Float(string="Investment Value",  required=False, )

    @api.constrains('x_investment_value')
    def update_investment_invoice_lines(self):
        for rec in self:
            if rec.journal_id.id in [23, 71] and rec.x_investment_value > 0:
                product_id = self.env['product.product'].browse(19404)
                rec.invoice_line_ids = [(0, 0, {
                    'product_id': product_id.id,
                    'account_id': 477,
                    'quantity': 1,
                    'price_unit': rec.x_investment_value,
                    'product_uom_id': product_id.uom_id.id,
                })]

























