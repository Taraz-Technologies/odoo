from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    x_bill_currency_id = fields.Many2one(related="vendor_bill_id.currency_id", store=True)
    x_bill_amount = fields.Monetary(string='Bill Amount', related="vendor_bill_id.amount_untaxed", store=True)
    x_partner_id = fields.Many2one(string='Vendor', related="vendor_bill_id.partner_id", store=True)

    x_custom_tag_ids = fields.Many2many('custom.tags', string='Tags')
    company_id = fields.Many2one('res.company', string="Company",
                                 related='account_journal_id.company_id', store=True)

    def write(self, vals):
        old_values = self.x_custom_tag_ids.ids
        res = super(LandedCost, self).write(vals)
        new_values = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_values, new_values=new_values
            )
        return res

    def button_validate(self):
        for rec in self:
            if any(picking.state != 'done' for picking in rec.picking_ids):
                raise UserError("You cannot validate Landed Cost if transfers are not done!")
        super(LandedCost, self).button_validate()

    def compute_landed_cost(self):
        for rec in self:
            if any(picking.state != 'done' for picking in rec.picking_ids):
                raise UserError("You cannot compute Landed Cost if transfers are not done!")
        super(LandedCost, self).compute_landed_cost()
