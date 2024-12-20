# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class DataQuickbooks(models.Model):
    _name = "data.quickbooks"
    _description = "Data QuickBooks"
    _rec_name = "x_name"
    _order = "create_date desc"

    @api.model
    def _get_journals(self):
        return self.env['data.quickbooks'].search([], limit=1).x_journal_ids

    x_name = fields.Char(string="Name", required=False, compute="_get_export_name", store=True, )

    x_date_from = fields.Date(string="Date From", required=False, )
    x_date_to = fields.Date(string="Date To", required=False, )

    x_journal_ids = fields.Many2many(comodel_name="account.journal", relation="account_journal_data_quickbooks_filter_rel", default=_get_journals,
                                     column1="account_journal_id", column2="data_quickbooks_filter_id", string="QuickBooks Journals", )

    x_invoice_count = fields.Integer(string="# of Invoices", required=False, compute="_get_quickbooks_data", store=True, )
    x_bill_count = fields.Integer(string="# of Bills", required=False, compute="_get_quickbooks_data", store=True, )
    x_internal_transfer_count = fields.Integer(string="# of Internal Transfers", required=False, compute="_get_quickbooks_data", store=True, )

    x_invoice_ids = fields.Many2many(comodel_name="account.move", relation="account_move_data_quickbooks_rel_1",
                                     column1="account_move_id", column2="data_quickbooks_id",
                                     string="Invoices", compute="_get_quickbooks_data", store=True, domain="[('type', '=', 'out_invoice')]", )
    x_bill_ids = fields.Many2many(comodel_name="account.move", relation="account_move_data_quickbooks_rel_2",
                                  column1="account_move_id", column2="data_quickbooks_id",
                                  string="Bills", compute="_get_quickbooks_data", store=True, domain="[('type', '=', 'in_invoice')]", )
    x_internal_transfer_ids = fields.Many2many(comodel_name="account.payment", relation="account_payment_data_quickbooks_rel",
                                               column1="account_payment_id", column2="data_quickbooks_id",
                                               string="Internal Transfers", compute="_get_quickbooks_data", store=True, )

    x_export_bills = fields.Many2many(comodel_name="account.move", relation="account_move_data_quickbooks_rel_3",
                                      column1="account_move_id", column2="data_quickbooks_id", string="Export Bills",
                                      domain="[('state', '=', 'posted'), ('type', '=', 'in_invoice'), ('x_payment_method', 'in', x_journal_ids), "
                                             "('invoice_date', '<=', x_date_to), ('invoice_date', '>=', x_date_from)]")

    @api.depends('x_date_from', 'x_date_to')
    def _get_export_name(self):
        for rec in self:
            if rec.x_date_to and rec.x_date_from:
                rec.x_name = rec.x_date_from.strftime('%Y%m%d') + "-" + rec.x_date_to.strftime('%Y%m%d')

    @api.depends('x_date_from', 'x_date_to', 'x_journal_ids')
    def _get_quickbooks_data(self):
        for rec in self:
            if rec.x_date_to and rec.x_date_from and rec.id:
                journals = rec.x_journal_ids.ids
                invoices = self.env['account.move'].search([('state', '=', 'posted'), ('type', '=', 'out_invoice'), ('x_payment_method', 'in', journals),
                                                            ('invoice_date', '<=', rec.x_date_to), ('invoice_date', '>=', rec.x_date_from)]).ids
                bills = self.env['account.move'].search([('state', '=', 'posted'), ('type', '=', 'in_invoice'), ('x_payment_method', 'in', journals),
                                                         ('invoice_date', '<=', rec.x_date_to), ('invoice_date', '>=', rec.x_date_from)]).ids
                internal_transfers = self.env['account.payment'].search([('payment_type', '=', 'transfer'), ('state', 'in', ('posted', 'reconciled')),
                                                                         ('journal_id', 'in', journals), ('destination_journal_id', 'in', journals),
                                                                         ('payment_date', '<=', rec.x_date_to), ('payment_date', '>=', rec.x_date_from)]).ids

                rec.x_invoice_count = len(invoices)
                rec.x_bill_count = len(bills)
                rec.x_internal_transfer_count = len(internal_transfers)

                rec.x_invoice_ids = [(6, 0, invoices)]
                rec.x_bill_ids = [(6, 0, bills)]
                rec.x_internal_transfer_ids = [(6, 0, internal_transfers)]

    def generate_excel_report(self):
        return self.env.ref('quickbook_data_export.data_quickbooks_xlsx').report_action(self)


class AccountsQuickbooks(models.Model):
    _name = "accounts.quickbooks"
    _description = "Accounts Quickbooks"
    _rec_name = "x_name"

    x_name = fields.Char(string="Account Name", required=False, )
    x_type = fields.Selection(string="Account Type",
                              selection=[
                                  ('AP', 'Accounts payable'),
                                  ('AR', 'Accounts receivable'),
                                  ('BANK', 'Checking or savings'),
                                  ('CCARD', 'Credit card account'),
                                  ('COGS', 'Cost of goods sold'),
                                  ('EQUITY', 'Capital/Equity'),
                                  ('EXEXP', 'Other expense'),
                                  ('EXINC', 'Other income'),
                                  ('EXP', 'Expense'),
                                  ('FIXASSET', 'Fixed asset'),
                                  ('INC', 'Income'),
                                  ('LTLIAB', 'Long term liability'),
                                  ('NONPOSTING', 'Non-posting account'),
                                  ('OASSET', 'Other asset'),
                                  ('OCASSET', 'Other current asset'),
                                  ('OCLIAB', 'Other current liability'),
                              ],
                              required=False, )


class ContactsQuickbooks(models.Model):
    _name = "contacts.quickbooks"
    _description = "Contacts Quickbooks"
    _rec_name = "x_name"

    x_name = fields.Char(string="Contact Name", required=False, )
    x_type = fields.Selection(string="Contact Type",
                              selection=[
                                  ('CUST', 'Customer'),
                                  ('VEND', 'Vendor'),
                              ],
                              required=False, )


