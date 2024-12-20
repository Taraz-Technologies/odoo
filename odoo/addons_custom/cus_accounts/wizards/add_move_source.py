from odoo import fields, models, api, _


class AddMoveSource(models.TransientModel):
    _name = 'add.move.source'
    _description = 'Add Move Source'

    x_move_id = fields.Many2one('account.move', string='Move')
    x_company_id = fields.Many2one(related='x_move_id.company_id')
    x_partner_id = fields.Many2one(related='x_move_id.partner_id')
    x_add_to = fields.Selection(selection=[
        ('sale', 'Sale Order'),
        ('purchase', 'Purchase Order'),
        ('related_sale', 'Related Sale Order'),
        ('related_purchase', 'Related Purchase Order'),
    ], string='Add to', required=False, )

    x_sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=False,
                                domain="[('partner_id', '=', x_partner_id), ('company_id', '=', x_company_id)]")
    x_purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', required=False,
                                    domain="[('partner_id', '=', x_partner_id), ('company_id', '=', x_company_id)]")
    x_sale_ids = fields.Many2many(comodel_name='sale.order', string='Related Sale Orders',
                                  domain="[('company_id', '=', x_company_id)]")
    x_purchase_ids = fields.Many2many(comodel_name='purchase.order', string='Related Purchase Orders',
                                      domain="[('company_id', '=', x_company_id)]")

    def action_add(self):
        for rec in self:
            if rec.x_add_to == 'sale':
                rec.x_sale_id.invoice_ids = [(4, rec.x_move_id.id)]
                rec.x_move_id.x_sale_order = rec.x_sale_id.id
            elif rec.x_add_to == 'purchase':
                rec.x_purchase_id.invoice_ids = [(4, rec.x_move_id.id)]
                rec.x_move_id.x_purchase_id = rec.x_purchase_id.id
            elif rec.x_add_to == 'related_sale':
                rec.x_move_id.x_sale_ids = rec.x_sale_ids.ids or False
                rec.x_move_id.x_picking_ids = rec.x_sale_ids.mapped('picking_ids').ids or False
            elif rec.x_add_to == 'related_purchase':
                rec.x_move_id.x_related_po_s = rec.x_purchase_ids.ids or False
                rec.x_move_id.x_picking_ids = rec.x_purchase_ids.mapped('picking_ids').ids or False




