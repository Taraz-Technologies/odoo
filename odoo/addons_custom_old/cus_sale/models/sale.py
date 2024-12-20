from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

import datetime
import pytz
import logging

_logger = logging.getLogger("*__addons_custom__*")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_region = fields.Many2one(related="x_country.x_region", store=True)
    x_subregion = fields.Many2one(related="x_country.x_subregion", store=True)
    x_bill_count = fields.Integer(compute='_compute_bill_count', store=True)
    x_repair_ids = fields.One2many('repair.order', 'x_sale_order_id')
    x_repair_count = fields.Integer(compute="compute_repair_count")

    x_show_hs_code = fields.Boolean(string='Show HS Code', required=False)
    x_show_coo = fields.Boolean(string='Show COO', required=False)
    x_custom_tag_ids = fields.Many2many('custom.tags', string="Tags", tracking=True)

    @api.depends('x_repair_ids')
    def compute_repair_count(self):
        for rec in self:
            rec.x_repair_count = len(rec.x_repair_ids)

    @api.depends('picking_ids.x_bill_count')
    def _compute_bill_count(self):
        for rec in self:
            rec.x_bill_count = sum(rec.picking_ids.mapped('x_bill_count'))

    # def action_confirm(self):
    #     for rec in self:
    #         rec.partner_id.commercial_partner_id.create_related_accounts()
    #     return super(SaleOrder, self).action_confirm()

    def write(self, vals):
        old_values = self.x_custom_tag_ids.ids
        res = super(SaleOrder, self).write(vals)
        new_values = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_values, new_values=new_values
            )
        for record in self:
            if record.state == 'sale':
                record.order_line.filtered(
                    lambda l: l.product_uom_qty != l.qty_delivered and l.product_id.type in ('product', 'consu')
                )._action_launch_stock_rule()
        return res

    # def write(self, values):
    #     res = super(SaleOrder, self).write(values)
    #     for rec in self:
    #         if rec.state == 'sale':
    #             rec.order_line.filtered(
    #                 lambda l: l.product_uom_qty != l.qty_delivered and l.product_id.type in ('product', 'consu')
    #             )._action_launch_stock_rule()
    #     return res

    def action_create_related_bill(self):
        for rec in self:
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': rec.picking_ids.ids,
                'default_x_sale_ids': [(6, 0, [rec.id])],
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                'default_invoice_date': datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
            }
            return dict(action, view_mode='form', views=[(False, 'form')])

    def action_view_related_bills(self):
        for rec in self:
            action = self.env.ref('cus_logistics_tracking.view_picking_related_bills_action').read()[0]
            action['context'] = {
                'default_type': 'in_invoice',
                'default_x_picking_ids': rec.picking_ids.ids,
                'default_x_sale_ids': [(6, 0, [rec.id])],
                'default_journal_id': 1 if rec.company_id.id == 1 else 97,
                'default_invoice_date': datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
            }
            action['domain'] = [('x_picking_ids', 'ilike', rec.picking_ids.ids)]
            return action

    def action_view_repairs(self):
        action = self.env.ref('repair.action_repair_order_tree').read()[0]
        action['domain'] = [('x_sale_order_id', '=', self.id)]
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        tag_name = self.env['sale.order'].browse(vals.get('order_id')).name
        tag_id = self.env['account.analytic.tag'].search([('name', '=', tag_name)])
        if not tag_id:
            tag_id = self.env['account.analytic.tag'].create({
                'name': tag_name,
                # 'company_id': vals.get('company_id'),
                # 'color': 1,
            })
        vals['analytic_tag_ids'] = [(4, tag_id.id)]
        return super(SaleOrderLine, self).create(vals)










