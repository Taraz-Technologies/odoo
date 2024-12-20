from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
from odoo.tools.misc import format_date

import datetime
import json
import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountAccount(models.Model):
    _inherit = "account.account"

    x_notes = fields.Text(string="Notes", required=False, tracking=True)
    x_quickbooks_name = fields.Char(string="QuickBooks Name", required=False, tracking=True)
    x_luca_name = fields.Char(string="Luca Name", required=False, tracking=True)
    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Contact', required=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_sale_tax_invoice_number = fields.Char(
        string="Taraz Invoice#",
        compute="generate_invoice_number",
        store=True, tracking=True, readonly=False,
    )

    x_product_id = fields.Many2one('product.product', related='invoice_line_ids.product_id', string='Product',
                                   readonly=False)
    x_analytic_account_id = fields.Many2one(related='invoice_line_ids.analytic_account_id', string="Analytic Account")
    x_analytic_tag_ids = fields.Many2many(related='invoice_line_ids.analytic_tag_ids', string="Analytic Tags")
    # ---------------------------------------------------------------------------------
    # ---------------------------- Invoice Customizations -----------------------------
    # ---------------------------------------------------------------------------------
    x_customer_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    help="Delivery address for current invoice.")
    x_end_user_id = fields.Many2one('res.partner', string='End user', readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    help="Delivery address for current invoice.")
    x_update_partner_data = fields.Boolean(compute="_compute_partner_products_and_status")
    x_web_order_number = fields.Char(string="WEB Order#", required=False, )
    x_sale_order = fields.Many2one(comodel_name="sale.order", string="Sale Order#", required=False, )
    x_so_payment_state = fields.Boolean(compute="_compute_so_payment_state")
    x_so_pt_id = fields.Many2one(comodel_name="account.payment.term", string="SO Payment Terms", required=False,
                                 related="x_sale_order.payment_term_id")
    x_payment_method = fields.Many2one(comodel_name="account.journal", string="Payment Method", required=False, )
    x_sale_type = fields.Selection(selection=[
        ('Investment', 'Investment'),
        ('Export / WeBoc', 'Export / WeBoc [EG]'),
        ('Export / Speedy', 'Export / Speedy [ES]'),
        ('Export / Services', 'Export / Services [ES]'),
        ('Domestic / Unofficial', 'Domestic / Unofficial [DU]'),
        ('Domestic Goods / Official', 'Domestic Goods / Official [DG]'),
        ('Domestic Services / Official', 'Domestic Services / Official [DS]'),
        ('Internal / Employee', 'Internal / Employee [IE]'),
    ], string="Sale Type", tracking=True, required=False, )
    x_sale_type_turkey = fields.Selection(selection=[
        ('export', 'Export'),
        ('domestic', 'Domestic'),
        ('dropship_av', 'Dropship AV'),
        ('dropship_uv', 'Dropship UV'),
        ('cbm_av', 'CBM AV'),
        ('cbm_uv', 'CBM UV'),
    ], string="Sale Type (TR)", tracking=True)
    x_gst_return_filed = fields.Selection(selection=[
        ('Yes', 'Yes'),
        ('No', 'No'),
    ], string="GST Returned Filed?", required=True, default='No', tracking=True)
    x_export = fields.Selection(string="Export?", selection=[('Actual', 'Actual'), ('UI', 'UI'), ('No', 'No'), ], required=False, tracking=True)
    x_comments = fields.Char(string="Comments", required=False, )
    x_delivery_method = fields.Many2one(comodel_name="delivery.carrier", string="Delivery Method", required=False, )
    x_registered_payments = fields.Text(string="Registered Payment(s)", required=False, compute="_update_registered_payments", store=True, )
    x_tracking_reference = fields.Char(string="Tracking Reference", required=False, )
    x_exclude_from_dashboard = fields.Selection(string="Exclude From DSHBD?", selection=[('Yes', 'Yes'), ('No', 'No'), ], required=False, )
    x_date_dashboard = fields.Date(string='Dashboard Date', required=False)
    x_fiscal_year = fields.Char(string="Fiscal Year", required=False, compute="calculate_fiscal_year", store=True)
    x_old_number = fields.Char(string="Old Number", tracking=True, required=False, )
    x_is_invoice = fields.Boolean(string='Show Invoice# Text?', required=False)
    x_invoice_docs_number = fields.Char(string='Invoice Docs. Number', compute="_compute_invoice_docs_number", store=True, )

    @api.depends('state', 'name', 'x_is_invoice', 'company_id', 'type')
    def _compute_invoice_docs_number(self):
        for rec in self:
            if (rec.type not in ['out_invoice', 'out_refund', 'out_receipt']
                    and rec.company_id.id == 1 and rec.state != 'posted'):
                return False
            if rec.x_is_invoice:
                rec.x_invoice_docs_number = rec.name[1:]
            else:
                rec.x_invoice_docs_number = rec.name

    # ---------------------------- Invoice Tab ----------------------------
    x_show_bill_to = fields.Boolean(string="Show Bill To", default=True)
    x_show_customer = fields.Boolean(string="Show Customer", )
    x_hide_customer = fields.Boolean(string="Hide Customer?", )
    x_hide_product = fields.Boolean(string="Hide Product?", )
    x_hide_discount = fields.Boolean(string="Hide Discount?", )
    x_hide_gst = fields.Boolean(string="Hide GST?", )
    x_letter_head_report = fields.Boolean(string="Letter Head Report?", )
    x_partial_weboc = fields.Boolean(string="Partial WeBoc?", )
    x_show_first_invoice = fields.Boolean(string="Show First Invoice#", default=True)

    x_show_ship_to = fields.Boolean(string="Show Ship To", default=True)
    x_show_end_user = fields.Boolean(string="Show End-User", )
    x_attach_short_terms = fields.Boolean(string="Show T&C Remark?", )
    x_attach_long_terms = fields.Boolean(string="Attach T&C?", )
    x_hs_code_and_coo = fields.Boolean(string="HS Code & COO?", )
    x_distributor_order = fields.Boolean(string="Distributor Desc.?", )
    x_appear_taraz_invoice_number = fields.Boolean(string="Show Taraz Invoice#?", )
    x_appear_payment_method = fields.Boolean(string="Payment Method?", compute="_update_payment_status", store=True, readonly=False, )
    x_invoice_id = fields.Many2one(comodel_name='account.move', string='First Invoice', readonly=False, store=True,
                                   domain="[('type', 'in', ('out_invoice', 'out_refund', 'out_receipt'))]", compute="_get_first_invoice")

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.date:
                rec.x_date_dashboard = rec.date
        return res

    def open_record(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_id': rec.id,
            }

    @api.depends('x_show_first_invoice')
    def _get_first_invoice(self):
        for rec in self:
            if rec.x_show_first_invoice and rec.x_sale_order.invoice_ids.filtered(lambda l: l.state == 'posted'):
                rec.x_invoice_id = min(rec.x_sale_order.invoice_ids.filtered(lambda l: l.state == 'posted').ids)
            else:
                rec.x_invoice_id = False

    x_invoice_lines = fields.One2many(
        'invoice.lines', 'invoice_id', string='Banking Invoice Lines',
        compute="update_invoice_data", store=True, readonly=False
    )
    # x_compute_invoice_lines = fields.Boolean(compute="update_invoice_data")
    x_amount_untaxed = fields.Monetary(string='Untaxed Amount (Invoice)', store=True, readonly=True, tracking=True,
                                       compute='compute_amount')
    x_amount_tax = fields.Monetary(string='Tax (Invoice)', store=True, readonly=True, compute='compute_amount')
    x_amount_gst = fields.Monetary(string='GST (Invoice)', store=True, readonly=True, compute='compute_amount')
    x_amount_gst_withheld = fields.Monetary(string='GST Withheld (Invoice)', store=True, readonly=True, compute='compute_amount')
    x_amount_it_withheld = fields.Monetary(string='IT Withheld (Invoice)', store=True, readonly=True, compute='compute_amount')
    x_amount_total = fields.Monetary(string='Total (Invoice)', store=True, readonly=True, compute='compute_amount')
    x_amount_residual = fields.Monetary(string='Amount Due (Invoice)', store=True, compute='compute_amount')
    x_amount_receivable = fields.Monetary(string='Amount Receivable (Invoice)', store=True, compute='compute_amount')
    x_amount_by_group = fields.Binary(string="Tax amount by group (Invoice)", compute='_compute_invoice_taxes_by_group')
    x_invoice_payments_widget = fields.Text(groups="account.group_account_invoice", compute='compute_amount', store=True)

    x_appear_pt_table = fields.Boolean(string="SO Payment Terms Table?", compute="compute_payment_term_table",
                                       store=True, readonly=False, )
    x_appear_paypal_link = fields.Boolean(string="Show Paypal Link?", )
    x_appear_banking_details = fields.Boolean(string="Show Banking Details?", )
    x_bank = fields.Many2one(comodel_name="payment.acquirer", string="Payment Acquirer",
                             compute="_update_payment_acquirer", store=True, readonly=False, )

    x_hide_payable = fields.Boolean(string="Hide Payable?", )
    x_appear_gst_withheld = fields.Boolean(string="Show GST Withheld?", )
    x_appear_it_withheld = fields.Boolean(string="Show IT Withheld?", )
    x_with_payments = fields.Boolean(string="With Payments?", compute="_update_payment_status", store=True,
                                     readonly=False, )
    x_payment_number = fields.Selection(selection=[
        ('payment_1', 'Payment 1'), ('payment_2', 'Payment 2'), ('payment_3', 'Payment 3'), ('payment_4', 'Payment 4'),
        ('payment_5', 'Payment 5'), ('payment_6', 'Payment 6'), ('payment_7', 'Payment 7'), ('payment_8', 'Payment 8'),
        ('payment_9', 'Payment 9'),
    ], required=False, string="Payment#", )

    x_remarks = fields.Text(string="Remarks", required=False, )
    # ---------------------------- Sale Tax Invoice Tab ----------------------------
    x_hide_sti_product = fields.Boolean(string="Hide Product?", default=True, )
    x_hide_sti_description = fields.Boolean(string="Hide Description", )
    x_hide_sti_remarks = fields.Boolean(string="Hide Remarks", default=True, )
    x_hide_sti_gst_breakup = fields.Boolean(string="Hide GST Breakup", )
    x_hide_sti_total_breakup = fields.Boolean(string="Hide Total Breakup", )
    x_sti_date = fields.Date(string='ST Invoice Date', compute="_get_invoice_date", store=True, readonly=False)
    x_sti_remarks = fields.Text(string="ST Invoice Remarks", required=False, )
    x_sale_tax_invoice_line_ids = fields.One2many(comodel_name="sale.tax.invoice.lines", inverse_name="invoice_id",
                                                  string="Sale Tax Invoice Lines", required=False, )
    # ---------------------------------------------------------------------------------
    # ------------------------------ Bill Customizations ------------------------------
    # ---------------------------------------------------------------------------------
    x_purchase_type = fields.Selection(selection=[
        ('Local', 'Local'), ('Foreign', 'Foreign'), ('Clearing', 'Clearing'), ('Investment', 'Investment'),
        ('Forwarding', 'Forwarding'), ('Imported Goods', 'Imported Goods'), ('Shipping (Export)', 'Shipping (Export)'),
        ('Shipping (Self Pickup)', 'Shipping (Self Pickup)'),
    ], required=False, string="Purchase Type", )
    x_item_type = fields.Selection(selection=[
        ('Tax', 'Tax'), ('Asset', 'Asset'), ('Medical', 'Medical'), ('Expense', 'Expense'), ('Inventory', 'Inventory'),
        ('Landed Cost', 'Landed Cost'), ('Investment Profit', 'Investment Profit'), ('Residence', 'Residence'),
        ('Inventory & Asset', 'Inventory & Asset'), ('Investment Return', 'Investment Return'),
        ('Cost of Freight Sold', 'Cost of Freight Sold'),
    ], required=False, string="Item Type", )
    x_import_method = fields.Selection(selection=[('WeBoc', 'WeBoc'), ('Speedy', 'Speedy'), ], string="Import Method", required=False, )
    x_related_po_s = fields.Many2many(comodel_name="purchase.order", relation="account_move_purchase_order_rel_1",
                                      column1="account_move_id", column2="purchase_order_id", string="Related PO(s)", )
    x_related_so_s = fields.Many2many(comodel_name="sale.order", relation="account_move_sale_order_rel_1",
                                      column1="account_move_id", column2="sale_order_id", string="Related Exp SO(s)", )
    x_weboc_gd = fields.Char(string="WeBoc GD#", required=False, )
    x_assessed_value = fields.Float(string="Assessed Value (Rs.)", required=False, )
    x_employee = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    x_medical_bill_type = fields.Selection(selection=[('consultancy', 'Consultancy'), ('medicine', 'Medicine'), ],
                                           string="Medical Bill Type", required=False, )
    x_relation = fields.Selection(selection=[
        ('Self', 'Self'), ('Father', 'Father'), ('Mother', 'Mother'), ('Husband', 'Husband'), ('Wife', 'Wife'),
        ('Son', 'Son'), ('Daughter', 'Daughter'),
    ], string="Relation", required=False, )
    x_support_doc = fields.Binary(string="Support Doc.", copy=False, )

    x_landed_cost_line_exist = fields.Boolean(string='Landed Cost Line Exist', compute='_landed_cost_line_exist', store=True)
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')
    x_medical_limit_exceed = fields.Boolean(compute="_compute_medical_limit_exceed")

    @api.depends('invoice_line_ids', 'invoice_line_ids.is_landed_costs_line')
    def _landed_cost_line_exist(self):
        for account_move in self:
            if account_move.landed_costs_ids:
                account_move.x_landed_cost_line_exist = False
            else:
                account_move.x_landed_cost_line_exist = any(line.is_landed_costs_line for line in account_move.invoice_line_ids)

    def employee_medical_expenses_for_current_year(self):
        for rec in self:
            # Calculate total medical expenses for the year
            current_year = str(fields.Date.today().year)  # Get current year
            medical_expenses = self.env['account.move'].search([
                ('x_employee', '=', rec.x_employee.id),
                ('invoice_date', '>=', current_year + '-01-01'),  # From beginning of year
                ('invoice_date', '<=', current_year + '-12-31'),  # To end of year
                ('x_item_type', '=', 'Medical'),
                ('state', '=', 'posted'),
            ]).mapped('amount_total')
            return sum(medical_expenses) if medical_expenses else 0

    @api.depends('amount_total', 'x_employee', 'state')
    def _compute_medical_limit_exceed(self):
        for rec in self:
            medical_expenses = rec.employee_medical_expenses_for_current_year()
            rec.x_medical_limit_exceed = True if medical_expenses > 30000 else False

    # @api.onchange('x_employee')
    # def _onchange_employee(self):
    #     if self.x_employee:
    #         self.invoice_line_ids = [(5, 0, 0)]
    #         total_expenses = self.employee_medical_expenses_for_current_year()
    #         price_unit = 30000 - total_expenses
    #         self.invoice_line_ids = [(0, 0, {
    #                 'product_id': 15429,
    #                 'account_id': 648,
    #                 'quantity': 1,
    #                 'price_unit': price_unit / 0.75,
    #                 'discount': 25,
    #                 'price_subtotal': price_unit,
    #             })]
    #         self._onchange_invoice_line_ids()
    #
    # @api.model
    # def copy(self, default=None):
    #     default = {}
    #     copied_record = super(AccountMove, self).copy(default=default)
    #     copied_record._onchange_employee()
    #     return copied_record

    @api.depends('invoice_payment_state')
    def _compute_so_payment_state(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)
            if order_id:
                invoice_payment_states = self.env['account.move'].search([
                    ('invoice_origin', '=', rec.invoice_origin)
                ]).mapped('invoice_payment_state')

                if all(status == 'paid' for status in invoice_payment_states):
                    order_id.x_so_payment_state = 'paid'
                elif all(status == 'not_paid' for status in invoice_payment_states):
                    order_id.x_so_payment_state = 'not_paid'
                elif any(status == 'paid' for status in invoice_payment_states):
                    order_id.x_so_payment_state = 'in_payment'
            rec.x_so_payment_state = True

    @api.depends('invoice_date')
    def _get_invoice_date(self):
        for rec in self:
            rec.x_sti_date = rec.invoice_date

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search([('x_sale_tax_invoice_number', operator, name)] + args, limit=limit)
        if not recs.ids:
            return super(AccountMove, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return recs.name_get()

    def action_invoice_sent(self):
        self._update_payment_status()
        res = super(AccountMove, self).action_invoice_sent()
        return res

    def _update_so_cgs_lines(self):
        for rec in self:
            if rec.type == "out_invoice":
                if rec.x_sale_order:
                    rec.x_sale_order.get_settings()
                elif rec.invoice_origin:
                    sale_order_id = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
                    rec.x_sale_order = sale_order_id.id if sale_order_id else False
                    if rec.x_sale_order:
                        rec.x_sale_order.get_settings()
            elif rec.type == "in_invoice":
                for sale_order in rec.x_related_so_s:
                    sale_order.get_settings()

    def _get_payments(self):
        for rec in self:
            invoice_payments = []
            for invoice in rec.x_sale_order.invoice_ids:
                if invoice.invoice_date and rec.invoice_date:
                    if invoice.invoice_date <= rec.invoice_date:
                        for payments in invoice._get_reconciled_info_JSON_values():
                            invoice_payments.append(payments)
            return invoice_payments

    def _get_move_display_name(self, show_ref=False):
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        if self.x_appear_taraz_invoice_number and self.company_id.id == 1:
            draft_name = self.x_sale_tax_invoice_number
        elif self.x_sale_tax_invoice_number and self.company_id.id == 1:
            if 'FY' in self.x_sale_tax_invoice_number:
                draft_name = self.x_sale_tax_invoice_number
        return (draft_name or self.name) + (
                show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

    def _get_report_base_filename(self):
        if any(not move.is_invoice() for move in self):
            raise UserError(_("Only invoices could be printed."))
        return self._get_move_display_name()

    def unlink(self):
        for move in self:
            if move.name != '/' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete an entry which has been posted once."))
            elif move.x_sale_tax_invoice_number and move.x_sale_tax_invoice_number != '/':
                raise UserError(_("You cannot delete an invoice which has Invoice#."))
            move.line_ids.unlink()
        return super(AccountMove, self).unlink()

    def on_change_invoice_line_ids(self):
        for rec in self:
            rec.x_sale_tax_invoice_line_ids = [(2, line.id) for line in rec.x_sale_tax_invoice_line_ids]
            sale_tax_invoice_line_ids = []
            for line in rec.invoice_line_ids:
                sale_tax_invoice_line_ids.append((0, 0, {
                    'invoice_id': rec.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': line.tax_ids.ids,
                    'price_subtotal': line.price_subtotal,
                }))
            rec.x_sale_tax_invoice_line_ids = sale_tax_invoice_line_ids

    @api.depends('x_sale_order', 'x_sale_order.order_line')
    def update_invoice_data(self):
        for record in self:
            record.x_invoice_lines = [(2, line.id) for line in record.x_invoice_lines]
            if record.x_sale_order:
                record.x_total_amount = 0
                invoice_lines = []
                for line in record.x_sale_order.order_line:
                    product = line.product_id.name
                    if product:
                        if 'Down Payment' not in product and 'BOS' not in product and 'PACKING' not in product:
                            invoice_lines.append((0, 0, {
                                'invoice_id': record.id,
                                'product_id': line.product_id.id,
                                'name': line.name,
                                'quantity': line.product_uom_qty,
                                'product_uom_id': line.product_uom.id,
                                'unit_price': line.price_unit,
                                'discount': line.discount,
                                'tax_ids': line.tax_id,
                                'price_subtotal': line.price_subtotal,
                            }))
                            record.x_total_amount += line.price_subtotal
                record.x_invoice_lines = invoice_lines
            elif record.type in ('out_invoice', 'out_refund', 'out_receipt'):
                record.x_total_amount = 0
                invoice_lines = []
                for line in record.invoice_line_ids:
                    product = line.product_id.name
                    if product:
                        if 'Down Payment' not in product and 'BOS' not in product and 'PACKING' not in product:
                            invoice_lines.append((0, 0, {
                                'invoice_id': record.id,
                                'product_id': line.product_id.id,
                                'name': line.name,
                                'quantity': line.quantity,
                                'product_uom_id': line.product_uom_id.id,
                                'unit_price': line.price_unit,
                                'discount': line.discount,
                                'tax_ids': [(6, 0, line.tax_ids.ids)],
                                'price_subtotal': line.price_subtotal,
                            }))
                            record.x_total_amount += line.price_subtotal
                record.x_invoice_lines = invoice_lines
            # record.x_compute_invoice_lines = True

    @api.depends('x_payment_method', 'x_sale_type', 'type')
    def _update_payment_acquirer(self):
        for rec in self:
            payment_acquirer_id = False
            if (
                    rec.x_sale_type != 'Investment'
                    and rec.type in ['out_invoice', 'out_refund', 'out_receipt']
                    and rec.x_payment_method
            ):
                payment_acquirer_id = self.env['payment.acquirer'].search(
                    [('journal_id', '=', rec.x_payment_method.id)], limit=1).id
            rec.x_bank = payment_acquirer_id if payment_acquirer_id else False

    @api.depends('invoice_payment_state', 'x_registered_payments', 'x_payment_method', 'currency_id', 'x_sale_type',
                 'type')
    def _update_payment_status(self):
        for rec in self:
            if rec.x_sale_type != 'Investment' and rec.type in ['out_invoice', 'out_refund', 'out_receipt']:
                rec.x_with_payments = True if rec.invoice_payment_state in ['paid', 'in_payment'] else False
                rec.x_with_payments = True if rec.x_registered_payments else False
                rec.x_appear_payment_method = False
                if rec.x_registered_payments:
                    sign_count = rec.x_registered_payments.count(rec.currency_id.symbol)
                    journal_names = self.env['account.journal'].search([]).mapped('name')
                    journal_count = 0
                    for journal_name in journal_names:
                        journal_count = rec.x_registered_payments.count(journal_name)
                        if journal_count != 0:
                            break
                    if sign_count == journal_count:
                        rec.x_appear_payment_method = True

    @api.depends('invoice_line_ids', 'state', 'x_customer_id', 'partner_id', 'partner_shipping_id', 'x_end_user_id')
    def _compute_partner_products_and_status(self):
        for rec in self:
            if rec.type == 'out_invoice':
                if rec.x_customer_id.id == rec.partner_id.id == rec.partner_shipping_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_id.id == rec.partner_shipping_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_shipping_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                elif rec.partner_id.id == rec.partner_shipping_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_id.id and rec.partner_shipping_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_shipping_id.id and rec.partner_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                elif rec.x_customer_id.id == rec.x_end_user_id.id and rec.partner_shipping_id.id == rec.partner_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id.parent_id)
                elif rec.x_customer_id.id == rec.partner_shipping_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id.parent_id)
                elif rec.x_customer_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                elif rec.partner_id.id == rec.partner_shipping_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id.parent_id)
                elif rec.partner_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                elif rec.partner_shipping_id.id == rec.x_end_user_id.id:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                else:
                    rec.x_sale_order.update_partner(rec.x_customer_id)
                    rec.x_sale_order.update_partner(rec.x_customer_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_id)
                    rec.x_sale_order.update_partner(rec.partner_id.parent_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id)
                    rec.x_sale_order.update_partner(rec.partner_shipping_id.parent_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id)
                    rec.x_sale_order.update_partner(rec.x_end_user_id.parent_id)
            rec.x_update_partner_data = True

    @api.depends('name', 'state', 'x_sale_tax_invoice_number', 'x_appear_taraz_invoice_number')
    def name_get(self):
        result = []
        for move in self:
            if self._context.get('name_groupby'):
                name = '**%s**, %s' % (format_date(self.env, move.date), move._get_move_display_name())
                if move.ref:
                    name += '     (%s)' % move.ref
                if move.partner_id.name:
                    name += ' - %s' % move.partner_id.name
            else:
                name = move._get_move_display_name(show_ref=True)
            result.append((move.id, name))
        return result

    @api.depends('invoice_payment_term_id', 'x_invoice_lines')
    def compute_payment_term_table(self):
        for rec in self:
            terms_count = len(rec.invoice_payment_term_id.line_ids)
            if terms_count <= 1:
                rec.x_appear_pt_table = False
            else:
                rec.x_appear_pt_table = True

    @api.depends('invoice_origin')
    def update_sale_order_number(self):
        for rec in self:
            if not rec.x_sale_order and rec.invoice_origin:
                rec.x_sale_order = self.env['sale.order'].search([('name', '=', rec.invoice_origin)]).id

    @api.depends('invoice_date')
    def calculate_fiscal_year(self):
        for record in self:
            if record.invoice_date and record.company_id.id == 1:
                date = record.invoice_date
                month = date.month
                if month > 6:
                    record.x_fiscal_year = str(date.year) + '-' + str(date.year + 1)
                elif month < 7:
                    record.x_fiscal_year = str(date.year - 1) + '-' + str(date.year)
            elif record.invoice_date and record.company_id.id == 2:
                date = record.invoice_date
                record.x_fiscal_year = str(date.year)

    @api.depends('x_invoice_lines', 'x_registered_payments')
    def compute_amount(self):
        for move in self:
            total_untaxed = sum(move.x_invoice_lines.mapped('price_subtotal'))
            total_gst = 0.0
            total_gst_withheld = 0.0
            total_it_withheld = 0.0
            total = 0.0

            for line in move.x_invoice_lines:
                # Taxes.
                for tax in line.tax_ids:
                    if tax.amount_type == 'percent':
                        if tax.tax_group_id.name == 'GST':
                            total_gst += round(line.price_subtotal * tax.amount / 100, 2)
                        elif tax.tax_group_id.name == 'GST Withheld':
                            total_gst_withheld += round(line.price_subtotal * tax.amount / 100, 2)
                        elif tax.tax_group_id.name == 'IT Withheld':
                            total_it_withheld += round(line.price_subtotal * tax.amount / 100, 2)
                    elif tax.amount_type == 'group':
                        for child_tax in tax.children_tax_ids:
                            if child_tax.amount_type == 'percent':
                                if child_tax.tax_group_id.name == 'GST':
                                    total_gst += round(line.price_subtotal * child_tax.amount / 100, 2)
                                elif child_tax.tax_group_id.name == 'GST Withheld':
                                    total_gst_withheld += round(line.price_subtotal * child_tax.amount / 100, 2)
                                elif child_tax.tax_group_id.name == 'IT Withheld':
                                    total_it_withheld += round(line.price_subtotal * child_tax.amount / 100, 2)
            # Total Amount.
            total += total_untaxed + total_gst + total_gst_withheld + total_it_withheld

            invoice_total = 0.0
            invoice_total_currency = 0.0
            total_receivable = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)
                if move.is_invoice(include_receipts=True):
                    if line.account_id.user_type_id.type in ('receivable', 'payable'):
                        total_receivable += line.amount_currency if line.currency_id else line.balance

            for invoice in move.x_sale_order.invoice_ids:
                if invoice.invoice_date and move.invoice_date:
                    if invoice.invoice_date <= move.invoice_date:
                        for line in invoice.line_ids:
                            if line.currency_id:
                                currencies.add(line.currency_id)
                            if move.is_invoice(include_receipts=True):
                                if not line.exclude_from_invoice_tab:
                                    invoice_total += line.balance
                                    invoice_total_currency += line.amount_currency
                                elif line.tax_line_id:
                                    invoice_total += line.balance
                                    invoice_total_currency += line.amount_currency
                                elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                                    total_residual += line.amount_residual
                                    total_residual_currency += line.amount_residual_currency
                            else:
                                if line.debit:
                                    invoice_total += line.balance
                                    invoice_total_currency += line.amount_currency

            sign = 1 if move.type == 'entry' or move.is_outbound() else -1

            invoice_total = sign * (invoice_total_currency if len(currencies) == 1 else invoice_total)
            total_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)

            move.update({
                'x_amount_untaxed': total_untaxed,
                'x_amount_tax': total_gst,
                'x_amount_gst': total_gst,
                'x_amount_gst_withheld': total_gst_withheld,
                'x_amount_it_withheld': total_it_withheld,
                'x_amount_total': total,
                'x_amount_residual': total_residual + total - invoice_total,
                'x_amount_receivable': total_receivable,
            })

            if move.state != 'posted' or not move.is_invoice(include_receipts=True):
                move.x_invoice_payments_widget = json.dumps(False)
                continue
            reconciled_vals = move._get_payments()
            if reconciled_vals:
                info = {
                    'title': _('Less Payment'),
                    'outstanding': False,
                    'content': reconciled_vals,
                }
                move.x_invoice_payments_widget = json.dumps(info, default=date_utils.json_default)
            else:
                move.x_invoice_payments_widget = json.dumps(False)

    @api.depends('invoice_payments_widget')
    def _update_registered_payments(self):
        for rec in self:
            payment_text = ''
            payments = rec._get_reconciled_info_JSON_values()
            for payment in payments:
                payment_text += '[%s, %s, %s, %s]\n' % (payment['journal_name'], payment['currency'],
                                                        round(payment['amount'], 2), payment['date'])
            rec.x_registered_payments = payment_text

    @api.depends('x_sale_type', 'invoice_date', 'x_appear_taraz_invoice_number', 'x_old_number')
    def generate_invoice_number(self):
        for rec in self:
            if rec.x_old_number:
                rec.x_sale_tax_invoice_number = rec.x_old_number
            elif rec.name == '/': # if Invoice # is assigned then don't change Taraz Invoice #
                rec.x_sale_tax_invoice_number = rec.generate_st_invoice_number(
                    rec.x_sale_type, rec.invoice_date, rec._origin.id, rec.company_id.id
                )
            else:
                rec.x_sale_tax_invoice_number = rec.x_sale_tax_invoice_number

    def generate_st_invoice_number(self, sale_type, invoice_date, res_id, company_id):
        if sale_type and invoice_date:
            invoice_month = invoice_date.month
            min_year = invoice_date.year if invoice_month > 6 else invoice_date.year - 1
            max_year = invoice_date.year + 1 if invoice_month > 6 else invoice_date.year
            min_date = datetime.date(min_year, 7, 1)
            max_date = datetime.date(max_year, 6, 30)
            prefix = 'FY' + str(min_date.year)[-2:] + str(max_date.year)[-2:] + '-'

            if sale_type == "Export / WeBoc":
                suffix_code = "-EG"
            elif sale_type == "Export / Speedy":
                suffix_code = "-ES"
            elif sale_type == "Export / Services":
                suffix_code = "-ES"
            elif sale_type == "Domestic / Unofficial":
                suffix_code = "-DU"
            elif sale_type == "Domestic Goods / Official":
                suffix_code = "-DG"
            elif sale_type == "Domestic Services / Official":
                suffix_code = "-DS"
            elif sale_type == "Internal / Employee":
                suffix_code = "-IE"
            elif sale_type == "Investment":
                suffix_code = "-INV"
            else:
                suffix_code = ""

            invoice_ids = self.env['account.move'].search([
                ('invoice_date', '>=', min_date), ('invoice_date', '<=', max_date),
                ('x_sale_type', '=', sale_type), ('company_id', '=', company_id), ('id', '!=', res_id),
            ])
            invoice_nums = set(int(number.split('-')[1]) for number in invoice_ids.mapped('x_sale_tax_invoice_number') if number and number != '/')
            n = len(invoice_nums) + 1
            all_invoice_nums = set(range(1, n))
            if all_invoice_nums - invoice_nums:
                invoice_num = ('00' + str(min(all_invoice_nums - invoice_nums)))[-3:]
            else:
                invoice_num = ('00' + str(n))[-3:]
            sale_tax_invoice_number = prefix + invoice_num + suffix_code

            return sale_tax_invoice_number
        else:
            return False

    @api.onchange('x_bank')
    def get_bank_details(self):
        for record in self:
            record.x_banking_details = record.x_bank.x_report_msg

    @api.onchange('x_sale_order')
    def get_sale_order_data(self):
        for record in self:
            if record.type == 'out_invoice' and record.x_sale_order:
                record.x_web_order_number = record.x_sale_order.x_web_order_number
                record.x_letter_head_report = record.x_sale_order.x_letter_head_report
                record.x_sale_type = record.x_sale_order.x_sale_type
                record.x_payment_method = record.x_sale_order.x_payment_method
                record.x_delivery_method = record.x_sale_order.carrier_id.id
                record.x_tracking_reference = record.x_sale_order.x_tracking_reference

    def button_draft(self):
        for inv in self:
            inv.x_old_number = inv.x_sale_tax_invoice_number
        return super(AccountMove, self).button_draft()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_account_tags = fields.Many2many(comodel_name="account.account.tag",
                                      relation="x_account_account_tag_account_move_line_rel",
                                      column1="account_move_line_id", column2="account_account_tag_id",
                                      string="Account Tags",
                                      related="account_id.tag_ids", ondelete='restrict', store=True, )
    x_account_type = fields.Many2one(comodel_name="account.account.type", string="Account Type", required=False,
                                     related="account_id.user_type_id", store=True, )
    x_account_group = fields.Many2one(comodel_name="account.group", string="Account Group", required=False,
                                      related='account_id.group_id', store=True, )
    x_account_group_name = fields.Char(string="Account Group Name", required=False, related="x_account_group.name",
                                       store=True, )
    x_deprecated = fields.Boolean(string="Account Deprecated", related="account_id.deprecated", store=True, )
    x_quickbooks_name = fields.Char(string="QuickBooks Name", related="account_id.x_quickbooks_name", store=True, )
    x_product_group = fields.Many2one(comodel_name="product.group", string="Product Group", required=False, )
    x_product_series = fields.Many2one(comodel_name="product.series", string="Product Series", required=False, )
    x_product_division = fields.Many2one(comodel_name="product.division", string="Product Division", required=False, )
    x_product_series_code = fields.Char(string="Product Series Code", required=False, )
    x_product_division_code = fields.Char(string="Product Division Code", required=False, )
    x_exclude_from_dashboard = fields.Selection(related="move_id.x_exclude_from_dashboard", store=True)
    x_date_dashboard = fields.Date(related="move_id.x_date_dashboard", store=True)
    x_fiscal_year = fields.Char(string="Fiscal Year", required=False, compute="calculate_fiscal_year", store=True)

    x_move_journal_id = fields.Many2one(comodel_name="account.journal", string="Journal Entry", required=False,
                                        related="move_id.journal_id")
    x_invoice_journal_id = fields.Many2one(comodel_name="account.journal", string="Journal Invoice", required=False,
                                           related="move_id.x_payment_method")

    x_payment_status = fields.Boolean(string="Payment Status", compute="_update_payment_status", store=True, readonly=False, )

    @api.depends('payment_id', 'payment_id.state')
    def _update_payment_status(self):
        for rec in self:
            rec.x_payment_status = True if rec.payment_id and rec.payment_id.state == 'reconciled' else False

    @api.onchange('product_id')
    def get_product_data(self):
        for record in self:
            if record.product_id.x_product_group:
                record.x_product_group = record.product_id.x_product_group.id
            if record.product_id.x_product_series:
                record.x_product_series = record.product_id.x_product_series.id
            if record.product_id.x_product_division:
                record.x_product_division = record.product_id.x_product_division.id
            if record.product_id.x_product_series.code:
                record.x_product_series_code = record.product_id.x_product_series.code
            if record.product_id.x_product_division.code:
                record.x_product_division_code = record.product_id.x_product_division.code

    @api.depends('date')
    def calculate_fiscal_year(self):
        for record in self:
            if record.date:
                date = record.date
                month = date.month
                if month > 6:
                    record.x_fiscal_year = str(date.year) + '-' + str(date.year + 1)
                elif month < 7:
                    record.x_fiscal_year = str(date.year - 1) + '-' + str(date.year)
