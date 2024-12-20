from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PayrollCurrencyRates(models.Model):
    _name = 'payroll.currency.rate'
    _description = 'Payroll Currency Rates'
    _rec_name = 'name'
    _order = 'name desc'

    x_date_from = fields.Date(string='Date from', required=True, default="2022-01-01")
    x_journal_id = fields.Many2one(comodel_name='account.journal', string='Journal', required=True,
                                   default=lambda self: self.env.ref("customizations.journal_bank_alfalah").id)
    x_account_id = fields.Many2one(comodel_name='account.account', string='Account', required=True,
                                   default=lambda self: self.env.ref("customizations.account_bank_alfalah_limited").id)
    x_in_amount = fields.Float(string='In Amount', compute="compute_amounts", store=True)
    x_out_amount = fields.Float(string='Out Amount', compute="compute_amounts", store=True)
    x_balance_amount = fields.Float(string='Balance Amount', required=True)

    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True)
    name = fields.Date(string='Date', required=True, index=True, default=lambda self: fields.Date.today())
    salary_expense = fields.Float(string='Salary Expense ($)', required=False)
    rate_fifo = fields.Float(string='Rate (FIFO)', digits=(12, 12), compute="compute_rate", store=True)
    rate = fields.Float(string='Rate (Avg)', digits=(12, 12), store=True)
    # rate = fields.Float(string='Rate (Avg)', digits=(12, 12), compute="compute_rate", store=True)
    notes = fields.Text(string="Notes", required=False)

    x_swift_inward_ids = fields.One2many(comodel_name='swift.inward.history', inverse_name='x_rate_id',
                                         string='Swift Inward History', compute="compute_swift_inward", store=True)

    @api.depends('x_balance_amount')
    def compute_swift_inward(self):
        for rec in self:
            balance_amount = rec.x_balance_amount

            bank_statement_line_ids = self.env['account.bank.statement.line'].search([
                ('date', '>=', rec.x_date_from),
                ('date', '<=', rec.name),
                ('journal_id', '=', rec.x_journal_id.id),
                ('journal_entry_ids', '!=', False),
                ('x_invoice_ids', '!=', False),
                ('amount', '>', 0),
            ], order='date desc')

            invoice_data = []
            for bank_statement_line in bank_statement_line_ids:
                invoice_id = bank_statement_line.mapped('x_invoice_ids').ids[0]
                move_line_ids = bank_statement_line.journal_entry_ids.mapped('move_id').mapped('line_ids')
                receivable_move_ids = move_line_ids.filtered(
                    lambda l: l.account_id.id == self.env.ref('customizations.account_account_receivable').id
                )
                receivable_amount = sum(receivable_move_ids.mapped('credit')) - sum(receivable_move_ids.mapped('debit'))
                if balance_amount > bank_statement_line.amount:
                    invoice_data.append((0, 0, {
                        'x_date': bank_statement_line.date,
                        'x_invoice_id': invoice_id,
                        'x_amount': receivable_amount,
                        'x_amount_currency': bank_statement_line.amount,
                    }))
                    balance_amount -= bank_statement_line.amount
                elif balance_amount != 0:
                    invoice_data.append((0, 0, {
                        'x_date': bank_statement_line.date,
                        'x_invoice_id': invoice_id,
                        'x_amount': receivable_amount * balance_amount / bank_statement_line.amount,
                        'x_amount_currency': balance_amount,
                    }))
                    break

            rec.x_swift_inward_ids = [(2, line.id) for line in rec.x_swift_inward_ids]
            rec.x_swift_inward_ids = invoice_data

    @api.depends('x_date_from')
    def compute_amounts(self):
        for rec in self:
            in_amount_ids = self.env['account.move.line'].search([
                ('account_id', '=', rec.x_account_id.id), ('date', '>=', rec.x_date_from), ('amount_currency', '>', 0),
            ])
            out_amount_ids = self.env['account.move.line'].search([
                ('account_id', '=', rec.x_account_id.id), ('date', '>=', rec.x_date_from), ('amount_currency', '<', 0)
            ])

            rec.x_in_amount = sum(in_amount_ids.mapped('amount_currency'))
            rec.x_out_amount = sum(out_amount_ids.mapped('amount_currency'))
            balance_amount = rec.x_in_amount + rec.x_out_amount
            rec.x_balance_amount = balance_amount

    # @api.depends('x_balance_amount')
    # def compute_swift_inward_01(self):
    #     for rec in self:
    #         in_amount_ids = self.env['account.move.line'].search([
    #             ('account_id', '=', rec.x_account_id.id), ('date', '>=', rec.x_date_from), ('amount_currency', '>', 0),
    #         ])
    #         balance_amount = rec.x_balance_amount
    #
    #         invoice_data = []
    #
    #         invoice_ids = self.env['account.move'].search([
    #             ('state', '=', 'posted'),
    #             ('invoice_payment_state', '=', 'paid'),
    #             ('type', 'in', ('out_invoice', 'out_refund', 'out_receipt')),
    #             ('x_payment_method.default_debit_account_id', '=', rec.x_account_id.id),
    #         ])
    #
    #         for invoice in invoice_ids:
    #             invoice_line_ids = invoice.line_ids.filtered(lambda l: l.full_reconcile_id)
    #             for invoice_line in invoice_line_ids:
    #                 line_ids = invoice_line.full_reconcile_id.reconciled_line_ids.mapped('move_id').mapped('line_ids')
    #                 bank_line_ids = line_ids.filtered(lambda l: l.id in in_amount_ids.ids)
    #                 for bank_line in bank_line_ids:
    #                     if balance_amount > bank_line.amount_currency:
    #                         invoice_data.append((0, 0, {
    #                             'x_date': bank_line.date,
    #                             'x_invoice_id': invoice.id,
    #                             'x_amount': bank_line.balance if len(bank_line_ids) > 1 else invoice_line.balance,
    #                             'x_amount_currency': bank_line.amount_currency,
    #                         }))
    #                         balance_amount -= bank_line.amount_currency
    #                     elif balance_amount != 0:
    #                         amount = bank_line.balance if len(bank_line_ids) > 1 else invoice_line.balance
    #                         amount_currency = bank_line.amount_currency
    #                         rate = amount_currency / amount
    #                         invoice_data.append((0, 0, {
    #                             'x_date': bank_line.date,
    #                             'x_invoice_id': invoice.id,
    #                             'x_amount': balance_amount / rate,
    #                             'x_amount_currency': balance_amount,
    #                         }))
    #                         balance_amount = 0
    #
    #         rec.x_swift_inward_ids = [(2, line.id) for line in rec.x_swift_inward_ids]
    #         rec.x_swift_inward_ids = invoice_data

    @api.depends('salary_expense', 'x_swift_inward_ids.x_amount', 'x_swift_inward_ids.x_amount_currency')
    def compute_rate(self):
        for rec in self:
            salary_expense = rec.salary_expense
            amount = 0
            amount_currency = 0
            for line in reversed(rec.x_swift_inward_ids):
                if salary_expense > line.x_amount:
                    amount += line.x_amount
                    amount_currency += line.x_amount_currency
                    salary_expense -= line.x_amount
                else:
                    amount += salary_expense
                    amount_currency += salary_expense * line.x_rate
                    break
            rec.rate_fifo = amount_currency / amount if amount != 0 else 0

            # amount = sum(rec.x_swift_inward_ids.mapped('x_amount'))
            # amount_currency = sum(rec.x_swift_inward_ids.mapped('x_amount_currency'))
            # rec.rate = amount_currency / amount if amount != 0 else 0

    def unlink(self):
        self.x_swift_inward_ids.unlink()
        return super(PayrollCurrencyRates, self).unlink()


class SwiftInwardHistory(models.Model):
    _name = 'swift.inward.history'
    _description = 'Swift Inward History'
    _rec_name = 'x_invoice_id'
    _order = 'x_date desc'

    x_rate_id = fields.Many2one(comodel_name='payroll.currency.rate', string='Currency Rate', required=False)

    x_date = fields.Date(string='Date', required=False)
    x_invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice #', required=False)
    x_amount = fields.Float(string='Amount', required=False)
    x_amount_currency = fields.Float(string='Amount Currency', required=False)
    x_rate = fields.Float(string='Rate', digits=(12, 12), compute="compute_rate", store=True)

    @api.depends('x_amount', 'x_amount_currency')
    def compute_rate(self):
        for rec in self:
            rec.x_rate = rec.x_amount_currency / rec.x_amount if rec.x_amount != 0 else 0




