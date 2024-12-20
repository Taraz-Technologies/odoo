from odoo import api, fields, models
from odoo.exceptions import UserError


class Location(models.Model):
    _inherit = "stock.location"

    image_1920 = fields.Image("Image")
    x_product_type_id = fields.Many2one(comodel_name='product.type', string='Store Parts Type')
    x_product_sub_type_id = fields.Many2one(comodel_name='product.sub.type', string='Store Parts Sub-Type')
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    @api.constrains('name', 'location_id')
    def name_constrains(self):
        for rec in self:
            duplicate_location_ids = len(
                self.env['stock.location'].search([('name', '=', rec.name), ('location_id', '=', rec.location_id.id)])
            )
            if duplicate_location_ids > 1:
                raise UserError('Location name must be Unique')



