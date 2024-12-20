from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, date_utils

import json
import babel
import datetime

from calendar import monthrange
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
import logging

_logger = logging.getLogger("*__addons_custom__*")


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    x_currency_id = fields.Many2one(related="slip_id.x_currency_id")
    x_amount_currency = fields.Float(string='Amount Currency', compute="compute_amount_currency", store=True)

    @api.depends('total', 'slip_id.x_payroll_rate_id', 'slip_id.x_rate')
    def compute_amount_currency(self):
        for rec in self:
            rec.x_amount_currency = round(rec.total * rec.slip_id.x_rate, 0)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'employee_id'

    x_slip_type = fields.Selection(selection=[
        ('Normal', 'Normal'), ('Advance', 'Advance'), ('Loan', 'Loan'), ('Bonus', 'Bonus'),
    ], string="Slip Type", default='Normal', readonly=True, tracking=True, states={'draft': [('readonly', False)]})
    x_payment_date = fields.Date(string="Payment Date", tracking=True, store=True,
                                 groups="account.group_account_invoice", compute="compute_payment_date")
    x_wht_cpr_number = fields.Char(string="WHT CPR#", required=False, tracking=True)
    x_payment_journal_id = fields.Many2one("account.journal", "Payment Method", store=True, default=7, tracking=True)
    x_show_balance_in_report = fields.Boolean(string='Show Bal. in Report', required=False)
    x_hide_in_banking_document = fields.Boolean(string="Hide in Banking Document", required=False)

    currency_id = fields.Many2one(related="company_id.currency_id")
    x_currency_id = fields.Many2one(related='journal_id.currency_id', string="Currency")

    x_work_days_of_month = fields.Integer(string="Working Days", tracking=True,
                                          readonly=True, states={'draft': [('readonly', False)]})
    x_loan = fields.Float(string="Loan", required=False, tracking=True,
                          readonly=True, states={'draft': [('readonly', False)]})
    x_loan_return = fields.Float(string="Loan Return", required=False, readonly=True,
                                 states={'draft': [('readonly', False)]}, tracking=True)
    x_loan_contract_id = fields.Many2one(comodel_name='hr.loans', string="Loan Contract", reaonly=True)
    x_payroll_rate_id = fields.Many2one('payroll.currency.rate', 'Conversion Rate', required=True,
                                        readonly=True, tracking=True, states={'draft': [('readonly', False)]})
    x_rate = fields.Float(related="x_payroll_rate_id.rate", store=True, tracking=True, required=False, digits=(12, 12),
                          readonly=True, states={'draft': [('readonly', False)]})
    x_payments = fields.Text(string="Payments", compute="compute_registered_payments",
                             groups="account.group_account_invoice", tracking=True)

    x_deductions = fields.Float(string="Deduction Share", readonly=True,
                                states={'draft': [('readonly', False)]}, tracking=True)
    x_advance_currency = fields.Float(string="Advance Salary", readonly=True,
                                      states={'draft': [('readonly', False)]}, tracking=True)
    x_advance = fields.Float(string="Advance Salary", readonly=True,
                             states={'draft': [('readonly', False)]}, tracking=True)
    x_bonus = fields.Float(string="Bonus", required=False, readonly=True,
                           states={'draft': [('readonly', False)]}, tracking=True)
    x_fine = fields.Float(string="Fine", required=False, readonly=True,
                          states={'draft': [('readonly', False)]}, tracking=True)
    x_sick_leaves = fields.Float(string="Sick Leaves", required=False, readonly=True,
                                 states={'draft': [('readonly', False)]}, tracking=True)
    x_unpaid_leaves = fields.Float(string="Unpaid Leaves", required=False, readonly=True,
                                   states={'draft': [('readonly', False)]}, tracking=True)
    x_additional_wht_salary = fields.Float(string="Adjust Income Tax", readonly=True,
                                           states={'draft': [('readonly', False)]}, tracking=True)

    x_payslip_type = fields.Selection(selection=[
        ('payable', 'Payable'), ('receivable', 'Receivable'), ('net_zero', 'Net 0'),
    ], required=False, string='Payslip Type')

    x_amount = fields.Monetary(string='Amount (USD)', readonly=True, store=True)
    x_amount_payable = fields.Monetary(string='Amount Payable', readonly=True, store=True)
    x_amount_residual = fields.Monetary(string='Amount Due', readonly=True, store=True)

    salary_outstanding_credits_debits_widget = fields.Text(groups="account.group_account_invoice",
                                                           compute='_compute_payments_widget_to_reconcile_info')
    salary_payments_widget = fields.Text(groups="account.group_account_invoice",
                                         compute='_compute_payments_widget_reconciled_info')
    salary_has_outstanding = fields.Boolean(groups="account.group_account_invoice",
                                            compute='_compute_payments_widget_to_reconcile_info')

    x_salary_detail_ids = fields.One2many(comodel_name='salary.details', inverse_name='x_slip_id',
                                          string='Salary Details', compute="compute_salary_details", store=True)

    x_gross_salary = fields.Monetary(string="Gross Salary", compute="compute_salary_amounts", store=True)
    x_wht_salary = fields.Monetary(string="WHT Salary", compute="compute_salary_amounts", store=True)
    x_eobi = fields.Monetary(string="EOBI", compute="compute_salary_amounts", store=True)
    x_net_salary = fields.Monetary(string="Net Salary", compute="compute_salary_amounts", store=True)

    x_wht_category = fields.Char(string="WHT Category", default="Salary (149/3)", required=False)

    x_fiscal_year_start = fields.Date(string="Fiscal Year Start", required=False)
    x_fiscal_year_end = fields.Date(string="Fiscal Year End", required=False)

    x_taxable_income = fields.Monetary(string="Taxable Income", required=False)

    x_wht_payable = fields.Monetary(string="IT Payable", required=False)
    x_wht_deducted = fields.Monetary(string="IT Recovered", required=False)
    x_wht_recoverable = fields.Monetary(string="IT Recoverable", required=False)

    x_remaining_months = fields.Integer(string='Remaining Months', required=False)

    x_wht_current = fields.Monetary(string="IT Current Month", required=False)

    x_letter_head_report = fields.Boolean(string="Letter Head Report?")

    x_payslip_fine_ids = fields.One2many(comodel_name='hr.payslip.fines', inverse_name='x_payslip_id',
                                         string='Payslip Fines', compute="compute_payslip_data", store=True)
    x_fine_ids = fields.One2many(comodel_name='hr.fines', inverse_name='x_payslip_id', string='Fines',
                                 compute="compute_payslip_data", store=True)
    x_bonus_ids = fields.One2many(comodel_name='hr.bonus', inverse_name='x_payslip_id', string='Bonus',
                                  compute="compute_payslip_data", store=True)
    x_attendance_ids = fields.Many2many(comodel_name='hr.attendance', string='Attendance Fines',
                                        compute="compute_payslip_data", store=True)

    x_deduction_ids = fields.Many2many(comodel_name='hr.allowances.details', string='Deductions',
                                       compute="compute_payslip_data", store=True)

    x_loan_installment_ids = fields.Many2many(comodel_name='hr.loans.installments',
                                              compute="compute_payslip_data", store=True)

    x_payment_salary_payable = fields.Monetary(string='Payable Balance', groups="account.group_account_invoice",
                                               compute='compute_registered_payments', tracking=True)

    # ------------------------------------- ON CHANGE -------------------------------------
    @api.onchange('x_slip_type', 'employee_id', 'date_from', 'date_to')
    def update_salary_structure_and_name(self):
        for rec in self:
            # Compute Salary Structure
            if rec.x_slip_type == 'Normal':
                rec.struct_id = rec.contract_id.struct_id.id
            elif rec.x_slip_type == 'Loan':
                rec.struct_id = rec.contract_id.x_loan_structure.id
            elif rec.x_slip_type == 'Bonus':
                rec.struct_id = rec.contract_id.x_bonus_structure.id

            # Compute Slip Name
            ttyme = datetime.combine(fields.Date.from_string(rec.date_to), time.min)
            locale = rec.env.context.get('lang') or 'en_US'
            rec.name = _('%s Slip of %s for %s') % (
                rec.x_slip_type, rec.employee_id.name,
                tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
            )

    @api.onchange('x_payroll_rate_id')
    def onchange_rate_id(self):
        for rec in self:
            rec.x_rate = rec.x_payroll_rate_id.rate

    @api.onchange('contract_id', 'date_from', 'date_to')
    def calculate_work_days_of_month(self):
        for rec in self:
            if rec.date_to and rec.contract_id:
                days_of_month = monthrange(rec.date_to.year, rec.date_to.month)[1]
                date_from = date(rec.date_from.year, rec.date_from.month, 1)
                date_to = date(rec.date_to.year, rec.date_to.month, days_of_month)
                day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
                day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

                # compute leave days
                leave_days = 0
                calendar = rec.contract_id.resource_calendar_id
                tz = timezone(calendar.tz)
                day_leave_intervals = rec.employee_id.list_leaves(
                    day_from, day_to, calendar=rec.contract_id.resource_calendar_id
                )
                for day, hours, leave in day_leave_intervals:
                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        leave_days += hours / work_hours

                # compute worked days
                work_data = rec.employee_id._get_work_days_data(
                    day_from, day_to, calendar=rec.contract_id.resource_calendar_id
                )

                rec.x_work_days_of_month = work_data['days'] + leave_days

    @api.onchange('worked_days_line_ids')
    def get_leaves(self):
        for rec in self:
            sick_leaves = 0
            unpaid_leaves = 0
            for lines in rec.worked_days_line_ids:
                if 'Sick Time Off' in lines.code:
                    sick_leaves = lines.number_of_days
                elif 'Unpaid' in lines.code:
                    unpaid_leaves = lines.number_of_days
            rec.x_sick_leaves = sick_leaves
            rec.x_unpaid_leaves = unpaid_leaves

    # ------------------------------------- DEPENDS -------------------------------------
    @api.depends('line_ids', 'x_additional_wht_salary')
    def compute_salary_amounts(self):
        for rec in self:
            for line in rec.line_ids:
                if line.code == 'GROSS':
                    rec.x_gross_salary = line.x_amount_currency
                if line.name == 'WHT Salary':
                    rec.x_wht_salary = line.x_amount_currency + rec.x_additional_wht_salary
                if line.name == 'EOBI':
                    rec.x_eobi = line.x_amount_currency
                if line.code == 'NET':
                    rec.x_net_salary = line.x_amount_currency

    @api.depends('x_slip_type', 'employee_id', 'date_from', 'date_to', 'x_rate')
    def compute_payslip_data(self):
        for rec in self:
            # Compute Installments
            for installment in rec.x_loan_installment_ids:
                installment.x_loan_id.state = 'in_progress'
                installment.state = 'in_progress'
                installment.x_payslip_id = False
                installment.x_loan_id.x_amount_due = installment.x_loan_id.x_amount
                paid_amount = installment.x_loan_id.x_installment_ids.filtered(lambda l: l.state == 'paid')
                installment.x_loan_id.x_amount_due -= sum(paid_amount.mapped('x_amount'))

            rec.x_loan_installment_ids.write({'x_payslip_id': False})
            rec.x_loan_installment_ids = [(5, 0)]
            if rec.x_slip_type == 'Normal':
                installment_ids = self.env['hr.loans.installments'].search([
                    ('x_employee_id', '=', rec.employee_id.id),
                    ('x_payment_date', '>=', rec.date_from), ('x_payment_date', '<=', rec.date_to),
                    ('state', '=', 'in_progress'), ('x_payslip_id', '=', False)
                ])
                rec.x_loan_installment_ids = [(6, 0, installment_ids.ids)]

                rec.x_loan_return = 0
                if rec.x_loan_installment_ids.filtered(lambda l: l.x_currency_id.id != rec.currency_id.id):
                    rec.x_loan_return = sum(rec.x_loan_installment_ids.filtered(
                        lambda l: l.x_currency_id != rec.currency_id
                    ).mapped('x_amount')) / rec.x_rate if rec.x_rate else 0
                if rec.x_loan_installment_ids.filtered(lambda l: l.x_currency_id.id == rec.currency_id.id):
                    rec.x_loan_return += sum(rec.x_loan_installment_ids.filtered(
                        lambda l: l.x_currency_id.id == rec.currency_id.id
                    ).mapped('x_amount'))

                rec.x_loan_installment_ids.write({'x_payslip_id': rec._origin.id})

            # Deductions
            deduction_ids = self.env['hr.allowances.details'].search([
                ('x_employee_id', '=', rec.employee_id.id),
                ('x_date', '>=', rec.date_from), ('x_date', '<=', rec.date_to)
            ])
            rec.x_deduction_ids = deduction_ids.ids
            rec.x_deductions = sum(deduction_ids.mapped('x_deduction_amount'))

            # Bonus
            # Bonus in Local Currency
            bonus_ids = self.env['hr.bonus'].search([
                ('x_employee_id', '=', rec.employee_id.id), ('x_state', '=', 'not_paid'),
                ('x_due_date', '>=', rec.date_from), ('x_due_date', '<=', rec.date_to),
                ('x_currency_id', '=', rec.x_currency_id.id),
            ])
            rec.x_bonus_ids = [(6, 0, bonus_ids.ids)]
            rec.x_bonus = sum(bonus_ids.mapped('x_amount')) / rec.x_rate if rec.x_rate != 0 else 0
            # Bonus in Company Currency
            bonus_ids = self.env['hr.bonus'].search([
                ('x_employee_id', '=', rec.employee_id.id), ('x_state', '=', 'not_paid'),
                ('x_due_date', '>=', rec.date_from), ('x_due_date', '<=', rec.date_to),
                ('x_currency_id', '=', rec.currency_id.id),
            ])
            rec.x_bonus_ids = [(4, bonus.id) for bonus in bonus_ids]
            rec.x_bonus += sum(bonus_ids.mapped('x_amount'))

            # Manual Fines
            # Fine in Local Currency
            fine_ids = self.env['hr.fines'].search([
                ('x_employee_id', '=', rec.employee_id.id), ('x_state', '=', 'not_paid'),
                ('x_due_date', '>=', rec.date_from), ('x_due_date', '<=', rec.date_to),
                ('x_currency_id', '=', rec.x_currency_id.id),
            ])
            rec.x_fine_ids = [(6, 0, fine_ids.ids)]
            manual_fines = sum(fine_ids.mapped('x_amount')) / rec.x_rate if rec.x_rate != 0 else 0
            # Fine in Company Currency
            fine_ids = self.env['hr.fines'].search([
                ('x_employee_id', '=', rec.employee_id.id), ('x_state', '=', 'not_paid'),
                ('x_due_date', '>=', rec.date_from), ('x_due_date', '<=', rec.date_to),
                ('x_currency_id', '=', rec.currency_id.id),
            ])
            rec.x_fine_ids = [(4, fine.id) for fine in fine_ids]
            manual_fines += sum(fine_ids.mapped('x_amount'))

            payslip_fine_line = [(0, 0, {'x_name': "Manual Fines", 'x_amount': manual_fines})]

            # Attendance Fines
            date_from = datetime.combine(rec.date_from, datetime.min.time())
            date_to = datetime.combine(rec.date_to, datetime.max.time())
            attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.employee_id.id), ('check_in', '>=', date_from), ('check_in', '<=', date_to)
            ])

            late_coming_fine = sum(attendance_ids.mapped('x_late_coming_fine'))
            payslip_fine_line.append((0, 0, {'x_name': "Late Coming Fine", 'x_amount': late_coming_fine}))

            early_going_fine = sum(attendance_ids.mapped('x_early_going_fine'))
            payslip_fine_line.append((0, 0, {'x_name': "Early Going Fine", 'x_amount': early_going_fine}))

            rec.x_payslip_fine_ids = [(2, line.id) for line in rec.x_payslip_fine_ids]
            rec.x_payslip_fine_ids = payslip_fine_line

            rec.x_fine = sum(rec.x_payslip_fine_ids.mapped('x_amount'))

            attendance_ids = attendance_ids.filtered(lambda l: l.x_late_coming_fine != 0 or l.x_early_going_fine != 0)
            rec.x_attendance_ids = [(6, 0, attendance_ids.ids)]

    @api.depends('salary_payments_widget')
    def compute_registered_payments(self):
        for rec in self:
            if not rec.move_id:
                rec.x_payment_date = False
                rec.x_payments = False
                rec.x_payment_salary_payable = 0
                continue

            move_ids = [rec.move_id.id]

            slip_salary_payable = 0
            for line in rec.move_id.line_ids:
                if line.account_id.id == 444 and line.partner_id.id == rec.employee_id.user_partner_id.id:
                    slip_salary_payable += line.amount_currency

            payment_text = ""
            payment_date = rec.x_payment_date
            payment_salary_payable = 0

            payments = json.loads(rec.salary_payments_widget)
            if payments:
                for payment in payments['content']:
                    payment_text += '[%s, %s %s, %s]\n' % (payment['journal_name'], payment['currency'],
                                                           round(payment['amount'], 2), payment['date'])
                    payment_date = payment['date'] if payment['date'] else payment_date
                    move_id = self.env['account.move'].browse(payment['move_id'])
                    if move_id:
                        move_ids.append(move_id.id)
                        for line in move_id.line_ids:
                            if line.account_id.id == 444 and line.partner_id.id == rec.employee_id.user_partner_id.id:
                                payment_salary_payable += line.amount_currency

            rec.x_payment_date = payment_date
            rec.x_payments = payment_text

            other_move_ids = self.env['account.move'].search([('ref', 'ilike', rec.number), ('id', 'not in', move_ids)])
            other_salary_payable = 0
            for move_id in other_move_ids:
                for line in move_id.line_ids:
                    if line.account_id.id == 444 and line.partner_id.id == rec.employee_id.user_partner_id.id:
                        other_salary_payable = line.amount_currency

            if payment_salary_payable != 0:
                rec.x_payment_salary_payable = payment_salary_payable + slip_salary_payable + other_salary_payable
            else:
                rec.x_payment_salary_payable = payment_salary_payable

    @api.depends('x_payments')
    def compute_payment_date(self):
        for rec in self:
            payment_date = rec.x_payment_date
            payments = json.loads(rec.salary_payments_widget)
            if payments:
                for payment in payments['content']:
                    payment_date = payment['date'] if payment['date'] else rec.x_payment_date
            rec.x_payment_date = payment_date

    @api.depends('state', 'move_id.line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        for rec in self:
            if rec.state != 'done':
                rec.salary_payments_widget = json.dumps(False)
                continue

            reconciled_vals = rec.move_id._get_reconciled_info_JSON_values()
            if reconciled_vals:
                info = {
                    'title': _('Less Payment'),
                    'outstanding': False,
                    'content': reconciled_vals,
                }
                rec.salary_payments_widget = json.dumps(info, default=date_utils.json_default)
            else:
                rec.salary_payments_widget = json.dumps(False)

            rec.x_amount_residual = rec.x_amount_payable
            if reconciled_vals:
                for data in reconciled_vals:
                    rec.x_amount_residual -= data['amount']

    @api.depends('contract_id')
    def compute_salary_details(self):
        for rec in self:
            rec.x_salary_detail_ids = [(2, line.id) for line in rec.x_salary_detail_ids]
            salary_detail_ids = [(0, 0, {
                'x_name': 'Salary',
                'x_category': 'Salary',
                'x_amount': rec.contract_id.wage,
            })]
            for line in rec.contract_id.x_skill_increment_ids.filtered(lambda l: l.x_status == 'pass'):
                salary_detail_ids.append((0, 0, {
                    'x_name': line.x_name,
                    'x_category': 'Skill Increments',
                    'x_amount': line.x_amount,
                }))
            for line in rec.contract_id.x_allowance_ids:
                salary_detail_ids.append((0, 0, {
                    'x_name': line.x_name,
                    'x_category': 'Allowances',
                    'x_amount': line.x_amount,
                }))
            for line in rec.contract_id.x_increment_ids.filtered(lambda l: l.x_status == 'pass'):
                salary_detail_ids.append((0, 0, {
                    'x_name': line.x_name,
                    'x_category': 'Other Increments',
                    'x_amount': line.x_amount,
                }))
            rec.x_salary_detail_ids = salary_detail_ids

    # ------------------------------------- OTHER FUNCTION -------------------------------------

    def download_slip(self):
        return self.env.ref('om_hr_payroll.action_report_payslip').report_action(self)

    def compute_fiscal_year_income(self):
        for rec in self:
            fiscal_year_start = datetime(rec.date.year - 1, 7, 1) if rec.date.month <= 6 else datetime(rec.date.year, 7, 1)
            fiscal_year_end = datetime(rec.date.year, 6, 30) if rec.date.month <= 6 else datetime(rec.date.year + 1, 6, 30)

            fiscal_year_previous_slips = self.env['hr.payslip'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('x_slip_type', '=', ('Normal', 'Bonus')), ('state', '=', 'done'),
                ('date', '>=', fiscal_year_start), ('date', '<', rec.date)]
            )

            taxable_income = sum(fiscal_year_previous_slips.mapped('x_gross_salary'))
            remaining_months = 6 - rec.date.month if rec.date.month < 6 else 18 - rec.date.month

            rec.compute_salary_amounts()
            taxable_income += rec.x_gross_salary * remaining_months
            wht_payable = 0
            # FY 2023-24
            if datetime(year=2023, month=7, day=1).date() <= rec.date <= datetime(year=2024, month=6, day=30).date():
                if 600000 < taxable_income <= 1200000:
                    wht_payable = round((taxable_income - 600000) * 0.025, 0)
                elif 1200000 < taxable_income <= 2400000:
                    wht_payable = round((15000 + (taxable_income - 1200000) * 0.125), 0)
                elif 2400000 < taxable_income <= 3600000:
                    wht_payable = round((165000 + (taxable_income - 2400000) * 0.225), 0)
                elif 3600000 < taxable_income <= 6000000:
                    wht_payable = round((435000 + (taxable_income - 3600000) * 0.275), 0)
                elif 6000000 < taxable_income <= 12000000:
                    wht_payable = round((1095000 + (taxable_income - 6000000) * 0.35), 0)
            # FY 2024-25
            elif datetime(year=2024, month=7, day=1).date() <= rec.date <= datetime(year=2025, month=6, day=30).date():
                if 600000 < taxable_income <= 1200000:
                    wht_payable = round((taxable_income - 600000) * 0.05, 0)
                elif 1200000 < taxable_income <= 2200000:
                    wht_payable = round((30000 + (taxable_income - 1200000) * 0.15), 0)
                elif 2200000 < taxable_income <= 3200000:
                    wht_payable = round((180000 + (taxable_income - 2200000) * 0.25), 0)
                elif 3200000 < taxable_income <= 4100000:
                    wht_payable = round((430000 + (taxable_income - 3200000) * 0.30), 0)
                elif 4100000 < taxable_income:
                    wht_payable = round((700000 + (taxable_income - 4100000) * 0.35), 0)
            else:
                raise UserError("Income Tax formulas for fiscal year of accounting date %s is not defined!" % rec.date)

            wht_deducted = sum(fiscal_year_previous_slips.mapped('x_wht_salary'))

            wht_recoverable = wht_payable - wht_deducted if wht_payable - wht_deducted > 0 else 0
            wht_current = round(wht_recoverable / remaining_months, 0) if remaining_months != 0 else 0

            rec.update({
                'x_fiscal_year_start': fiscal_year_start,
                'x_fiscal_year_end': fiscal_year_end,
                'x_taxable_income': taxable_income,
                'x_wht_payable': wht_payable,
                'x_wht_deducted': wht_deducted,
                'x_wht_recoverable': wht_recoverable,
                'x_remaining_months': remaining_months,
                'x_wht_current': wht_current,
            })

    def action_balance_payable(self):
        for rec in self:
            try:
                payments = json.loads(rec.salary_payments_widget)
                if payments:
                    for payment in payments['content']:
                        salary_payable = 0
                        move_id = self.env['account.move'].browse(payment['move_id'])
                        for line in move_id.line_ids:
                            if line.account_id.id == 444 and line.partner_id.id == rec.employee_id.user_partner_id.id:
                                salary_payable = line.amount_currency
                        if salary_payable != payment['amount']:
                            return self.env['account.payment'].with_context(
                                active_ids=[move_id.id], active_model='account.move', active_id=move_id.id,
                                slip_id=rec.id
                            ).action_register_payment()
            finally:
                rec.compute_registered_payments()

    def get_payment_vals(self):
        for rec in self:
            balance = rec.x_net_salary
            payments = json.loads(rec.salary_payments_widget)
            if payments:
                for payment in payments['content']:
                    paid_from = 'Bank Alfalah' if 'Bank Alfalah' in payment['journal_name'] else 'Cash'
                    payment['paid_from'] = 'Paid from %s on %s' % (paid_from, payment['date'])
                    move_id = self.env['account.move'].browse(payment['move_id'])
                    for line in move_id.line_ids:
                        if line.account_id.id == 444 and line.partner_id.id == rec.employee_id.user_partner_id.id:
                            payment['payment_amount'] = line.amount_currency
                            balance -= payment['payment_amount']
                for payment in payments['content']:
                    payment['balance'] = balance
                return payments['content']

    def _compute_payments_widget_to_reconcile_info(self):
        for rec in self:
            rec.salary_outstanding_credits_debits_widget = json.dumps(False)
            rec.salary_has_outstanding = False

            if rec.employee_id and not rec.employee_id.user_partner_id:
                raise UserError("Error! %s's user is not defined!" % rec.employee_id.name)

            if rec.state != 'done':
                continue
            pay_term_line_ids = rec.move_id.line_ids.filtered(
                lambda l: l.account_id.user_type_id.type in ('receivable', 'payable'))

            domain = [('account_id', 'in', pay_term_line_ids.mapped('account_id').ids),
                      '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'),
                      ('journal_id.post_at', '=', 'bank_rec'),
                      ('partner_id', '=', rec.employee_id.user_partner_id.id),
                      ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                      ('amount_residual_currency', '!=', 0.0)]

            if rec.x_payslip_type == 'receivable':
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')

            info = {'title': '', 'outstanding': True, 'content': [], 'move_id': rec.move_id.id}

            lines = self.env['account.move.line'].search(domain)

            currency_id = rec.move_id.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == rec.move_id.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency = line.company_id.currency_id
                        amount_to_show = currency._convert(abs(line.amount_residual), rec.move_id.currency_id,
                                                           rec.move_id.company_id, line.date or fields.Date.today())

                    if float_is_zero(amount_to_show, precision_rounding=rec.move_id.currency_id.rounding):
                        continue
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, rec.move_id.currency_id.decimal_places],
                        'payment_date': fields.Date.to_string(line.date),
                    })
                info['title'] = type_payment
                rec.salary_outstanding_credits_debits_widget = json.dumps(info)
                rec.salary_has_outstanding = True

    def compute_sheet(self):
        for rec in self:
            rec.compute_payslip_data()
            rec.compute_fiscal_year_income()
        super(HrPayslip, self).compute_sheet()
        for rec in self:
            rec.compute_payslip_data()
            for line in rec.line_ids:
                if line.category_id.name == 'Net':
                    if line.total > 0:
                        rec.x_payslip_type = 'payable'
                        rec.x_amount = line.total
                        rec.x_amount_payable = line.x_amount_currency
                        rec.x_amount_residual = line.x_amount_currency
                    elif line.total < 0 or rec.credit_note:
                        rec.x_payslip_type = 'receivable'
                        rec.x_amount = -line.total
                        rec.x_amount_payable = -line.x_amount_currency
                        rec.x_amount_residual = -line.x_amount_currency
                    else:
                        rec.x_payslip_type = 'net_zero'
                        rec.x_amount = line.total
                        rec.x_amount_payable = line.x_amount_currency
                        rec.x_amount_residual = line.x_amount_currency

    def action_salary_register_payment(self):
        return self.env['account.payment'].with_context(
            active_ids=[self.move_id.id], active_model='account.move', active_id=self.move_id.id, slip_id=self.id
        ).action_register_payment()

    def action_payslip_cancel(self):
        res = super(HrPayslip, self).action_payslip_cancel()
        for rec in self:
            rec.x_fine_ids.write({
                'x_state': 'not_paid',
                'x_payslip_id': False,
            })
            rec.x_bonus_ids.write({
                'x_state': 'not_paid',
                'x_payslip_id': False,
            })
            if rec.x_loan_contract_id.x_installment_ids.filtered(lambda l: l.x_payslip_id):
                raise UserError('Contract installments are linked to payslips.')
            rec.x_loan_contract_id.write({'state': 'cancel'})
            rec.x_loan_contract_id.x_installment_ids.unlink()

            for installment in rec.x_loan_installment_ids:
                installment.x_loan_id.state = 'in_progress'
                installment.state = 'in_progress'
                installment.x_payslip_id = False
                installment.x_loan_id.x_amount_due = installment.x_loan_id.x_amount
                paid_amount = installment.x_loan_id.x_installment_ids.filtered(lambda l: l.state == 'paid')
                installment.x_loan_id.x_amount_due -= sum(paid_amount.mapped('x_amount'))
            rec.x_loan_installment_ids = [(5, 0)]
        return res

    def action_payslip_draft(self):
        res = super(HrPayslip, self).action_payslip_draft()
        for rec in self:
            rec.x_fine_ids.write({'x_state': 'not_paid'})
            rec.x_bonus_ids.write({'x_state': 'not_paid'})
            self.env['hr.benefits'].search([('x_payslip_id', '=', rec.id)]).unlink()
        return res

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            if rec.x_slip_type in ('Normal', 'Loan'):
                vals = [{
                    'x_payslip_id': rec.id,
                    'x_type': 'sal',
                    'x_amount': sum(
                        rec.line_ids.filtered(lambda l: l.category_id.name == 'Basic').mapped('x_amount_currency')),
                },{
                    'x_payslip_id': rec.id,
                    'x_type': 'sinc',
                    'x_amount': sum(rec.line_ids.filtered(lambda l: l.category_id.name == 'Skill Increments').mapped(
                        'x_amount_currency')),
                },{
                    'x_payslip_id': rec.id,
                    'x_type': 'alw',
                    'x_amount': sum(
                        rec.line_ids.filtered(lambda l: l.category_id.name == 'Allowance').mapped('x_amount_currency')),
                },{
                    'x_payslip_id': rec.id,
                    'x_type': 'inc',
                    'x_amount': sum(rec.line_ids.filtered(lambda l: l.category_id.name == 'Increments').mapped(
                        'x_amount_currency')),
                },{
                    'x_payslip_id': rec.id,
                    'x_type': 'bon',
                    'x_amount': sum(
                        rec.line_ids.filtered(lambda l: l.category_id.name == 'Bonus').mapped('x_amount_currency')),
                },{
                    'x_payslip_id': rec.id,
                    'x_type': 'lon',
                    'x_amount': sum(
                        rec.line_ids.filtered(lambda l: l.category_id.name == 'Loan').mapped('x_amount_currency')),
                }]
                self.env['hr.benefits'].create(vals)
            rec.x_fine_ids.write({'x_state': 'paid'})
            rec.x_bonus_ids.write({'x_state': 'paid'})
            rec.x_loan_contract_id.action_loan_done()
            rec.x_loan_installment_ids.write({'state': 'paid'})
            for installment in rec.x_loan_installment_ids:
                installment.x_loan_id.x_amount_due -= installment.x_amount
                if installment.x_loan_id.x_amount_due == 0:
                    installment.x_loan_id.state = 'paid'
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _order = 'x_payment_date desc'

    x_date = fields.Date(string='Accounting Date', readonly=True, required=True,
                         default=lambda self: fields.Date.to_string(date.today()),
                         states={'draft': [('readonly', False)]}, tracking=True)
    x_payment_date = fields.Date(string='Payment Date', required=True, tracking=True,
                                 default=lambda self: fields.Date.to_string(date.today()))
    x_currency_id = fields.Many2one(related='journal_id.currency_id', string="Currency")
    x_payroll_rate_id = fields.Many2one('payroll.currency.rate', 'Conversion Rate', required=True, tracking=True)
    x_rate = fields.Float(related="x_payroll_rate_id.rate", store=True, tracking=True, digits=(12, 12), readonly=False)

    x_letter_head_report = fields.Boolean(string='Letter Head Report?', required=False, )
    x_bank_id = fields.Many2one(comodel_name='res.bank', string='Bank', default=2)
    x_cheque_number = fields.Char(string='Cheque #', required=False)
    x_amount_in_words = fields.Char(string='Amount in Words', readonly=False, tracking=True,
                                    compute='_compute_amount_in_words', store=True)
    x_wht_salary_bill_id = fields.Many2one(comodel_name='account.move', string='WHT Salary Bill', required=False)

    def download_slips(self):
        return self.slip_ids.download_slip()

    @api.depends('slip_ids.x_amount_residual', 'slip_ids.x_hide_in_banking_document')
    def _compute_amount_in_words(self):
        for rec in self:
            amount = sum(rec.slip_ids.filtered(
                lambda l: l.employee_id.bank_account_id and not l.x_hide_in_banking_document
            ).mapped('x_amount_residual'))
            rec.x_amount_in_words = rec.x_currency_id.amount_to_text(amount)

    @api.model
    def default_get(self, fields_list):
        rec = super(HrPayslipRun, self).default_get(fields_list)
        rec.update({
            'name': 'Payslips Batch - (%s)' % date.today().strftime('%b-%Y')
        })
        return rec

    @api.onchange('date_end')
    def onchange_date_end(self):
        for rec in self:
            rec.name = 'Payslips Batch - (%s)' % rec.date_end.strftime('%b-%Y')

    @api.onchange('x_payment_date')
    def onchange_payment_date(self):
        for rec in self:
            rec.x_payroll_rate_id = self.env['payroll.currency.rate'].search([
                ('name', '=', rec.x_payment_date), ('currency_id', '=', rec.x_currency_id.id)
            ]).id

    @api.onchange('x_payroll_rate_id')
    def onchange_rate_id(self):
        for rec in self:
            rec.x_rate = rec.x_payroll_rate_id.rate
            rec.slip_ids.write({'x_payroll_rate_id': rec.x_payroll_rate_id.id, 'x_rate': rec.x_rate})
            rec.slip_ids.line_ids.compute_amount_currency()

    def compute_sheets(self):
        for rec in self:
            rec.x_payroll_rate_id.salary_expense = sum(rec.slip_ids.mapped('x_amount'))
            rec.slip_ids.update({
                'x_rate': rec.x_rate,
                'x_payroll_rate_id': rec.x_payroll_rate_id.id,
                'date': rec.x_date,
            })
            rec.slip_ids.compute_sheet()

    def create_wht_bill(self):
        for rec in self:
            fbr_partner_id = 77
            payment_bill_journal_id = 1
            bank_alfalah_journal_id = 7
            pkr_currency_id = 165
            tag_ids = self.env['custom.tags'].search([('x_name', '=', 'WHT - Salary')])
            vals = {
                'type': 'in_invoice',
                'partner_id': fbr_partner_id,
                'partner_shipping_id': fbr_partner_id,
                'x_purchase_type': 'Local',
                'x_item_type': 'Tax',
                'invoice_date': fields.date.today(),
                'date': fields.date.today(),
                'journal_id': payment_bill_journal_id,
                'x_payment_method': bank_alfalah_journal_id,
                'currency_id': pkr_currency_id,
                'x_tag_ids': tag_ids.ids,
                'invoice_line_ids': []
            }
            wht_salary_product_id = self.env['product.product'].browse([17005])
            for slip in rec.slip_ids:
                vals['invoice_line_ids'].append({
                    'product_id': wht_salary_product_id.id,
                    'name': slip.employee_id.name,
                    'account_id': wht_salary_product_id.property_account_expense_id.id,
                    'quantity': 1,
                    'product_uom_id': 1,
                    'price_unit': slip.x_wht_salary,
                })
            rec.x_wht_salary_bill_id = self.env['account.move'].create(vals).id

