from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_package_id = fields.Many2one(related="x_taraz_part_number_id.x_package_id", readonly=False, store=True)


class Product(models.Model):
    _inherit = 'product.product'

    x_package_id = fields.Many2one(related="x_taraz_part_number_id.x_package_id", readonly=False, store=True)

    # @api.model
    # def create(self, vals):
    #     res = super(Product, self).create(vals)
    #     res['barcode'] = res['name']
    #     return res


class TarazPartNumber(models.Model):
    _inherit = "taraz.part.number"

    x_package_id = fields.Many2one(comodel_name='nd4.packages', string='Package')

