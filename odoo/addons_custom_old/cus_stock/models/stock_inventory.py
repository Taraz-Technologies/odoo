from odoo import api, fields, models, _


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    x_image_128 = fields.Image(related='product_id.image_128', string='Image')
    x_description = fields.Text(related='product_id.description')