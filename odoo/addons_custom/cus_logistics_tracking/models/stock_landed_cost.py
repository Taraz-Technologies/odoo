from odoo import models, fields, api, _


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    x_free_zone_operation_id = fields.Many2one(related="vendor_bill_id.x_free_zone_operation_id")

    def get_valuation_lines(self):
        lines = super(LandedCost, self).get_valuation_lines()
        for rec in self:
            if rec.x_free_zone_operation_id:
                product_ids = rec.x_free_zone_operation_id.x_product_ids.mapped('x_product_id').ids
                lines = [line for line in lines if line['product_id'] in product_ids]
        return lines
