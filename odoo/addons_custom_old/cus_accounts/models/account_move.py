from odoo import fields, models, api
from odoo.exceptions import UserError

from datetime import datetime
import json
import pytz
import ast
import logging
from collections import defaultdict

_logger = logging.getLogger("*__addons_custom__*")


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_sale_ids = fields.Many2many(comodel_name='sale.order', relation="cus_sale_account_move_sale_order_rel",
                                  column1="account_move_id", column2="sale_order_id", string='Related SO(s)',
                                  domain="[('company_id', '=', company_id)]")
    x_picking_ids = fields.Many2many(comodel_name='stock.picking', string='Related ROs/DOs',
                                     relation="stock_picking_account_move_rel", column1="stock_picking_id",
                                     column2="account_move_id",
                                     domain="[('picking_type_code', 'in', ('incoming', 'outgoing')), ('company_id', '=', company_id), ]")

    x_folder_name = fields.Char(string='Folder Name', compute="_compute_folder_name", store=True)

    x_currency_rate_id = fields.Many2one(comodel_name='res.currency.rate', string='Currency Rate',
                                         compute="get_currency_rate_id", store=True,
                                         readonly=False,
                                         domain="[('currency_id', '=', currency_id), ('company_id', '=', company_id)]")
    x_rate = fields.Float(compute="get_currency_rate", store=True, readonly=False, digits=(12, 12))
    x_je_rate = fields.Float(compute="get_je_currency_rate", store=True, readonly=False, digits=(12, 12))
    x_currency_error = fields.Boolean(compute="get_currency_error", store=True)
    x_amount_total_try = fields.Float(compute="get_amount_total_try", store=True)
    x_try_currency_id = fields.Many2one(comodel_name='res.currency', string='TRY Currency', default=31)

    x_statement_line_id = fields.Many2one(
        comodel_name='account.bank.statement.line', string='Statement Line', required=False
    )
    x_document = fields.Binary(string="Doc.", tracking=True)
    x_reconciled_doc = fields.Binary(string="Reconciled Doc.", tracking=True)
    x_document_name = fields.Char(string='Doc. Name', compute="compute_file_name", store=True)
    x_get_x_customer_po = fields.Boolean(compute="get_x_customer_po", store=True)
    x_hide_paid_banner = fields.Boolean(related="journal_id.x_hide_paid_banner")

    x_create_bills = fields.Boolean(related="journal_id.x_create_bills")
    x_attach_invoices = fields.Boolean(related="journal_id.x_attach_invoices")

    x_invoice_count = fields.Integer(compute='_compute_invoice_count')
    x_related_invoice_ids = fields.Many2many(comodel_name='account.move', relation="account_move_rel_00",
                                             column1="id1", column2="id2", string='Related Invoices',
                                             domain="[('company_id', '=', company_id), ('type', '=', 'out_invoice')]")
    x_bill_count = fields.Integer(compute='_compute_bill_count')
    x_related_bill_ids = fields.Many2many(comodel_name='account.move', relation="account_move_rel_01",
                                          column1="id1", column2="id2", string='Related Invoices',
                                          domain="[('company_id', '=', company_id), ('type', '=', 'in_invoice')]")

    x_services_advance_visible = fields.Boolean(compute="transfer_services_advance_to_income", store=True)
    x_income_move_id = fields.Many2one(comodel_name='account.move', string='Income Journal Entry', required=False)

    x_income_journal_entry_state = fields.Selection([
        ('pending', 'Not a Service Bill or DOs are not validated'),
        ('normal', 'Income Journal Entry is created'),
        ('blocked', 'Income Journal Entry is not created'),
        ('done', 'Income Journal Entry is posted')
    ], string='JE', copy=False, default='pending', required=True, compute="_compute_income_journal_entry_state",
        store=True, tracking=True,
        readonly=False, help="Indicates if service advances are posted to income accounts")

    x_luca_entry_state = fields.Selection([
        ('pending', 'Luca (Not Posted)'),
        ('blocked', 'Luca (Error)'),
        ('done', 'Luca (Posted)')
    ], string='LS', copy=False, default='pending', required=True, tracking=True,
        help="Indicates if entries are posted to Luca")

    x_odoo_entry_state = fields.Selection([
        ('normal', 'Odoo (Discuss)'),
        ('blocked', 'Odoo (Error)'),
        ('done', 'Odoo (OK)')
    ], string='OS', copy=False, default='done', required=True, tracking=True)
    x_compute_odoo_status = fields.Boolean(compute="_compute_odoo_status")

    x_analytic_tag_ids = fields.Many2many(related="line_ids.analytic_tag_ids", string="Analytic Tags")
    x_product_id = fields.Many2one(related="line_ids.product_id", string="Product")
    x_name = fields.Text(related="line_ids.name", string="Label")
    x_account_id = fields.Many2one(related="line_ids.account_id", string="Account")
    x_purchase_id = fields.Many2one(comodel_name='purchase.order', compute="_compute_purchase_order", store=True)
    x_sale_line_ids = fields.Many2many(related="line_ids.sale_line_ids", string="Sale Lines")

    x_lines_partner_id = fields.Many2one(comodel_name='res.partner', string='Update Lines Partner', tracking=True)

    x_src_account_id = fields.Many2one(comodel_name='account.account', string='Source Lines Account', tracking=True)
    x_dst_account_id = fields.Many2one(comodel_name='account.account', string='Destination Lines Account',
                                       tracking=True)

    x_is_commented = fields.Boolean(string="Has Notes", compute="_compute_is_commented")

    x_freight = fields.Monetary(string="Freight", compute="_compute_freight", store=True)

    @api.depends('invoice_line_ids')
    def _compute_freight(self):
        for record in self:
            # Initialize freight value
            freight = 0.0

            # Loop through the invoice line items
            for line in record.invoice_line_ids:
                if line.product_id.id == 13813:
                    # Set the freight to the price_subtotal of the product with id 13813
                    freight = line.price_subtotal
                    break  # Exit loop once the product is found

            # Assign the computed freight value
            record.x_freight = freight

    @api.depends('narration')
    def _compute_is_commented(self):
        for record in self:
            record.x_is_commented = bool(record.narration)

    def action_show_notes(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.id,
        }

    def update_lines_account(self):
        for rec in self:
            rec.line_ids.filtered(
                lambda a: a.account_id.id == rec.x_src_account_id.id
            ).update({
                'account_id': rec.x_dst_account_id.id
            })

    def update_lines_partner(self):
        for rec in self:
            rec.line_ids.update({'partner_id': rec.x_lines_partner_id.id})

    x_move_type = fields.Selection(selection=[
        ('purchase_bill', 'Purchase Bills'),
        ('receipt_bill', 'Receipt Bills'),
        ('related_bill', 'Related Bills'),
        ('landed_cost_bill', 'Landed Cost Bills'),
        ('payment_entry', 'Payment Entries'),
        ('receipt_entry', 'Receipt Entries'),
    ], string='Move Type', compute="_compute_move_type", store=True)

    x_attachment_ids = fields.Many2many(comodel_name='ir.attachment', relation="account_move_attachment_rel",
                                        column1="account_move_id", column2="attachment_id", string='Attachments')

    x_unreported = fields.Selection(selection=[
        ('inside_fz', 'Inside FZ'), ('outside_fz', 'Outside FZ'),
    ], string='Unreported', required=False, )

    x_related_purchase_id = fields.Many2one(comodel_name='purchase.order', string='Related PO',
                                            compute="_compute_related_purchase_id", store=True)

    x_payment_status = fields.Selection(
        selection=[
            ('reconcile', 'Reconciled'),
            ('partially', 'Partially Reconciled'),
            ('unreconciled', 'Not Reconciled'),
        ],
        string='Payment Status',
        compute="_compute_payment_status",
        store=True
    )

    x_currency_warning = fields.Char(string='Currency Warning', required=False)
    x_commercial_partner = fields.Char(related='partner_id.commercial_partner_id.name', store=True)

    x_document_date_apv = fields.Date(string="Document Date")
    x_shipment_date_apv = fields.Date(string="Estimated Shipment Date")
    x_payment_term_apv = fields.Char(string="Payment Term")
    x_contact_no_apv = fields.Char(string="Contact#")
    x_signatory_apv = fields.Many2one('hr.employee', string='Signatory')
    x_products_apv = fields.Many2many('product.product', string='Products')

    x_body1_apv = fields.Html(string="Body1 (APV)", compute="compute_body1_apv", store=True)

    x_body2_apv = fields.Html(string="Body2 (APV)", compute="compute_body2_apv", store=True)

    x_body3_apv = fields.Html(string="Body3 (APV)", compute="compute_body3_apv", store=True)

    x_body4_apv = fields.Html(string="Body4 (APV)", compute="compute_body4_apv", store=True)

    x_currency_pkr_id = fields.Many2one('res.currency', string='Currency (PKR)',
                                        default=lambda self: self.env['res.currency'].search([('name', '=', 'PKR')],
                                                                                             limit=1))
    x_amount_untaxed_in_pkr = fields.Monetary(string='Untaxed Amount in PKR', store=True, readonly=True,
                                              compute='_compute_amount_untaxed_in_pkr',
                                              currency_field='x_currency_pkr_id')

    x_amount_tax_in_pkr = fields.Monetary(string='Tax in PKR', store=True, readonly=True,
                                          compute='_compute_amount_tax_in_pkr',
                                          currency_field='x_currency_pkr_id')
    x_amount_total_in_pkr = fields.Monetary(string='Total in PKR', store=True, readonly=True,
                                            compute='_compute_amount_total_in_pkr',
                                            currency_field='x_currency_pkr_id')

    x_is_attachment = fields.Boolean(string="Attachment", compute="_compute_is_attachment")

    @api.depends('x_document', 'x_reconciled_doc')
    def _compute_is_attachment(self):
        for rec in self:
            if rec.x_document or rec.x_reconciled_doc:
                rec.x_is_attachment = True
            else:
                rec.x_is_attachment = False

    @api.depends('amount_total')
    def _compute_amount_total_in_pkr(self):
        currency_pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
        for rec in self:
            if rec.amount_total < 0:
                rec.x_amount_total_in_pkr = (rec.company_currency_id._convert(abs(rec.amount_total), currency_pkr,
                                                                              rec.company_id, rec.date)) * -1
            else:
                rec.x_amount_total_in_pkr = rec.company_currency_id._convert(rec.amount_total, currency_pkr,
                                                                             rec.company_id, rec.date)

    @api.depends('amount_tax')
    def _compute_amount_tax_in_pkr(self):
        currency_pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
        for rec in self:
            if rec.amount_tax < 0:
                rec.x_amount_tax_in_pkr = (rec.company_currency_id._convert(abs(rec.amount_tax), currency_pkr,
                                                                            rec.company_id, rec.date)) * -1
            else:
                rec.x_amount_tax_in_pkr = rec.company_currency_id._convert(rec.amount_tax, currency_pkr,
                                                                           rec.company_id, rec.date)

    @api.depends('amount_untaxed')
    def _compute_amount_untaxed_in_pkr(self):
        currency_pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
        for rec in self:
            if rec.amount_untaxed < 0:
                rec.x_amount_untaxed_in_pkr = (rec.company_currency_id._convert(abs(rec.amount_untaxed), currency_pkr,
                                                                                rec.company_id, rec.date)) * -1
            else:
                rec.x_amount_untaxed_in_pkr = rec.company_currency_id._convert(rec.amount_untaxed, currency_pkr,
                                                                               rec.company_id, rec.date)

    def format_date_2(self, date):
        formatted_date = datetime.strptime(str(date), '%Y-%m-%d').strftime('%d/%m/%Y') if date else False
        return formatted_date

    def format_date(self, date):
        # Format the date
        formatted_date = datetime.strptime(str(date), '%Y-%m-%d').strftime('%B %d, %Y')
        return formatted_date

    @api.depends('x_document_date_apv', 'x_shipment_date_apv', 'x_payment_term_apv', 'x_contact_no_apv',
                 'x_signatory_apv')
    def compute_body1_apv(self):
        company_name = self.env['res.company'].browse(1).name
        for rec in self:
            if rec.type not in ('out_invoice'):
                rec.x_body1_apv = ""
                return
            rec.x_body1_apv = (f"""
                <p>
                <span style="float: right;">{self.format_date(rec.x_document_date_apv) if rec.x_document_date_apv else False}</span><br>
                The Manager<br>
                Bank Alfalah Limited<br>
                IBG Trade Hub North<br>
                Rawalpindi<br>
                <br><br>
                <b><u>SUBJECT: APV DOCUMENT AGAINST INVOICE # {rec.x_sale_tax_invoice_number if rec.x_sale_tax_invoice_number else rec.name} 
                ({rec.x_sale_order.name if rec.x_sale_order.name else rec.x_web_order_number})</b><br><br>
                Dear Sir,<br><br>
                APV documents are attached. Kindly process & credit our A/C.
                <br><br>
                Furthermore, the Credit Advice should be mailed at the earliest.
                <br><br>
                Regards<br>
                <br><br><br><br><br>
                ({rec.x_signatory_apv.name})<br>
                {rec.x_signatory_apv.x_job_title_id.x_name}<br>
                {company_name}<br>
                {rec.x_contact_no_apv}
                </p>
            """)

    @api.depends('x_document_date_apv', 'x_shipment_date_apv', 'x_payment_term_apv', 'x_contact_no_apv',
                 'x_signatory_apv')
    def compute_body2_apv(self):
        company_name = self.env['res.company'].browse(1).name
        for rec in self:
            if rec.type not in ('out_invoice'):
                rec.x_body2_apv = ""
                return
            rec.x_body2_apv = (f"""
                <p>
                <span style="float: right;">{self.format_date(rec.x_document_date_apv) if rec.x_document_date_apv else False}</span><br>
                The Manager<br>
                Trade Department<br>
                Bank Alfalah<br>
                Rawalpindi<br>
                <br><br>
                <b>SUBJECT: RECEIPT OF US$ {rec.amount_total}  AS {rec.x_payment_term_apv.upper() if rec.x_payment_term_apv else False} AMOUNT FROM 
                {rec.partner_id.commercial_partner_id.name.upper() if rec.partner_id.commercial_partner_id.name else False} 
                AGAINST INVOICE # {rec.x_sale_tax_invoice_number if rec.x_sale_tax_invoice_number else rec.name} ({rec.x_sale_order.name if rec.x_sale_order.name else rec.x_web_order_number})</b>
                <br><br>
                <b>END-USE OF THE PRODUCTS:</b>
                <br><br>
                Items as per attached Invoice # {rec.x_sale_tax_invoice_number if rec.x_sale_tax_invoice_number else rec.name} ({rec.x_sale_order.name if rec.x_sale_order.name else rec.x_web_order_number})<br>
                <br>
                Products to be shipped are used in the Research Labs & Universities.<br>
                Regards<br>
                <br><br><br><br><br>
                ({rec.x_signatory_apv.name})<br>
                {rec.x_signatory_apv.x_job_title_id.x_name}<br>
                {company_name}<br>
                {rec.x_contact_no_apv}
                </p>
            """)

    def generate_invoice_table(self, record):
        # This will store the merged data by HS code
        product_data = defaultdict(lambda: {
            'description': [],
            'quantity': 0,
            'value': 0.0,
            'coo': '',
        })

        # Sum of all line values (excluding freight)
        total_value = 0.0

        # Freight-related information
        freight_value = 0.0
        freight_product_id = 13813  # ID of the freight product

        # Process each product line
        for line in record.x_invoice_lines:
            product = line.product_id
            hs_code = product.dk_hs_code.x_hs_code if product.dk_hs_code else "N/A"  # Use "N/A" if HS code is missing
            quantity = line.quantity
            line_value = line.price_subtotal

            # Check if the product is freight (do not include it in the table)
            if product.id == freight_product_id:
                freight_value = line_value  # Record the freight value
                continue  # Skip adding freight product to the table

            total_value += line_value  # Sum the total value of non-freight products

            # Add product information to the product_data dictionary
            product_data[hs_code]['description'].append(product.name)
            product_data[hs_code]['quantity'] += quantity
            product_data[hs_code]['value'] += line_value
            product_data[hs_code][
                'coo'] = product.x_country_id.name if product.x_country_id else "N/A"  # COO (Country of Origin)

        # Adjust freight value proportionally across the product lines
        for hs_code, data in product_data.items():
            # Calculate proportional freight for this line
            proportional_freight = (data['value'] / total_value) * freight_value
            data['value'] += proportional_freight

        # Generate the HTML table dynamically
        html_table = f"""
        <table style="border: 1px solid black; text-align: center;" width="100%">
            <thead>
                <tr style="border: 1px solid black;">
                    <th style="border: 1px solid black;">SO #</th>
                    <th style="border: 1px solid black;">Invoice #</th>
                    <th style="border: 1px solid black;">Incoterm</th>
                    <th style="border: 1px solid black;">HS Codes</th>
                    <th style="border: 1px solid black;">Description</th>
                    <th style="border: 1px solid black;">QTY</th>
                    <th style="border: 1px solid black;">COO</th>
                    <th style="border: 1px solid black;">Item Value (USD)</th>
                    <th style="border: 1px solid black;">Invoice Value (USD)</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border: 1px solid black;">
                    <td rowspan="{len(product_data)}" style="border: 1px solid black; vertical-align: middle;"><b>{record.x_sale_order.name if record.x_sale_order.name else record.x_web_order_number}</b></td>
                    <td rowspan="{len(product_data)}" style="border: 1px solid black; vertical-align: middle;">{record.x_sale_tax_invoice_number if record.x_sale_tax_invoice_number else record.name}</td>
                    <td rowspan="{len(product_data)}" style="border: 1px solid black; vertical-align: middle;">{record.invoice_incoterm_id.name}</td>
        """

        # Populate the table rows with product data
        first_row = True
        for hs_code, data in product_data.items():
            description = ", ".join(data['description'])  # Combine descriptions for same HS code
            row = ""
            if first_row:
                # Add the final Invoice Value cell only once
                row += f"""
                <td style="border: 1px solid black;">{hs_code}</td>
                <td style="border: 1px solid black;">{description}</td>
                <td style="border: 1px solid black;">{data['quantity']}</td>
                <td style="border: 1px solid black;">{data['coo']}</td>
                <td style="border: 1px solid black;">${data['value']:.2f}</td>
                <td rowspan="{len(product_data)}" style="border: 1px solid black; vertical-align: middle;">${total_value + freight_value:.2f}</td>
                </tr>
                """
                first_row = False
            else:
                row += f"""
                <tr style="border: 1px solid black;">
                    <td style="border: 1px solid black;">{hs_code}</td>
                    <td style="border: 1px solid black;">{description}</td>
                    <td style="border: 1px solid black;">{data['quantity']}</td>
                    <td style="border: 1px solid black;">{data['coo']}</td>
                    <td style="border: 1px solid black;">${data['value']:.2f}</td>
                </tr>
                """
            html_table += row

        html_table += """
            </tbody>
        </table><br>
        """

        return html_table

    def generate_summary_table(self, record):
        # This dictionary will store merged data by HS code
        product_data = defaultdict(lambda: {
            'description': [],
            'quantity': 0,
            'value': 0.0,
            'coo': '',
        })

        # Process each product line to gather HS codes
        for line in record.x_invoice_lines:
            product = line.product_id
            hs_code = product.dk_hs_code.x_hs_code if product.dk_hs_code else ""

            # Check if this product is not freight
            if product.id != 13813:  # Assuming 13813 is the freight product ID
                product_data[hs_code]['description'].append(product.name)
                product_data[hs_code]['quantity'] += line.quantity
                product_data[hs_code]['value'] += line.price_subtotal
                product_data[hs_code]['coo'] = product.x_country_id.name if product.x_country_id else "N/A"

        # Generate a smaller HTML table with HS Codes only
        html_table = """
        <table width="300px" style="text-align: center; border-collapse: collapse; border: 1px solid black;">
            <tr>
                <td style="border: 1px solid black;"><b>Country</b></td>
                <td style="border: 1px solid black;"><b>Commodity</b></td>
                <td style="border: 1px solid black;"><b>Dept</b></td>
            </tr>
            <tr>
                <td style="border: 1px solid black;"></td>
                <td style="border: 1px solid black;">
        """

        # Add HS Codes to the second cell of the second row
        hs_codes = "\n".join(product_data.keys())  # Join all HS codes with commas
        html_table += f"{hs_codes}"

        html_table += """
                </td>
                <td style="border: 1px solid black;">852</td>
            </tr>
            <tr>
                <td style="border: 1px solid black;"><b>Quantity</b></td>
                <td style="border: 1px solid black;"><b>Unit</b></td>
                <td style="border: 1px solid black;"><b>Unit Price</b></td>
            </tr>
            <tr>
                <td width="140px" style="border: 1px solid black;">As Per Invoice-Attached</td>
                <td width="140px" style="border: 1px solid black;">As Per Invoice-Attached</td>
                <td width="140px" style="border: 1px solid black;">As Per Invoice-Attached</td>
            </tr>
        </table>
        """

        return html_table

    @api.depends('x_document_date_apv', 'x_shipment_date_apv', 'x_payment_term_apv', 'x_contact_no_apv',
                 'x_signatory_apv')
    def compute_body3_apv(self):
        company_id = self.env['res.company'].browse(1)
        for rec in self:
            if rec.type not in ('out_invoice'):
                rec.x_body3_apv = ""
                return
            rec.x_body3_apv = (f"""
                <h5><u><center><b>Advance Payment Voucher</b></center></u></h5>
                <p>
                <br>
                <b>Currency:</b> <u>USD</u><br>
                <b>Name & address of the exporter:</b><br>
                    &emsp;&emsp;<u><b>{company_id.name}</b></u><br>
                    &emsp;&emsp;{company_id.street} {company_id.street2}<br>
                    &emsp;&emsp;{company_id.city}<br>
                <br>
                <b>Name & address of the importer:</b><br>
                     &emsp;&emsp;<u><b>{rec.partner_id.commercial_partner_id.name if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.name else ''}</b></u><br>
                    {'&emsp;&emsp;' + rec.partner_id.commercial_partner_id.street if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.street else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_id.commercial_partner_id.street2 if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.street2 else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_id.commercial_partner_id.city if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.city else ''}
                    {', ' + rec.partner_id.commercial_partner_id.country_id.name if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.country_id else ''}
                    {'<br>&emsp;&emsp;Attn: ' + rec.partner_id.commercial_partner_id.name if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.name else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_id.commercial_partner_id.phone if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.phone else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_id.commercial_partner_id.email if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.email else ''}

                <br><br>
                <b>Name & address of the Consignee:</b><br>
                     &emsp;&emsp;<u><b>{rec.partner_shipping_id.parent_id.name if rec.partner_shipping_id and rec.partner_shipping_id.name else ''}</b></u><br>
                    {'&emsp;&emsp;' + rec.partner_shipping_id.street if rec.partner_shipping_id and rec.partner_shipping_id.street else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_shipping_id.street2 if rec.partner_shipping_id and rec.partner_shipping_id.street2 else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_shipping_id.city if rec.partner_shipping_id and rec.partner_shipping_id.city else ''}
                    {', ' + rec.partner_shipping_id.country_id.name if rec.partner_shipping_id and rec.partner_shipping_id.country_id else ''}
                    {'<br>&emsp;&emsp;Attn: ' + rec.partner_shipping_id.name if rec.partner_shipping_id and rec.partner_shipping_id.name else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_shipping_id.phone if rec.partner_shipping_id and rec.partner_shipping_id.phone else ''}
                    {'<br>&emsp;&emsp;' + rec.partner_shipping_id.email if rec.partner_shipping_id and rec.partner_shipping_id.email else ''}
                <br><br>
                <b>For Export of:</b><br>
                    &emsp;&emsp;Items as per attached Invoice # {rec.x_sale_tax_invoice_number if rec.x_sale_tax_invoice_number else rec.name} 
                ({rec.x_sale_order.name if rec.x_sale_order.name else rec.x_web_order_number})<br>
                <br>
                    &emsp;<b><u>Items Information:</u></b><br>
                {self.generate_invoice_table(rec)}<br>
                <div style="text-align: right;">
                    <span style="font-weight: bold;">Total (USDs)</span>
                    <span style="font-weight: bold;">{rec.x_amount_total}</span>
                </div>
                <br><br><br>
                <b>NTN No. 4109694-7</b><br>
                <b>Estimated Shipment Date: </b><u>{self.format_date(rec.x_shipment_date_apv) if rec.x_shipment_date_apv else False}</u><br>
                <b>Dated: </b><u>{self.format_date(rec.x_document_date_apv) if rec.x_document_date_apv else False}</u><br>
                <br>
                <span style="float: right;">______________________________________________</span><br>
                <span style="float: right;">Stamp & Signatures of the Beneficiary</span><br>
                <span style="float: right;">{rec.x_signatory_apv.name}</span><br>
                <span style="float: right;">{rec.x_signatory_apv.x_job_title_id.x_name}</span><br>
                <br>
                <span style="float: right;">______________________________________________</span><br>
                <span style="width: 400px; float: right; text-align: right;">Stamp & Signatures of the Authorized Dealer</span><br>
                <br>
                <center>{self.generate_summary_table(rec)}</center><br>
                </p>
            """)

    @api.depends('x_document_date_apv', 'x_shipment_date_apv', 'x_payment_term_apv', 'x_contact_no_apv',
                 'x_signatory_apv')
    def compute_body4_apv(self):
        for rec in self:
            if rec.type not in ('out_invoice'):
                rec.x_body4_apv = ""
                return
            rec.x_body4_apv = (f"""
                <p>
                <span style="float: right;"><b>Date: </b>{self.format_date(rec.x_document_date_apv) if rec.x_document_date_apv else False}</span><br>
                <b>The Manager<br>
                <br><br>
                ________________<br>
                Bank Alfalah Islamic ("Bank")</b><br>
                <br>
                <b>Dear Sir/Madam,</b><br>
                <br>
                I/We <b><u>Taraz Technologies (Pvt) Ltd</u></b> hereby undertake that price mentioned on invoice no. 
                <u><b>{rec.x_sale_tax_invoice_number if rec.x_sale_tax_invoice_number else rec.name} ({rec.x_sale_order.name if rec.x_sale_order.name else rec.x_web_order_number})</b></u> 
                dated. <b>{self.format_date(rec.invoice_date) if rec.invoice_date else False}</b> is declared in accordance with Fair 
                Market Value(<b>"FMV"</b>) of <u><b>The Concerned Market<b></u>.<br>
                <br>
                I/We further undertake that declared price is in accordance with FMV. In case, if any difference (including 
                valuation from professional evaluators) is found in price at any point of time, I/we will be fully responsible 
                for all the consequences. Furthermore, the Goods Declaration (GD) will show declared and assessed value of 
                each item and that will be submitted by me/us in Bank immediately after release of goods.<br>
                <br>
                I/we hereby confirm and undertake that the information provided above is correct and true to the best of my/our 
                knowledge. Further, if there is any change in the above stated information in future, I/We shall be fully 
                responsible to immediately inform the same to the Bank in writing. I also indemnify the Bank against any 
                losses/claims/liabilities that the Bank may incur as a consequence of the information being incorrect or not updated.<br>
                <br>
                This Undertaking shall be governed by and construed in accordance with the laws of Pakistan and the courts of 
                Karachi shall have the jurisdiction to resolve any disputes arising hereunder.<br>
                <br>
                I/we hereby confirm that I/we have all the requisite authority from <u><b>Taraz Technologies (PVt.) Ltd.</b></u> vide 
                <u><b>Board Resolution</b></u> to provide this Undertaking to the Bank.<br>
                <br><br>
                <center>__________________________ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;____________________________________</center>
                <center><b>Authorized Signatory</b> &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; <b>Authorized Signatory</b> (Note 1)</center><br>
                <br>
                <b>Note 1</b> (please tick checkbox)<br>
                <table style="width: 100%; margin-top: 10px;">
                    <tr>
                        <td style="width: 3%; vertical-align: center;">
                            ☐
                        </td>
                        <td style="width: 97%; vertical-align: top;">
                            <b>Authorized signatories should be verified by IPA / PA holder at branch / BU level which should be as per 
                            BoD resolution of customer OR as per Bank's system (T24). IPA / PA holder would be solely responsible in case 
                            of any eventuality.</b>
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 3%; vertical-align: center;">
                            ☐
                        </td>
                        <td style="width: 97%; vertical-align: top;">
                            <b>Original Indemnity cum FMV undertaking would be shared with CTO for their records along with other trade documents.</b><br>   
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 3%;">

                        </td>
                        <td style="width: 97%">
                            <b><i>This undertaking is to be discontinued if Master Undertaking is obtained.</i></b>
                        </td>
                    </tr>
                </table>
                </p>
            """)

    @api.depends('invoice_payments_widget')
    def _compute_payment_status(self):
        for rec in self:
            if rec.type == 'entry':
                rec.x_payment_status = False
            elif rec.invoice_payments_widget:
                invoice_payments_widget = rec.invoice_payments_widget
                invoice_payments_widget = invoice_payments_widget.split(', ')
                invoice_payments = [
                    int(item.replace('"account_payment_id": ', '')) for item in invoice_payments_widget
                    if '"account_payment_id": ' in item and item.replace('"account_payment_id": ', '').isdigit()
                ]
                payment_ids = self.env['account.payment'].browse(invoice_payments)
                if not payment_ids:
                    rec.x_payment_status = False
                elif all(payment.state == 'reconciled' for payment in payment_ids):
                    rec.x_payment_status = 'reconcile'
                elif any(payment.state == 'reconciled' for payment in payment_ids):
                    rec.x_payment_status = 'partially'
                elif all(payment.state != 'reconciled' for payment in payment_ids):
                    rec.x_payment_status = 'unreconciled'
            else:
                rec.x_payment_status = False

    @api.depends('x_related_po_s')
    def _compute_related_purchase_id(self):
        for rec in self:
            if rec.company_id.id == 1:
                return
            elif rec.x_purchase_id:
                rec.x_related_purchase_id = rec.x_purchase_id.id
            elif rec.x_related_po_s:
                rec.x_related_purchase_id = rec.x_related_po_s[0].id

    def action_download_attachments(self):
        if not self.x_attachment_ids:
            return
        if len(self.x_attachment_ids.ids) > 1:
            try:
                url = '/web/binary/download_document?tab_id=%s&zip_filename=%s' % (
                    self.x_attachment_ids.ids, self.x_folder_name)
            except ValueError:
                url = '/web/binary/download_document?tab_id=%s' % self.x_attachment_ids.ids
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
        else:
            url = '%s&download=true' % self.x_attachment_ids.mapped('local_url')[0]
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }

    def action_view_related_sale_orders(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['domain'] = [('id', 'in', self.x_sale_ids.ids)]
        action['context'] = {}
        return action

    def action_view_related_purchase_orders(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.x_related_po_s.ids)]
        action['context'] = {}
        return action

    @api.depends('x_purchase_id', 'picking_id', 'x_picking_ids', 'invoice_line_ids.is_landed_costs_line')
    def _compute_move_type(self):
        for rec in self:
            if rec.type not in ('in_invoice', 'in_refund', 'entry'):
                rec.x_move_type = False
            elif rec.picking_id:
                rec.x_move_type = 'receipt_bill'
            elif rec.x_purchase_id:
                rec.x_move_type = 'purchase_bill'
            elif rec.x_picking_ids and not any(line.is_landed_costs_line for line in rec.invoice_line_ids):
                rec.x_move_type = 'related_bill'
            elif rec.x_picking_ids and any(line.is_landed_costs_line for line in rec.invoice_line_ids):
                rec.x_move_type = 'landed_cost_bill'

    def copy(self, default=None):
        self.x_document = False
        res = super(AccountMove, self).copy(default)
        return res

    @api.depends('invoice_line_ids.account_id')
    def _compute_odoo_status(self):
        for rec in self:
            account_ids = rec.invoice_line_ids.mapped('account_id')
            if 1174 in account_ids.ids:
                rec.x_odoo_entry_state = 'normal'
            rec.x_compute_odoo_status = True

    def action_add_to_sale_order(self):
        action = self.env.ref('cus_accounts.action_add_move_source').read()[0]
        action['context'] = {
            'default_x_move_id': self.id,
            'default_x_add_to': 'sale',
            'default_x_sale_id': self.x_sale_order.id,
        }
        return action

    def action_add_to_purchase_order(self):
        action = self.env.ref('cus_accounts.action_add_move_source').read()[0]
        action['context'] = {
            'default_x_move_id': self.id,
            'default_x_add_to': 'purchase',
            'default_x_purchase_id': self.x_purchase_id.id,
        }
        return action

    def action_relate_to_purchase_orders(self):
        action = self.env.ref('cus_accounts.action_add_move_source').read()[0]
        action['context'] = {
            'default_x_move_id': self.id,
            'default_x_add_to': 'related_purchase',
            'default_x_purchase_ids': self.x_related_po_s.ids,
        }
        return action

    def action_relate_to_sale_orders(self):
        action = self.env.ref('cus_accounts.action_add_move_source').read()[0]
        action['context'] = {
            'default_x_move_id': self.id,
            'default_x_add_to': 'related_sale',
            'default_x_sale_ids': self.x_sale_ids.ids,
        }
        return action

    @api.depends('invoice_origin')
    def _compute_purchase_order(self):
        for rec in self:
            purchase_id = self.env['purchase.order'].search([('name', '=', rec.invoice_origin)])
            rec.x_purchase_id = purchase_id.id if purchase_id else False

    @api.depends('x_rate', 'amount_total', 'amount_total_signed')
    def get_currency_error(self):
        for rec in self:
            amount_total_signed = rec.amount_total_signed * - 1 if rec.amount_total_signed < 0 else rec.amount_total_signed
            amount_total = round(rec.amount_total / rec.x_rate, 2) if rec.x_rate != 0 else rec.amount_total
            rec.x_currency_error = True if amount_total_signed != amount_total else False

    @api.depends('x_sale_order.x_customer_po')
    def get_x_customer_po(self):
        for rec in self:
            if rec.x_sale_order:
                rec.x_document = rec.x_sale_order.x_customer_po

    @api.depends('x_document', 'x_reconciled_doc', 'date', 'x_folder_name')
    def compute_file_name(self):
        for rec in self:
            rec.x_document_name = "%s - %s" % (rec.date, rec.id)
            if rec.x_folder_name:
                rec.x_document_name += " - %s" % rec.x_folder_name
            # x = 0
            # for attachment in rec.x_attachment_ids:
            #     extension = attachment.mimetype.split('/')[-1]
            #     attachment.name = '%s (%s).%s' % (rec.x_document_name, x, extension) if x else '%s.%s' % (rec.x_document_name, extension)
            #     x += 1

    def change_luca_state_to_pending(self):
        for rec in self:
            rec.x_luca_entry_state = 'pending'

    def change_luca_state_to_blocked(self):
        for rec in self:
            rec.x_luca_entry_state = 'blocked'

    def change_luca_state_to_done(self):
        for rec in self:
            rec.x_luca_entry_state = 'done'

    def change_odoo_state_to_normal(self):
        for rec in self:
            rec.x_odoo_entry_state = 'normal'

    def change_odoo_state_to_blocked(self):
        for rec in self:
            rec.x_odoo_entry_state = 'blocked'

    def change_odoo_state_to_done(self):
        for rec in self:
            rec.x_odoo_entry_state = 'done'

    @api.depends(
        'invoice_line_ids', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.type',
        'x_income_move_id', 'x_income_move_id.state',
        'x_sale_order.picking_ids', 'x_sale_order.picking_ids.state'
    )
    def _compute_income_journal_entry_state(self):
        for rec in self:
            if not any(rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name
            )) or any(
                picking_id.state != 'done' for picking_id in rec.x_sale_order.picking_ids) or rec.type != 'out_invoice':
                rec.x_income_journal_entry_state = 'pending'

            elif any(rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name
            )) and not rec.x_income_move_id and all(
                picking_id.state == 'done' for picking_id in rec.x_sale_order.picking_ids):
                rec.x_income_journal_entry_state = 'blocked'

            elif any(rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name
            )) and rec.x_income_move_id.state != 'posted' and all(
                picking_id.state == 'done' for picking_id in rec.x_sale_order.picking_ids):
                rec.x_income_journal_entry_state = 'normal'

            elif any(rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name
            )) and rec.x_income_move_id.state == 'posted' and all(
                picking_id.state == 'done' for picking_id in rec.x_sale_order.picking_ids):
                rec.x_income_journal_entry_state = 'done'

    @api.depends('state', 'x_income_move_id', 'invoice_line_ids', 'invoice_line_ids.product_id',
                 'invoice_line_ids.product_id.type')
    def transfer_services_advance_to_income(self):
        for rec in self:
            if rec.x_income_move_id:
                rec.x_services_advance_visible = False
            else:
                rec.x_services_advance_visible = any(rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name
                ))

    def create_income_journal_entry(self):
        for rec in self:
            invoice_vals = {
                'type': 'entry',
                'x_sale_order': rec.x_sale_order.id,
                'x_move_type': 'payment_entry',
                'ref': "%s services advance to income" % rec.name,
                'date': datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'journal_id': 22 if rec.company_id.id == 1 else 102,
                'line_ids': []
            }
            for line in rec.invoice_line_ids.filtered(
                    lambda l: l.product_id.type == 'service' and 'Down Payment' not in l.product_id.name):
                invoice_vals['line_ids'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'partner_id': line.partner_id.id,
                    'account_id': line.account_id.id,
                    'name': line.name,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'currency_id': line.currency_id.id,
                    'amount_currency': line.amount_currency,
                    'debit': line.credit,  # debit advance account if credited in invoice
                    'credit': line.debit,  # credit advance account if debited in invoice
                }))
                invoice_vals['line_ids'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'partner_id': line.partner_id.id,
                    'account_id': line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id,
                    'name': line.name,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'currency_id': line.currency_id.id,
                    'amount_currency': line.amount_currency,
                    'debit': line.debit,  # debit advance account if credited in invoice
                    'credit': line.credit,  # credit advance account if debited in invoice
                }))
            move = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
            rec.x_income_move_id = move.id
            action = self.env.ref('account.action_move_journal_line').read()[0]
            return dict(action, view_mode='form', res_id=move.id, views=[(False, 'form')])

    def action_view_journal_entry(self):
        for rec in self:
            action = self.env.ref('account.action_move_journal_line').read()[0]
            return dict(action, view_mode='form', res_id=rec.x_income_move_id.id, views=[(False, 'form')])

    def action_view_move_sale_order(self):
        for rec in self:
            action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
            return dict(action, view_mode='form', res_id=rec.x_sale_order.id, views=[(False, 'form')])

    def action_view_move_purchase_order(self):
        for rec in self:
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            return dict(action, view_mode='form', res_id=rec.x_purchase_id.id, views=[(False, 'form')])

    def action_post(self):
        for rec in self:
            """return action_post if date is between global leave datetime dates"""
            global_leave_id = rec.company_id.resource_calendar_id.global_leave_ids.filtered(
                lambda l: l.date_from.date() <= rec.date <= l.date_to.date())
            if global_leave_id:
                return super(AccountMove, self).action_post()
            currency_rate = self.env['res.currency.rate'].search(
                [('name', '=', rec.date), ('currency_id', '=', rec.currency_id.id)])
            if (
                    not currency_rate
                    and rec.date.weekday() not in (5, 6)
                    and rec.currency_id.id != 2
                    and rec.company_id.id == 2
            ):
                rec.x_currency_warning = "Currency rate of %s does not exist on %s." % (rec.currency_id.name, rec.date)
            else:
                rec.x_currency_warning = False
        return super(AccountMove, self).action_post()

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
        super(AccountMove, self)._onchange_invoice_date()
        if self.invoice_date:
            if not self.invoice_payment_term_id and (
                    not self.invoice_date_due or self.invoice_date_due != self.invoice_date):
                self.invoice_date_due = self.invoice_date
            self.date = self.invoice_date
            self._onchange_currency()

    @api.onchange('invoice_date')
    def update_move_dates(self):
        for rec in self:
            if rec.invoice_date:
                rec.date = rec.invoice_date
                rec.invoice_date_due = rec.invoice_date

    @api.onchange('journal_id')
    def update_move_lines(self):
        for rec in self:
            if rec.journal_id.x_product_ids:
                rec.invoice_line_ids = [(2, line.id) for line in rec.invoice_line_ids]
                invoice_line_ids = []
                for product in rec.journal_id.x_product_ids:
                    invoice_line_ids.append((0, 0, {
                        'name': product.description,
                        'product_id': product.id,
                        'account_id': product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id,
                        'product_uom_id': product.uom_id.id,
                        'quantity': 1,
                        'price_unit': product.lst_price,
                    }))
                rec.invoice_line_ids = invoice_line_ids

    @api.depends('x_related_invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.x_invoice_count = len(rec.x_related_invoice_ids)
            if rec.type == 'in_invoice':
                for move in rec.x_related_invoice_ids:
                    move.x_related_bill_ids = [(4, rec.id)]

    @api.depends('x_related_bill_ids.x_related_invoice_ids')
    def _compute_bill_count(self):
        for rec in self:
            if rec.type == 'out_invoice':
                rec.x_related_bill_ids = [
                    (6, 0, self.env['account.move'].search([('x_related_invoice_ids', 'ilike', rec.id)]).ids)
                ]
            rec.x_bill_count = len(rec.x_related_bill_ids)

    def action_create_bill(self):
        for rec in self:
            bill_id = self.env['account.move'].create({
                'type': 'in_invoice',
                'partner_id': False,
                'partner_shipping_id': False,
                'invoice_date': datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'journal_id': 1 if rec.company_id.id == 1 else 97,
                'invoice_incoterm_id': False,
                'x_related_invoice_ids': [rec.id]
            })
            rec.x_related_bill_ids = [(4, bill_id.id)]
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            return dict(action, view_mode='form', res_id=bill_id.id, views=[(False, 'form')])

    def action_view_bills(self):
        for rec in self:
            action = self.env.ref('cus_accounts.view_invoice_related_bills_action').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_related_invoice_ids': [rec.id],
                'journal_id': 1 if rec.company_id.id == 1 else 97,
            }
            action['domain'] = [('x_related_invoice_ids', 'ilike', rec.id)]
            return action

    def action_view_invoices(self):
        for rec in self:
            action = self.env.ref('cus_accounts.view_bill_related_invoices_action').read()[0]
            action['context'] = {
                'default_type': 'out_invoice',
                'default_x_related_bill_ids': [rec.id],
                'journal_id': 1 if rec.company_id.id == 1 else 97,
            }
            action['domain'] = [('x_related_bill_ids', 'ilike', rec.id)]
            return action

    def unlink(self):
        sale_line_ids = []
        sale_order = None
        for rec in self:
            rec.x_related_invoice_ids = []
            rec.x_related_bill_ids = []
            if rec.x_sale_order:
                sale_order = rec.x_sale_order
                if rec.journal_id.x_remove_down_payment_lines:
                    product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
                    for line in rec.invoice_line_ids:
                        if line.product_id.id == int(product_id):
                            for sale_line_id in line.sale_line_ids:
                                sale_line_ids.append(sale_line_id.id)
        super(AccountMove, self).unlink()
        if sale_order:
            if sale_order.state != 'sale':
                sale_order.action_unlock()
            sale_order.order_line = [(2, sale_line_id) for sale_line_id in sale_line_ids]
            if sale_order.state != 'done':
                sale_order.action_done()

    @api.depends('invoice_date', 'date', 'currency_id', 'journal_id')
    def get_currency_rate_id(self):
        for rec in self:
            rec.x_currency_rate_id = self.env['res.currency.rate'].search([
                ('currency_id', '=', rec.currency_id.id), ('company_id', '=', rec.company_id.id),
                ('name', '<=', rec.date),
            ], limit=1).id

    @api.depends('x_currency_rate_id', 'x_currency_rate_id.rate')
    def get_currency_rate(self):
        for rec in self:
            rec.x_rate = rec.x_currency_rate_id.rate

    @api.depends('amount_total', 'amount_total_signed')
    def get_je_currency_rate(self):
        for rec in self:
            rec.x_je_rate = rec.amount_total / rec.amount_total_signed if rec.amount_total_signed != 0 else 1

    @api.depends('currency_id', 'date', 'amount_total_signed', 'amount_total')
    def get_amount_total_try(self):
        for rec in self:
            if rec.currency_id.id != self.env.ref('base.TRY').id:
                rate_try = self.env['res.currency.rate'].search([
                    ('currency_id', '=', self.env.ref('base.TRY').id), ('company_id', '=', 2), ('name', '<=', rec.date),
                ], limit=1).rate
                rate_currency = self.env['res.currency.rate'].search([
                    ('currency_id', '=', rec.currency_id.id), ('company_id', '=', 2), ('name', '<=', rec.date),
                ], limit=1).rate
                rec.x_amount_total_try = rec.amount_total_signed * rate_try / rate_currency if rate_currency else rec.amount_total_signed * rate_try
                rec.x_amount_total_try = rec.x_amount_total_try * -1 if rec.amount_total_signed < 0 else rec.x_amount_total_try
            else:
                rec.x_amount_total_try = rec.amount_total

    @api.onchange('invoice_date', 'currency_id', 'x_currency_rate_id', 'x_rate')
    def update_invoice_lines(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                if line.sale_line_ids:
                    line.price_unit = line.sale_line_ids[0].price_unit * rec.x_rate if rec.x_rate != 0 else \
                        line.sale_line_ids[0].price_unit
                    line._onchange_price_subtotal()
            rec._recompute_payment_terms_lines()
            rec.update_invoice_data()
            for line in rec.x_invoice_lines:
                line.unit_price *= rec.x_rate if rec.x_rate != 0 else 1
                line.price_subtotal = line.unit_price * line.quantity * (100 - line.discount) / 100
            rec.compute_amount()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_parent_id = fields.Many2one(related="account_id.x_parent_id", store=True)
    x_parent_id_1 = fields.Many2one(related="account_id.x_parent_id_1", store=True)
    x_parent_id_2 = fields.Many2one(related="account_id.x_parent_id_2", store=True)
    x_parent_id_3 = fields.Many2one(related="account_id.x_parent_id_3", store=True)
    x_parent_id_4 = fields.Many2one(related="account_id.x_parent_id_4", store=True)
    x_parent_id_5 = fields.Many2one(related="account_id.x_parent_id_5", store=True)

    x_is_otb_account = fields.Boolean(string='OTB Account?', required=False)
    x_main_account_id = fields.Many2one(comodel_name="account.account", string="ITB Account")
    x_main_account_type = fields.Many2one(comodel_name="account.account.type", string="ITB Account Type")
    x_gl_type_id = fields.Many2one(comodel_name='account.account.gl.type', string='Account GL Type')
    x_gl_group_id = fields.Many2one(comodel_name='account.account.gl.group', string='Account GL Group')
    x_get_account_data = fields.Boolean(compute="_get_account_data")

    x_status = fields.Selection([('reconciled', 'Reconciled'), ('unreconciled', 'Unreconciled')],
                                string='Status', default='unreconciled',
                                compute='compute_status', store=True
                                )
    x_custom_tag_ids = fields.Many2many('custom.tags', string='Tags')

    x_currency_pkr_id = fields.Many2one('res.currency', string='Currency (PKR)',
                                        default=lambda self: self.env['res.currency'].search([('name', '=', 'PKR')],
                                                                                             limit=1))
    x_debit_in_pkr = fields.Monetary(string='Debit in PKR', store=True, readonly=True,
                                     compute='_compute_debit_in_pkr',
                                     currency_field='x_currency_pkr_id')
    x_credit_in_pkr = fields.Monetary(string='Credit in PKR', store=True, readonly=True,
                                      compute='_compute_credit_in_pkr',
                                      currency_field='x_currency_pkr_id')
    x_tags_by_source = fields.Many2many(string="Tags by Source", related="move_id.x_tag_ids")

    @api.depends('credit')
    def _compute_credit_in_pkr(self):
        currency_pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
        for rec in self:
            if rec.credit < 0:
                rec.x_credit_in_pkr = (rec.company_currency_id._convert(abs(rec.credit), currency_pkr,
                                                                        rec.company_id, rec.date)) * -1
            else:
                rec.x_credit_in_pkr = rec.company_currency_id._convert(rec.credit, currency_pkr,
                                                                       rec.company_id, rec.date)

    @api.depends('debit')
    def _compute_debit_in_pkr(self):
        currency_pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
        for rec in self:
            if rec.debit < 0:
                rec.x_debit_in_pkr = (rec.company_currency_id._convert(abs(rec.debit), currency_pkr,
                                                                       rec.company_id, rec.date)) * -1
            else:
                rec.x_debit_in_pkr = rec.company_currency_id._convert(rec.debit, currency_pkr,
                                                                      rec.company_id, rec.date)

    @api.depends('full_reconcile_id', 'account_id.reconcile', 'balance')
    def compute_status(self):
        for rec in self:
            if (rec.full_reconcile_id == False) and (rec.balance != 0) and (rec.account_id.reconcile == True):
                rec.x_status = 'unreconciled'
            else:
                rec.x_status = 'reconciled'

    def open_view(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move.line',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_line_form').id,
                'res_id': rec.id,
            }

    @api.depends('account_id')
    def _get_account_data(self):
        for rec in self:
            rec.update({
                'x_is_otb_account': rec.account_id.x_is_otb_account,
                'x_main_account_id': rec.account_id.x_main_account_id.id,
                'x_main_account_type': rec.account_id.x_main_account_id.user_type_id.id,
                'x_gl_type_id': rec.account_id.x_gl_type_id.id,
                'x_gl_group_id': rec.account_id.x_gl_type_id.x_gl_group_id.id,
            })
            rec.x_get_account_data = True
