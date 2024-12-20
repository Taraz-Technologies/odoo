from odoo import fields, api, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    x_short_code = fields.Char(string='Short Code', required=False)

    x_hide_paid_banner = fields.Boolean(string='Remove Paid Banner from Bills/Invoices', required=False)
    x_remove_down_payment_lines = fields.Boolean(string='Remove Down Payment Lines', required=False)

    x_create_bills = fields.Boolean(string='Create Related Bills', required=False)
    x_attach_invoices = fields.Boolean(string='Attach Invoices', required=False)
    x_attach_pickings = fields.Boolean(string='Attach DOs/ROs', required=False)

    x_product_ids = fields.Many2many(comodel_name='product.product', string='Journal Products')


class Account(models.Model):
    _name = 'account.account'
    _inherit = ['account.account', 'mail.thread', 'mail.activity.mixin']

    x_gl_type_id = fields.Many2one(comodel_name='account.account.gl.type', string='Account GL Type', required=True)
    x_gl_group_id = fields.Many2one(related="x_gl_type_id.x_gl_group_id", store=True)

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Help Tags')
    x_parent_id = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]",
                                  string='Parent Account', compute="_compute_parent_account", store=True, tracking=True)
    x_parent_id_1 = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]", store=True, tracking=True)
    x_parent_id_2 = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]", store=True, tracking=True)
    x_parent_id_3 = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]", store=True, tracking=True)
    x_parent_id_4 = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]", store=True, tracking=True)
    x_parent_id_5 = fields.Many2one(comodel_name='account.account', domain="[('company_id', '=', company_id)]", store=True, tracking=True)

    write_uid = fields.Many2one(
        'res.users', 'Last Updated By',
        index=True,
        readonly=True,
        copy=False,
    )

    move_line_ids = fields.One2many(
        comodel_name='account.move.line',  # Related model name
        inverse_name='account_id',  # Related field name on the 'account.move.line' model
        string='Journal Items'
    )

    x_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='account_account_account_journal_rel_2',
        column1='account_account_id',
        column2='account_journal_id',
        string='Journals',
        compute='_compute_journals',
        store=True
    )

    x_is_otb_account = fields.Boolean(string='OTB Account?', required=False)
    x_main_account_id = fields.Many2one(comodel_name='account.account', string='ITB Account', required=False)

    @api.onchange('x_is_otb_account')
    def _update_account_move_line_is_otb_account(self):
        for rec in self:
            rec.move_line_ids.update({'x_is_otb_account': rec.x_is_otb_account})

    @api.onchange('x_main_account_id')
    def _update_account_move_line_main_account_id(self):
        for rec in self:
            rec.move_line_ids.update({'x_main_account_id': rec.x_main_account_id.id})

    @api.onchange('x_main_account_id.user_type_id')
    def _update_account_move_line_main_account_type(self):
        for rec in self:
            rec.move_line_ids.update({'x_main_account_type': rec.x_main_account_id.user_type_id.id})

    @api.onchange('x_gl_type_id')
    def _update_account_move_line_gl_type_id(self):
        for rec in self:
            rec.move_line_ids.update({'x_gl_type_id': rec.x_gl_type_id.id})

    @api.onchange('x_gl_type_id.x_gl_group_id')
    def _update_account_move_line_gl_group_id(self):
        for rec in self:
            rec.move_line_ids.update({'x_gl_group_id': rec.x_gl_type_id.x_gl_group_id.id})

    @api.depends('move_line_ids.journal_id')
    def _compute_journals(self):
        for rec in self:
            journal_ids = rec.move_line_ids.mapped('journal_id.id')
            rec.x_journal_ids = [(6, 0, journal_ids)]

    @api.onchange('x_is_otb_account')
    def reset_main_account(self):
        for rec in self:
            if not rec.x_is_otb_account:
                rec.x_main_account_id = False

    @api.constrains('name')
    def _constraint_name(self):
        account_ids = self.env['account.account'].search([
            ('name', '=', self.name), ('company_id', '=', self.company_id.id)
        ])
        if len(account_ids) != 1:
            raise UserError('The name of the account must be unique per company!')

    @api.depends('code')
    def _compute_parent_account(self):
        for rec in self:
            if not rec.code:
                rec.x_parent_id = False
                return
            account_ids = self.env['account.account'].search([('company_id', '=', rec.company_id.id)])
            account_ids = account_ids.filtered(lambda l: l.code in rec.code and l.code != rec.code)
            if account_ids:
                codes = [code for code in account_ids.mapped('code') if code == rec.code[0: len(code)]]
                rec.x_parent_id = self.env['account.account'].search([('code', '=', max(codes, key=len)), ('company_id', '=', rec.company_id.id)]).id
            else:
                rec.x_parent_id = False
            y = 1
            for x in range(len(rec.code)):
                account_id = self.env['account.account'].search([('code', '=', rec.code[0: x]), ('company_id', '=', rec.company_id.id)])
                if account_id:
                    rec['x_parent_id_%s' % y] = account_id.id
                    if y != 5:
                        y += 1
                    else:
                        break


class AccountGlGroup(models.Model):
    _name = "account.account.gl.group"
    _description = "Account GL Group"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=True)


class AccountGlType(models.Model):
    _name = "account.account.gl.type"
    _description = "Account Gl Type"
    _rec_name = "display_name"

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)
    x_name = fields.Char(string='Name', required=True)
    x_gl_group_id = fields.Many2one(comodel_name='account.account.gl.group', string='Account GL Group', required=True)

    @api.depends('x_name', 'x_gl_group_id', 'x_gl_group_id.x_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s (%s)" % (rec.x_name, rec.x_gl_group_id.x_name)







