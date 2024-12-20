from odoo import fields, models


class Country(models.Model):
    _name = 'res.country'
    _inherit = 'res.country'

    x_turkish_translation = fields.Char(string='Turkish Translation')