from odoo import api, models, fields, _
from odoo.exceptions import UserError


class Help(models.Model):
    _name = 'res.help'
    _description = 'Help'
    _rec_name = 'x_model_id'
    
    x_model_id = fields.Many2one(comodel_name='ir.model', string='Model', required=False)
    x_memo = fields.Html(string='Help Note', required=False)

