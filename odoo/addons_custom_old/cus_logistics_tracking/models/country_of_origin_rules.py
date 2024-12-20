from odoo import fields, models, api, _


class CountryOfOriginRules(models.Model):
    _name = "country.of.origin.rules"
    _description = "Country Of Origin Rules"
    _rec_name = 'x_name'

    x_name = fields.Char(string='Description', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id)
    x_country_ids = fields.Many2many(comodel_name='res.country', string='Forbidden Countries')
    x_country_id = fields.Many2one(comodel_name='res.country', string='Import from Country', required=True, default=233)

