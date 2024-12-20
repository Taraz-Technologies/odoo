from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


def prepare_account_values(code, name, user_type_id, rec_id=False):
    vals = {
        'code': code,
        'name': name,
        'user_type_id': user_type_id,
        'company_id': 2,
        'reconcile': True,
        'x_partner_id': rec_id,
    }
    return vals


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Individual with company (Ignore)
    # Individual without company or company
    @api.constrains('name', 'parent_id')
    def _constraint_name(self):
        if not self.parent_id:
            domain = [('name', '=', self.name), ('parent_id', '=', False)]
            if self.search_count(domain) > 1:
                raise UserError('Contact Name already exist!')
        else:
            domain = [('name', '=', self.name), ('parent_id', '=', self.parent_id.id)]
            if self.search_count(domain) > 1:
                raise UserError('Contact Name already exist!')

    def _get_customer_advance_account(self):
        return 463 if self.env.company.id == 1 else 952

    def _get_vendor_advance_account(self):
        return 430 if self.env.company.id == 1 else 838

    x_company_id = fields.Many2one(
        comodel_name='res.company', string='Accounts Company', required=True,
        default=lambda self: self.env.company, tracking=True,
    )

    x_customer_advance_account_id = fields.Many2one(
        comodel_name='account.account', string='Acct. Customer Adv.',
        domain=lambda self: [('user_type_id', '=', self.env.ref('account.data_account_type_current_liabilities').id)],
        default=_get_customer_advance_account, company_dependent=True, required=False, tracking=True
    )
    x_vendor_advance_account_id = fields.Many2one(
        comodel_name='account.account', string='Acct. Vendor Adv.',
        domain=lambda self: [('user_type_id', '=', self.env.ref('account.data_account_type_current_assets').id)],
        default=_get_vendor_advance_account, company_dependent=True, required=False, tracking=True
    )
    x_free_zone_contact = fields.Boolean(string='Free Zone Contact', required=False)
    x_sub_code = fields.Char(string='Sub Code', required=False)

    def _get_account_sub_code(self):
        for rec in self:
            if rec.country_id.id == self.env.ref('base.tr').id:
                if rec.x_free_zone_contact:
                    sub_code = '003.'
                else:
                    sub_code = '001.'
            else:
                sub_code = '002.'
            return sub_code

    def _add_account_sub_code(self, code):
        for rec in self:
            if rec.country_id.id == self.env.ref('base.tr').id:
                if rec.x_free_zone_contact:
                    code += '003.'
                else:
                    code += '001.'
            else:
                code += '002.'
        return code

    def _get_account_code(self, code_prefix):
        account_ids = self.env['account.account'].search([('code', 'ilike', code_prefix)])
        if [
            int(code.replace(code_prefix, '')) for code in account_ids.mapped('code') if
            code.replace(code_prefix, '').isnumeric()
        ]:
            code_number = max([int(code.replace(code_prefix, '')) for code in account_ids.mapped('code') if
                               code.replace(code_prefix, '').isnumeric()]) + 1
        else:
            code_number = 1
        code_number = '000%s' % code_number
        code = '%s%s' % (code_prefix, code_number[-3:])
        return code

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        res.create_related_accounts()
        return res

    def create_related_accounts(self):
        if self.parent_id or not self.name:
            return
        allowed_company_ids = self.env.context.get('allowed_company_ids', False)
        if not allowed_company_ids:
            allowed_company_ids = self.env.company.ids
        for company in allowed_company_ids:
            if company == 1:
                self = self.with_context(force_company=company, company_id=company)
                self.property_account_payable_id = 443
                self.property_account_receivable_id = 405
                self.x_customer_advance_account_id = 463
                self.x_vendor_advance_account_id = 430
            elif company == 2:
                # Assign default accounts on creation or when contact company is Pakistan
                self = self.with_context(force_company=company, company_id=company)
                if not self.property_account_payable_id or self.x_company_id.id == 1:
                    self.property_account_payable_id = 784
                if not self.property_account_receivable_id or self.x_company_id.id == 1:
                    self.property_account_receivable_id = 769
                if not self.x_customer_advance_account_id or self.x_company_id.id == 1:
                    self.x_customer_advance_account_id = 952
                if not self.x_vendor_advance_account_id or self.x_company_id.id == 1:
                    self.x_vendor_advance_account_id = 838
                if self.x_company_id.id == 1:
                    self.env['account.account'].search([
                        '|', ('x_partner_id', '=', self.id), ('name', 'ilike', self.name),
                    ]).unlink()
        if self.x_company_id.id == 2:
            self = self.with_context(force_company=self.x_company_id.id, company_id=self.x_company_id.id)
            # Account Receivable
            receivable = '%s (receivable)' % self.name
            if (
                    (
                            self.property_account_receivable_id.x_partner_id.id != self.id
                            and self.property_account_receivable_id.name != receivable
                    )
                    and self.x_partner_type == 'Customer'
            ):
                self.property_account_receivable_id = self.env['account.account'].sudo().create(
                    prepare_account_values(
                        self._get_account_code(self._add_account_sub_code('120.')),
                        receivable,
                        1,
                        self.id
                    )
                ).id
            elif (
                    (
                            self.property_account_receivable_id.x_partner_id.id == self.id
                            or self.property_account_receivable_id.name == receivable
                    )
                    and self.x_sub_code != self._get_account_sub_code()
                    and self.x_partner_type == 'Customer'
            ):
                self.property_account_receivable_id.code = self._get_account_code(self._add_account_sub_code('120.'))
            elif (
                    (
                            self.property_account_receivable_id.x_partner_id.id != self.id
                            and self.property_account_receivable_id.name != receivable
                    )
                    and self.x_partner_type == 'Vendor'
            ):
                self.property_account_receivable_id = self.env['account.account'].sudo().create(
                    prepare_account_values(
                        self._get_account_code(self._add_account_sub_code('127.')),
                        receivable,
                        1,
                        self.id,
                    )
                ).id
            elif (
                    (
                            self.property_account_receivable_id.x_partner_id.id == self.id
                            or self.property_account_receivable_id.name == receivable
                    )
                    and self.x_sub_code != self._get_account_sub_code()
                    and self.x_partner_type == 'Vendor'
            ):
                self.property_account_receivable_id.code = self._get_account_code(self._add_account_sub_code('127.'))
            # Account Payable
            payable = '%s (payable)' % self.name
            if (
                    (
                            self.property_account_payable_id.x_partner_id.id != self.id
                            and self.property_account_payable_id.name != payable
                    )
                    and self.x_partner_type == 'Vendor'
            ):
                self.property_account_payable_id = self.env['account.account'].sudo().create(
                    prepare_account_values(
                        self._get_account_code(self._add_account_sub_code('320.')),
                        payable,
                        2,
                        self.id,
                    )
                ).id
            elif (
                    (
                            self.property_account_payable_id.x_partner_id.id == self.id
                            or self.property_account_payable_id.name == payable
                    )
                    and self.x_sub_code != self._get_account_sub_code()
                    and self.x_partner_type == 'Vendor'
            ):
                self.property_account_payable_id.code = self._get_account_code(self._add_account_sub_code('320.'))
            elif (
                    (
                            self.property_account_payable_id.x_partner_id.id != self.id
                            and self.property_account_payable_id.name != payable
                    )
                    and self.x_partner_type == 'Customer'
            ):
                self.property_account_payable_id = self.env['account.account'].sudo().create(
                    prepare_account_values(
                        self._get_account_code(self._add_account_sub_code('329.')),
                        payable,
                        2,
                        self.id,
                    )
                ).id
            elif (
                    (
                            self.property_account_payable_id.x_partner_id.id == self.id
                            or self.property_account_payable_id.name == payable
                    )
                    and self.x_sub_code != self._get_account_sub_code()
                    and self.x_partner_type == 'Customer'
            ):
                self.property_account_payable_id.code = self._get_account_code(self._add_account_sub_code('329.'))
            # Customer Advance Account
            if (
                    self.x_customer_advance_account_id.x_partner_id.id != self.id
                    and self.x_customer_advance_account_id.name != '%s (unearned revenue)' % self.name
            ):
                code = self._get_account_code(self._add_account_sub_code('340.'))
                account_vals = prepare_account_values(code, '%s (unearned revenue)' % self.name, 9, self.id)
                account_id = self.env['account.account'].sudo().create(account_vals)
                self.x_customer_advance_account_id = account_id.id
            # Vendor Advance Account
            if (
                    self.x_vendor_advance_account_id.x_partner_id.id != self.id
                    and self.x_vendor_advance_account_id.name != '%s (advance)' % self.name
            ):
                code = self._get_account_code(self._add_account_sub_code('159.'))
                account_vals = prepare_account_values(code, '%s (advance)' % self.name, 5, self.id)
                account_id = self.env['account.account'].sudo().create(account_vals)
                self.x_vendor_advance_account_id = account_id.id
            # Update Accounts name
            if self.property_account_receivable_id.x_partner_id.id == self.id:
                self.property_account_receivable_id.name = '%s (receivable)' % self.name
            if self.property_account_payable_id.x_partner_id.id == self.id:
                self.property_account_payable_id.name = '%s (payable)' % self.name
            if self.x_customer_advance_account_id.x_partner_id.id == self.id:
                self.x_customer_advance_account_id.name = '%s (unearned revenue)' % self.name
            if self.x_vendor_advance_account_id.x_partner_id.id == self.id:
                self.x_vendor_advance_account_id.name = '%s (advance)' % self.name
            self.x_sub_code = self._get_account_sub_code()

    def write(self, vals):
        if vals.get('name') is not None:
            for rec in self:
                if rec.property_account_receivable_id.x_partner_id.id == rec.id:
                    rec.property_account_receivable_id.name = '%s (receivable)' % vals.get('name')
                if rec.property_account_payable_id.x_partner_id.id == rec.id:
                    rec.property_account_payable_id.name = '%s (payable)' % vals.get('name')
                if rec.x_customer_advance_account_id.x_partner_id.id == rec.id:
                    rec.x_customer_advance_account_id.name = '%s (unearned revenue)' % vals.get('name')
                if rec.x_vendor_advance_account_id.x_partner_id.id == rec.id:
                    rec.x_vendor_advance_account_id.name = '%s (advance)' % vals.get('name')
        return super(ResPartner, self).write(vals)

    def unlink(self):
        for rec in self:
            account_ids = []
            if rec.property_account_receivable_id.x_partner_id.id == rec.id:
                account_ids.append(rec.property_account_receivable_id.id)
                rec.property_account_receivable_id = False
            if rec.property_account_payable_id.x_partner_id.id == rec.id:
                account_ids.append(rec.property_account_payable_id.id)
                rec.property_account_payable_id = False
            if rec.x_customer_advance_account_id.x_partner_id.id == rec.id:
                account_ids.append(rec.x_customer_advance_account_id.id)
                rec.x_customer_advance_account_id = False
            if rec.x_vendor_advance_account_id.x_partner_id.id == rec.id:
                account_ids.append(rec.x_vendor_advance_account_id.id)
                rec.x_vendor_advance_account_id = False
            self.env['account.account'].browse(account_ids).unlink()
        return super(ResPartner, self).unlink()
