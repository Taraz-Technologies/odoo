from odoo import models, fields, api, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Partner(models.Model):
    _inherit = 'res.partner'

    # x_octopart_name = fields.Char(string='OctoPart Name', required=False)
    # x_preferred_vendor = fields.Boolean(string='OctoPart Preferred Vendor', required=False)
