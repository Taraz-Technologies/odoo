from odoo import api, fields, models, _

import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_update_crm_lead_amount_lines = fields.Boolean(compute="update_crm_lead_amount_lines")

    @api.depends('state')
    def update_crm_lead_amount_lines(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)
            if order_id:
                order_id.update_crm_lead_amount_lines()
            rec.x_update_crm_lead_amount_lines = True



