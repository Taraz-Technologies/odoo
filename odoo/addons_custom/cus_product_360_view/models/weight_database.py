from odoo import api, fields, models


class WeightDatabase(models.Model):
    _name = 'weight.database'
    _description = 'Weight Database'
    _rec_name = "display_name"

    display_name = fields.Char(compute='_compute_display_name', store=True)
    x_quantity = fields.Integer(string='Quantity', required=True, default=1)
    x_weight = fields.Float(string='Weight (kg)', required=True, digits=(12, 6))
    x_unit_weight = fields.Float(string='Unit Weight (kg)', digits=(12, 6), compute="_compute_unit_weight", store=True)
    x_description_keyword_01 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_02 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_03 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_04 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_05 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_06 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_07 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_08 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')
    x_description_keyword_09 = fields.Many2one(comodel_name='description.keyword', string='Description Keyword')

    @api.depends('x_weight', 'x_quantity')
    def _compute_unit_weight(self):
        for rec in self:
            rec.x_unit_weight = rec.x_weight / rec.x_quantity if rec.x_quantity != 0 else 0

    @api.depends('x_description_keyword_01', 'x_description_keyword_02', 'x_description_keyword_03', 
                 'x_description_keyword_04', 'x_description_keyword_05', 'x_description_keyword_06', 
                 'x_description_keyword_07', 'x_description_keyword_08', 'x_description_keyword_09',)
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = ''
            rec.display_name += '[' + rec.x_description_keyword_01.x_name + ']' if rec.x_description_keyword_01 else ''
            rec.display_name += '[' + rec.x_description_keyword_02.x_name + ']' if rec.x_description_keyword_02 else ''
            rec.display_name += '[' + rec.x_description_keyword_03.x_name + ']' if rec.x_description_keyword_03 else ''
            rec.display_name += '[' + rec.x_description_keyword_04.x_name + ']' if rec.x_description_keyword_04 else ''
            rec.display_name += '[' + rec.x_description_keyword_05.x_name + ']' if rec.x_description_keyword_05 else ''
            rec.display_name += '[' + rec.x_description_keyword_06.x_name + ']' if rec.x_description_keyword_06 else ''
            rec.display_name += '[' + rec.x_description_keyword_07.x_name + ']' if rec.x_description_keyword_07 else ''
            rec.display_name += '[' + rec.x_description_keyword_08.x_name + ']' if rec.x_description_keyword_08 else ''
            rec.display_name += '[' + rec.x_description_keyword_09.x_name + ']' if rec.x_description_keyword_09 else ''


class DescriptionKeyword(models.Model):
    _name = "description.keyword"
    _description = "Description Keyword"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string='Property Name')
