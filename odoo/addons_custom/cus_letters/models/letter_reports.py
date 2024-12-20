from odoo import api, models, fields, _
from odoo.exceptions import UserError


class LetterReports(models.Model):
    _name = 'letter.reports'
    _description = 'Letters'
    _rec_name = 'x_name'
    _order = 'x_name desc'

    x_name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                         default=lambda self: _('New'))

    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    x_letter_head_report = fields.Boolean(string='Letter Head Report?', required=False)
    x_ref = fields.Char(string='Reference', required=False)
    x_sale_order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=False)
    x_purchase_order_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', required=False)

    x_letter_content = fields.Html(string="Letter Content", required=False)

    x_add_signature = fields.Boolean(string='Signature?', default=True)
    x_user_id = fields.Many2one(comodel_name='res.users', string='User', default=lambda self: self.env.uid, required=True)
    x_signature = fields.Html(string='Signature', related="x_user_id.signature", readonly=False, store=True)
    @api.model
    def create(self, vals):
        if vals.get('x_name', _('New')) == _('New'):
            vals['x_name'] = self.env['ir.sequence'].next_by_code('letter.reports') or 'New'
        return super(LetterReports, self).create(vals)

