from odoo import _, api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Partner(models.Model):
    _inherit = 'res.partner'

    x_manufacturer = fields.Boolean(string="Is Manufacturer?")

    @api.onchange('x_partner_type')
    def update_manufacturer_status(self):
        for rec in self:
            if rec.x_partner_type != 'Vendor':
                rec.x_manufacturer = False
