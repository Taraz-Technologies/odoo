from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_payable_account_id = fields.Many2one('account.account')
    partner_type = fields.Selection(selection_add=[
        ('employee', 'Employee')
    ], tracking=True, readonly=True, states={'draft': [('readonly', False)]})

    x_partner_type = fields.Selection(selection=[
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Employee', 'Employee'),
    ], compute='get_partner_domain', store=True)

    @api.depends('partner_type')
    def get_partner_domain(self):
        for rec in self:
            if rec.partner_type == 'employee':
                rec.x_partner_type = 'Employee'
            if rec.partner_type == 'supplier':
                rec.x_partner_type = 'Vendor'
            if rec.partner_type == 'customer':
                rec.x_partner_type = 'Customer'

    def action_post(self, sequence_code=False):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name or rec.name == 'New':
                # Use the right sequence to set the name
                if rec.partner_type == 'employee':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.employee.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.employee.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label))\
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids')\
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                    .reconcile()

        return True

    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        for rec in self:
            if rec.x_payable_account_id:
                rec.destination_account_id = rec.x_payable_account_id.id
                rec.x_payable_account_id = False

    def action_draft(self):
        for rec in self:
            if rec.payment_type in ('inbound', 'outbound') and rec.partner_id.x_partner_type == 'Employee':
                rec.x_payable_account_id = rec.move_line_ids.filtered(
                    lambda l: l.account_id.user_type_id.type in ('receivable', 'payable')).account_id.id
        super(AccountPayment, self).action_draft()














