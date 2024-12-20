from odoo import fields, models, api, _


class LogisticsRoute(models.Model):
    _name = "logistics.route"
    _description = "Logistics Route"
    _rec_name = 'x_name'

    x_name = fields.Char(string='Name', required=True)
    x_description = fields.Char(string='Description', required=False)
    x_sub_route_ids = fields.Many2many(comodel_name='logistics.sub.route', string='Sub Routes')


class LogisticsSubRoute(models.Model):
    _name = "logistics.sub.route"
    _description = "Logistics Sub-Route"
    _rec_name = 'x_name'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', required=False)
    x_name = fields.Char(string='Name', required=True)
    x_from = fields.Many2one(comodel_name='res.partner', string='From', required=False)
    x_to = fields.Many2one(comodel_name='res.partner', string='To', required=False)
    x_delivery_days = fields.Integer(string='Delivery Days', required=False)

