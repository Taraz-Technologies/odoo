from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    x_tracking_url = fields.Char(string='Tracking URL', required=False)
    x_average_delivery_days = fields.Integer(string='Avg. Delivery Days', required=False, tracking=True)
