from odoo import api, models, fields
import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_update_move_line_sale_orders = fields.Boolean(compute="_update_move_line_source")

    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     for rec in self:
    #         rec.partner_id.commercial_partner_id.create_related_accounts()
    #     return super(AccountMove, self)._onchange_partner_id()

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self._update_move_line_source()
        return res

    @api.depends('x_sale_order', 'x_picking_ids', 'x_related_invoice_ids', 'invoice_origin', 'stock_move_id')
    def _update_move_line_source(self):
        for rec in self:
            origin = ''
            if rec.x_sale_order:
                origin = rec.x_sale_order.name
            elif rec.x_related_invoice_ids.mapped('x_sale_order'):
                origin = ','.join(rec.x_related_invoice_ids.mapped('x_sale_order').mapped('name'))
            elif rec.x_picking_ids:
                origin = ','.join(rec.x_picking_ids.mapped('origin'))
            elif rec.stock_move_id:
                origin = rec.stock_move_id.origin
            elif rec.invoice_origin:
                origin = rec.invoice_origin.replace("['", '').replace("']", '')

            rec.line_ids.write({'x_origin': origin})
            rec.x_update_move_line_sale_orders = True


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_origin = fields.Char(string='Source', required=False)
    x_label = fields.Char(string='Label', compute="_compute_label", store=True)
    x_luca_name = fields.Text(string="Luca Label", compute="_compute_luca_name", store=True)
    x_compute_payment_data = fields.Boolean(compute="_compute_payment_data", store=True)

    @api.depends('name')
    def _compute_payment_data(self):
        for rec in self:
            if not rec.name or not rec.payment_id:
                continue
            move_id = self.env['account.move'].search([('type', 'in', ('in_invoice', 'in_refund', 'out_invoice', 'out_refund'))])
            move_id = move_id.filtered(
                lambda l: l.name == rec.name or 'Vendor Payment: %s' % l.name == rec.name or 'Customer Payment: %s' % l.name == rec.name
            )
            if move_id:
                origin = move_id.line_ids[0].x_origin
                rec.x_origin = origin
                for line in rec.move_id.line_ids:
                    if not line.name:
                        if line.x_origin:
                            line.x_origin += ',%s' % origin
                        else:
                            line.x_origin = '%s' % origin
                        continue
                    line_move_id = self.env['account.move'].search([('type', 'in', ('in_invoice', 'in_refund', 'out_invoice', 'out_refund'))])
                    line_move_id = line_move_id.filtered(
                        lambda l: l.name == line.name or 'Vendor Payment: %s' % l.name == line.name or 'Customer Payment: %s' % l.name == rec.name
                    )
                    if line_move_id:
                        line.x_origin = line_move_id.line_ids[0].x_origin
                    elif line.x_origin:
                        line.x_origin += ',%s' % origin
                    else:
                        line.x_origin = '%s' % origin
            if not rec.x_origin:
                if rec.move_id.line_ids.mapped('analytic_tag_ids'):
                    rec.x_origin = ','.join(rec.move_id.line_ids.mapped('analytic_tag_ids').mapped('name'))
            if rec.analytic_tag_ids and not rec.x_origin:
                rec.move_id.line_ids.filtered(lambda l: not l.analytic_tag_ids).write({'analytic_tag_ids': rec.analytic_tag_ids.ids})

    # (PO/SO :: INV/BILL)
    # (SO :: INV :: BILL)

    # (PO/SO :: RO/DO :: INV/BILL)
    # (PO/SO :: RO/DO :: INV/BILL) Stock Valuation

    # (PO/SO :: RO/DO :: LC BILL)
    # (PO/SO :: RO/DO :: LC BILL :: LAN) Stock Valuation
    @api.depends('x_origin', 'move_id.name', 'move_id.state', 'move_id.picking_id', 'move_id.x_picking_ids', 'move_id.x_related_invoice_ids')
    def _compute_label(self):
        for rec in self:
            if not rec.move_id.picking_id and not rec.move_id.x_picking_ids and rec.move_id.type in ('in_invoice', 'out_invoice'):
                label = ''
                if rec.x_origin:
                    label += '%s :: ' % rec.x_origin
                if rec.move_id.x_related_invoice_ids.filtered(lambda l: l.state != 'cancel'):
                    invoices = ','.join(rec.move_id.x_related_invoice_ids.filtered(lambda l: l.state != 'cancel').mapped('name'))
                    label += '%s :: ' % invoices
                label += '%s' % rec.move_id.name
                rec.x_label = label
            elif rec.move_id.picking_id:
                rec.x_label = '%s :: %s :: %s' % (rec.move_id.picking_id.origin, rec.move_id.picking_id.name, rec.move_id.name)
                for line in rec.move_id.picking_id.move_lines.mapped('account_move_ids').mapped('line_ids'):
                    line.x_label = rec.x_label
            elif rec.move_id.x_picking_ids:
                origin = ','.join(rec.move_id.x_picking_ids.mapped('origin'))
                picking_name = ','.join(rec.move_id.x_picking_ids.mapped('name'))
                rec.x_label = '%s :: %s :: %s' % (origin, picking_name, rec.move_id.name)

            if rec.x_origin:
                rec.analytic_tag_ids = [(5, 0, 0)]
                if ',' in rec.x_origin:
                    origins = rec.x_origin.split(',')
                    for origin in origins:
                        if origin:
                            tag_id = self.env['account.analytic.tag'].search([('name', '=', origin)])
                            if not tag_id:
                                tag_id = self.env['account.analytic.tag'].create({
                                    'name': origin,
                                    # 'company_id': rec.move_id.company_id.id,
                                })
                            rec.analytic_tag_ids = [(4, tag_id.id)]
                else:
                    tag_id = self.env['account.analytic.tag'].search([('name', '=', rec.x_origin)])
                    if not tag_id:
                        tag_id = self.env['account.analytic.tag'].create({
                            'name': rec.x_origin,
                            # 'company_id': rec.move_id.company_id.id,
                        })
                    rec.analytic_tag_ids = [(4, tag_id.id)]

    @api.depends('name', 'x_label')
    def _compute_luca_name(self):
        for rec in self:
            rec.x_luca_name = '%s\n%s' % (rec.x_label, rec.name) if rec.x_label else rec.name



