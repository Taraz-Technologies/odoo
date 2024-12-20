from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    x_status = fields.Selection(string="State", selection=[('Valid', 'Valid'), ('Invalid', 'Invalid'), ],
                                default="Valid", required=False, )
    x_date_from = fields.Date(string="Date From", readonly=False, compute="compute_dates", store=True, )
    x_date_to = fields.Date(string="Date To", readonly=False, compute="compute_dates", store=True, )
    x_gl_starting_balance = fields.Monetary(string="Starting Balance", required=False, store=True,
                                            compute="_compute_general_ledger_balances", )
    x_gl_ending_balance = fields.Monetary(string="Ending Balance", required=False, store=True,
                                          compute="_compute_general_ledger_balances", )
    x_difference = fields.Monetary(string="Difference", required=False, store=True,
                                   compute="_compute_general_ledger_balances", )
    x_general_ledger_item_ids = fields.Many2many(comodel_name="account.move.line",
                                                 relation="account_move_line_account_bank_statement_rel",
                                                 column1="account_move_line_id", column2="account_bank_statement_id",
                                                 string="General Ledger Items", compute="update_general_ledger_items",
                                                 store=True, )
    x_payment_ids = fields.Many2many(comodel_name='account.payment', string='Payments',
                                     compute="get_unreconciled_payments", store=True)

    @api.depends('line_ids.journal_entry_ids', 'x_date_from', 'x_date_to')
    def get_unreconciled_payments(self):
        for rec in self:
            payment_ids = self.env['account.payment'].search([
                ('payment_date', '>=', rec.x_date_from), ('payment_date', '<=', rec.x_date_to), ('state', '=', 'posted'),
                '|', ('journal_id', '=', rec.journal_id.id), ('destination_journal_id', '=', rec.journal_id.id)
            ])
            rec.x_payment_ids = [(6, 0, payment_ids.ids)]

    @api.onchange('balance_end')
    def update_balance_end_real(self):
        for rec in self:
            rec.balance_end_real = rec.balance_end

    @api.onchange('journal_id', 'date')
    def update_alfalah_reference(self):
        for rec in self:
            if rec.journal_id._origin.id == 7 and rec.date:
                rec.name = 'Bank Alfalah Limited - ' + rec.date.strftime('%b') + ' ' + rec.date.strftime('%Y')

    @api.depends('date')
    def compute_dates(self):
        for rec in self:
            rec.x_date_from = rec.date
            rec.x_date_to = rec.date + relativedelta(months=1, days=-1)
            rec.update_general_ledger_items()

    @api.depends('x_date_from', 'x_date_to')
    def update_general_ledger_items(self):
        for rec in self:
            if rec.x_date_from and rec.x_date_to:
                journal_item_ids = self.env['account.move.line'].search(
                    [('date', '>=', rec.x_date_from), ('date', '<=', rec.x_date_to), ('move_id.state', '=', 'posted'),
                     ('account_id', 'in', (rec.journal_id.default_credit_account_id.id,
                                           rec.journal_id.default_debit_account_id.id))]).ids
                rec.x_general_ledger_item_ids = [(6, 0, journal_item_ids)]
                rec._compute_general_ledger_balances()

    @api.depends('x_date_from', 'x_date_to', 'x_general_ledger_item_ids')
    def _compute_general_ledger_balances(self):
        for rec in self:
            if rec.x_date_from and rec.x_date_to:
                date_from_journal_item_ids = self.env['account.move.line'].search([('date', '<', rec.x_date_from),
                                                                                   ('move_id.state', '=', 'posted'),
                                                                                   ('account_id', 'in', (
                                                                                       rec.journal_id.default_credit_account_id.id,
                                                                                       rec.journal_id.default_debit_account_id.id))])
                date_to_journal_item_ids = self.env['account.move.line'].search([('date', '<=', rec.x_date_to),
                                                                                 ('move_id.state', '=', 'posted'),
                                                                                 ('account_id', 'in', (
                                                                                     rec.journal_id.default_credit_account_id.id,
                                                                                     rec.journal_id.default_debit_account_id.id))])
                if rec.journal_id.currency_id.id == 2 or not rec.journal_id.currency_id:
                    starting_balance = date_from_journal_item_ids.mapped('balance')
                    rec.x_gl_starting_balance = sum(starting_balance)
                    ending_balance = date_to_journal_item_ids.mapped('balance')
                    rec.x_gl_ending_balance = sum(ending_balance)
                else:
                    starting_balance = date_from_journal_item_ids.mapped('amount_currency')
                    rec.x_gl_starting_balance = sum(starting_balance)
                    ending_balance = date_to_journal_item_ids.mapped('amount_currency')
                    rec.x_gl_ending_balance = sum(ending_balance)
                rec.x_difference = rec.x_gl_ending_balance - rec.balance_end_real

    def update_journal_entries(self):
        for record in self:
            for line in record.line_ids:
                line.compute_journal_entries()

    @api.model
    def update_gl_balances(self):
        statement_ids = self.env['account.bank.statement'].search([])
        for statement in statement_ids:
            statement.compute_dates()


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    x_invoice_ids = fields.Many2many(comodel_name="account.move",
                                     relation="account_bank_statement_line_account_move_rel_1",
                                     column1="account_bank_statement_line_1_id",
                                     column2="account_move_1_id",
                                     string="Invoice / Bills",
                                     compute='compute_invoices_bills', store=True)
    x_payment_ids = fields.Many2many(comodel_name='account.payment', string='Payments',
                                     compute='compute_payments', store=True)
    x_journal_entries = fields.Many2many(comodel_name="account.move",
                                         relation="account_bank_statement_line_account_move_rel",
                                         column1="account_bank_statement_line_id",
                                         column2="account_move_id",
                                         string="Journal Entries",
                                         compute='compute_journal_entries', store=True)

    x_date_mismatch = fields.Boolean(string='Date Mismatch', compute="compute_payments", store=True)

    @api.depends('journal_entry_ids')
    def compute_journal_entries(self):
        for rec in self:
            rec.x_journal_entries = [(6, 0, rec.journal_entry_ids.mapped('move_id').ids)]

    @api.depends('journal_entry_ids')
    def compute_payments(self):
        for rec in self:
            payment_ids = []
            for line in rec.journal_entry_ids:
                payment_ids.append(self.env['account.payment'].search([('move_line_ids', 'ilike', line.id)]).id)
            rec.x_payment_ids = [(6, 0, payment_ids)]

            rec.x_date_mismatch = False
            if rec.x_payment_ids:
                payment_date_months = {payment.payment_date.month for payment in rec.x_payment_ids}
                if len(payment_date_months) != 1:
                    rec.x_date_mismatch = True
                elif rec.x_payment_ids.mapped('payment_date')[0].month != rec.date.month:
                    rec.x_date_mismatch = True

    @api.depends('x_payment_ids')
    def compute_invoices_bills(self):
        for rec in self:
            rec.x_invoice_ids = [(6, 0, rec.x_payment_ids.mapped('reconciled_invoice_ids').ids)]
