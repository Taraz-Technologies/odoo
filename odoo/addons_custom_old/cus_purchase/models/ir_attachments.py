from odoo import models, fields, api, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        res = super(IrAttachment, self).create(vals)
        if vals.get('res_model') == 'purchase.order' and vals.get('res_id'):
            purchase_order = self.env['purchase.order'].browse(vals.get('res_id'))
            new_vals = []
            for payment_invoice_id in purchase_order.x_payment_invoice_ids:
                attachment_vals = vals
                attachment_vals['res_id'] = payment_invoice_id.id
                attachment_vals['res_model'] = 'account.move'
                attachment_vals['res_name'] = payment_invoice_id.name
                new_vals.append(attachment_vals)
            if new_vals:
                self.create(new_vals)
        return res
