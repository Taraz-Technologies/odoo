# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('state')
    def _get_invoiced(self):
        for order in self:
            invoice_ids = self.env['account.move'].search([('picking_id', '=', order.id)])
            order.invoice_count = len(invoice_ids)

    invoice_count = fields.Integer(string='# of Invoices', compute='_get_invoiced')

    def button_view_invoice(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        work_order_id = self.env['account.move'].search([('picking_id', '=', self.id)])
        inv_ids = []
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        context = {
            'default_type': work_order_id[0].type,
        }
        action['domain'] = [('id', 'in', work_order_id.ids)]
        action['context'] = context
        return action

    def create_invoice(self):
        res_config = self.env['res.config.settings'].sudo().search([], order="id desc", limit=1)
        for picking in self:
            if picking.state == 'done':
                if picking.picking_type_id.code == 'incoming':
                    if picking.company_id.id != self.env.company.id:
                        raise UserError(_("Odoo selected company is not same as the order company!"))
                    account_inv_obj = self.env['account.move']
                    journal = self.env['account.move'].with_context(default_type='in_invoice')._get_default_journal()
                    if not journal:
                        raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                            picking.company_id.name, picking.company_id.id))
                    if self._context.get('flag') == True:
                        for record in picking.purchase_ids:
                            vals = {
                                'type': 'in_invoice',
                                'invoice_origin': record.name,
                                'pur_id': record.id,
                                'journal_id': journal.id,
                                'purchase_id': record.id,
                                'partner_id': picking.partner_id.id,
                                'picking_id': picking.id,
                                'currency_id': record.currency_id.id,

                                'ref': record.partner_ref,
                                'x_operation_type': record.x_operation_type,
                                'invoice_date': picking.x_form_field_09.date(),
                                'x_document': record.x_attachment,
                                'x_related_po_s': record.x_related_po_s.ids,
                                'x_related_so_s': record.x_related_so_s.ids,
                                'invoice_incoterm_id': record.incoterm_id.id,
                                'invoice_payment_term_id': record.payment_term_id.id,
                                'x_payment_method': record.x_payment_method.id,
                                'x_purchase_type': record.x_purchase_type,
                                'x_item_type': record.x_item_type,
                                'x_import_method': record.x_import_method,
                                'x_weboc_gd': record.x_weboc_gd,
                                'x_assessed_value': record.x_assessed_value,
                                'x_comments': record.x_comments,

                                'x_attachment_name': picking.x_attachment_name if picking.company_id.id == 2 else False,
                                'x_attachment': picking.x_attachment if picking.company_id.id == 2 else False,
                                'x_form_field_01': picking.x_form_field_01 if picking.company_id.id == 2 else False,
                                'x_form_field_02': picking.x_form_field_02 if picking.company_id.id == 2 else False,
                                'x_form_field_03': picking.x_form_field_03 if picking.company_id.id == 2 else False,
                                'x_form_field_04': picking.x_form_field_04 if picking.company_id.id == 2 else False,
                                'x_form_field_05': picking.x_form_field_05 if picking.company_id.id == 2 else False,
                                'x_form_field_06': picking.x_form_field_06 if picking.company_id.id == 2 else False,
                                'x_form_field_07': picking.x_form_field_07 if picking.company_id.id == 2 else False,
                                'x_form_field_08': picking.x_form_field_08 if picking.company_id.id == 2 else False,
                                'x_form_field_09': picking.x_form_field_09 if picking.company_id.id == 2 else False,
                                'x_form_field_10': picking.x_form_field_10 if picking.company_id.id == 2 else False,
                                'x_form_field_11': picking.x_form_field_11 if picking.company_id.id == 2 else False,
                                'x_form_field_12': picking.x_form_field_12 if picking.company_id.id == 2 else False,
                                'x_form_field_13': picking.x_form_field_13.id if picking.company_id.id == 2 else False,
                                'x_form_field_14': picking.x_form_field_14.id if picking.company_id.id == 2 else False,
                            }
                            res = account_inv_obj.create(vals)
                            po_lines = record.order_line
                            new_lines = self.env['account.move.line']
                            new_lines = []
                            for line in po_lines.filtered(lambda l: not l.display_type):
                                new_lines.append((0, 0, line._prepare_account_move_line(res)))
                                new_lines.append((0, 0, line._prepare_advance_account_move_line(res)))
                            res.write({
                                'invoice_line_ids': new_lines,
                                'journal_id': picking.company_id.x_delivery_bill_journal_id.id,
                                'invoice_date': picking.x_form_field_09.date(),
                                'date': picking.x_form_field_09.date(),
                            })
                            res._onchange_invoice_date()
                            for inv in res:
                                if res_config.auto_validate_invoice:
                                    inv.action_post()
                                if self._context.get('validate') and self._context.get('flag'):
                                    inv.action_post()
                                if res_config.auto_validate_invoice and res_config.auto_send_mail_invoice:
                                    template = self.env.ref('account.email_template_edi_invoice', False)
                                    send = inv.with_context(
                                        force_send=True, model_description='Invoice'
                                    ).message_post_with_template(
                                        int(template), email_layout_xmlid="mail.mail_notification_paynow"
                                    )
                    elif picking.purchase_id:
                        vals = {
                            'type': 'in_invoice',
                            'invoice_origin': picking.origin,
                            'pur_id': picking.purchase_id.id,
                            'journal_id': picking.company_id.x_delivery_bill_journal_id.id,
                            'purchase_id': picking.purchase_id.id,
                            'partner_id': picking.partner_id.id,
                            'picking_id': picking.id,
                            'currency_id': picking.purchase_id.currency_id.id,

                            'ref': '%s - DBILL' % picking.purchase_id.partner_ref,
                            'x_operation_type': picking.purchase_id.x_operation_type,
                            'invoice_date': picking.x_form_field_09.date(),
                            'date': picking.x_form_field_09.date(),
                            'x_document': picking.purchase_id.x_attachment,
                            'x_related_po_s': picking.purchase_id.x_related_po_s.ids,
                            'x_related_so_s': picking.purchase_id.x_related_so_s.ids,
                            'invoice_incoterm_id': picking.purchase_id.incoterm_id.id,
                            'invoice_payment_term_id': picking.purchase_id.payment_term_id.id,
                            'x_payment_method': picking.purchase_id.x_payment_method.id,
                            'x_purchase_type': picking.purchase_id.x_purchase_type,
                            'x_item_type': picking.purchase_id.x_item_type,
                            'x_import_method': picking.purchase_id.x_import_method,
                            'x_weboc_gd': picking.purchase_id.x_weboc_gd,
                            'x_assessed_value': picking.purchase_id.x_assessed_value,
                            'x_comments': picking.purchase_id.x_comments,

                            'x_attachment_name': picking.x_attachment_name if picking.company_id.id == 2 else False,
                            'x_attachment': picking.x_attachment if picking.company_id.id == 2 else False,
                            'x_form_field_01': picking.x_form_field_01 if picking.company_id.id == 2 else False,
                            'x_form_field_02': picking.x_form_field_02 if picking.company_id.id == 2 else False,
                            'x_form_field_03': picking.x_form_field_03 if picking.company_id.id == 2 else False,
                            'x_form_field_04': picking.x_form_field_04 if picking.company_id.id == 2 else False,
                            'x_form_field_05': picking.x_form_field_05 if picking.company_id.id == 2 else False,
                            'x_form_field_06': picking.x_form_field_06 if picking.company_id.id == 2 else False,
                            'x_form_field_07': picking.x_form_field_07 if picking.company_id.id == 2 else False,
                            'x_form_field_08': picking.x_form_field_08 if picking.company_id.id == 2 else False,
                            'x_form_field_09': picking.x_form_field_09 if picking.company_id.id == 2 else False,
                            'x_form_field_10': picking.x_form_field_10 if picking.company_id.id == 2 else False,
                            'x_form_field_11': picking.x_form_field_11 if picking.company_id.id == 2 else False,
                            'x_form_field_12': picking.x_form_field_12 if picking.company_id.id == 2 else False,
                            'x_form_field_13': picking.x_form_field_13.id if picking.company_id.id == 2 else False,
                            'x_form_field_14': picking.x_form_field_14.id if picking.company_id.id == 2 else False,
                        }
                        res = account_inv_obj.create(vals)
                        po_lines = picking.purchase_id.order_line
                        new_lines = self.env['account.move.line']
                        new_lines = []
                        for line in po_lines.filtered(lambda l: not l.display_type):
                            if line._prepare_account_move_line(res)['quantity'] != 0:
                                new_lines.append((0, 0, line._prepare_account_move_line(res)))
                                new_lines.append((0, 0, line._prepare_advance_account_move_line(res)))
                        res.write({'invoice_line_ids': new_lines})
                        for line in res.invoice_line_ids:
                            line.account_id = line.product_id.product_tmpl_id._get_product_accounts()['stock_input'] or line.account_id
                        for inv in res:
                            if res_config.auto_validate_invoice:
                                inv.action_post()
                            if self._context.get('validate') and self._context.get('flag'):
                                inv.action_post()
                            if res_config.auto_validate_invoice and res_config.auto_send_mail_invoice:
                                template = self.env.ref('account.email_template_edi_invoice', False)
                                send = inv.with_context(
                                    force_send=True, model_description='Invoice'
                                ).message_post_with_template(
                                    int(template), email_layout_xmlid="mail.mail_notification_paynow"
                                )

                    for purchase_line in account_inv_obj.invoice_line_ids:
                        if purchase_line.quantity <= 0:
                            purchase_line.unlink()
                if picking.picking_type_id.code == 'outgoing':
                    sale_order = self.env['sale.order'].search([('name', '=', picking.origin)])
                    if sale_order.company_id.id != self.env.company.id and sale_order:
                        raise UserError(_("Odoo selected company is not same as the sale order company!"))
                    if picking.origin:
                        pass
                    else:
                        picking.update({'origin': self._context.get('default_origin')})

                    if sale_order:
                        invoice = sale_order._create_invoices()
                        invoice.write({
                            'picking_id': picking.id,
                            'journal_id': sale_order.company_id.x_delivery_invoice_journal_id.id,
                            'invoice_date': picking.x_form_field_09.date(),
                            'date': picking.x_form_field_09.date(),
                        })
                        invoice._onchange_invoice_date()
                        if res_config.auto_validate_invoice:
                            invoice.action_post()
                        if res_config.auto_validate_invoice and res_config.auto_send_mail_invoice:
                            template = self.env.ref('account.email_template_edi_invoice', False)
                            send = invoice.with_context(
                                force_send=True, model_description='Invoice'
                            ).message_post_with_template(
                                int(template), email_layout_xmlid="mail.mail_notification_paynow"
                            )
                picking._get_invoiced()

    def action_done(self):
        action = super(Picking, self).action_done()
        self.create_invoice()
        return action
