from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Partner(models.Model):
    _inherit = 'res.partner'

    x_is_forwarder = fields.Boolean(string='Is Forwarder?', required=False, )



