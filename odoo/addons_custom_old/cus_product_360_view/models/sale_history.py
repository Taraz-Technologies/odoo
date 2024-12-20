from odoo import api, fields, models
# from odoo import _
# from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class SaleHistory(models.Model):
    _name = "sale.history"
    _description = "Sale History"
    _rec_name = "x_product_id"

    x_order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=False)
    x_order_date = fields.Date(string='Date', required=False)
    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', related="x_order_id.partner_id")
    x_partner_invoice_id = fields.Many2one(comodel_name='res.partner', string='Invoice Address',
                                           related="x_order_id.partner_invoice_id")
    x_partner_shipping_id = fields.Many2one(comodel_name='res.partner', string='Delivery Address',
                                            related="x_order_id.partner_shipping_id")
    x_end_user_id = fields.Many2one(comodel_name='res.partner', string='Customer', related="x_order_id.x_end_user")

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product',
                                   compute="_compute_product", store=True)

    x_product_quotation_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_product_sale_order_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_internal_notes = fields.Text(string="Internal Notes")
    x_product_uom_qty = fields.Float(string='Quantity', digits=(12, 4))
    x_qty_delivered = fields.Float(string='Delivered', digits=(12, 4))
    x_qty_invoiced = fields.Float(string='Invoiced', digits=(12, 4))
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related="x_product_id.currency_id")
    x_product_uom = fields.Many2one(comodel_name='uom.uom', string='UoM')
    x_price_unit = fields.Float(string='Unit Price', digits=(12, 4))
    x_discount = fields.Float(string='Disc.%', required=False)
    x_price_subtotal = fields.Float(string='Subtotal')
    x_unit_cost = fields.Float(string="Unit Cost", digits=(12, 4))
    x_cost = fields.Monetary(string="Cost")

    @api.depends('x_product_quotation_id', 'x_product_sale_order_id')
    def _compute_product(self):
        for rec in self:
            if rec.x_product_quotation_id:
                rec.x_product_id = rec.x_product_quotation_id.id
            if rec.x_product_sale_order_id:
                rec.x_product_id = rec.x_product_sale_order_id.id


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    x_update_history = fields.Boolean(string='Update History', compute="_compute_history", store=True)

    @api.depends(
        'order_line', 'date_order', 'state', 'x_cgs_line_ids', 'partner_id', 'partner_invoice_id',
        'partner_shipping_id', 'x_end_user'
    )
    def _compute_history(self):
        for rec in self:
            for line in rec.order_line:
                product_id = line.product_id.product_tmpl_id

                sale_history = self.env['sale.history']
                history_ids = sale_history.search([
                    '&',
                    ('x_order_id', '=', rec.id),
                    '|',
                    ('x_product_quotation_id', '=', product_id.id),
                    ('x_product_sale_order_id', '=', product_id.id),
                ])

                if history_ids and rec.state == 'cancel':
                    history_ids.unlink()

                price_unit = line.price_unit
                price_subtotal = line.price_subtotal
                if rec.date_order and rec.currency_id.id != line.product_id.currency_id.id:
                    price_unit = rec.currency_id._convert(
                        price_unit, line.product_id.currency_id, rec.company_id, rec.date_order.date()
                    )
                    price_subtotal = rec.currency_id._convert(
                        price_subtotal, line.product_id.currency_id, rec.company_id, rec.date_order.date()
                    )

                unit_cost = 0
                cost = 0
                cost_id = rec.x_cgs_line_ids.search([
                    ('x_product_id', '=', line.product_id.id), ('x_type', '=', 'cost'),
                    ('x_sale_order_id', '=', rec.id), ('x_product_type', '=', 'products')
                ], limit=1)
                if cost_id:
                    unit_cost = cost_id.x_price_unit
                    cost = cost_id.x_price_subtotal
                    if rec.date_order and cost_id.x_currency_id.id != line.product_id.currency_id.id:
                        unit_cost = cost_id.x_currency_id._convert(
                            unit_cost, line.product_id.currency_id, rec.company_id, rec.date_order.date()
                        )
                        cost = cost_id.x_currency_id._convert(
                            cost, line.product_id.currency_id, rec.company_id, rec.date_order.date()
                        )

                vals = {
                    'x_order_date': rec.date_order.date() if rec.date_order else False,
                    'x_product_uom_qty': line.product_uom_qty,
                    'x_qty_delivered': line.qty_delivered,
                    'x_qty_invoiced': line.qty_invoiced,
                    'x_product_uom': line.product_uom.id,
                    'x_price_unit': price_unit,
                    'x_discount': line.discount,
                    'x_price_subtotal': price_subtotal,
                    'x_unit_cost': unit_cost,
                    'x_cost': cost,
                }

                if not history_ids and rec.state in ['draft', 'sent']:
                    vals['x_order_id'] = rec.id
                    product_id.x_quotation_history_ids = [(0, 0, vals)]
                elif not history_ids and rec.state in ['sale', 'done']:
                    vals['x_order_id'] = rec.id
                    product_id.x_sale_order_history_ids = [(0, 0, vals)]
                elif history_ids and rec.state != 'cancel':
                    vals['x_product_quotation_id'] = product_id.id if rec.state in ['draft', 'sent'] else False
                    vals['x_product_sale_order_id'] = product_id.id if rec.state in ['sale', 'done'] else False
                    history_ids.update(vals)


