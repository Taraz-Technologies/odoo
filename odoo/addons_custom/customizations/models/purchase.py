from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_folder_name = fields.Char(string='Folder Name', compute="_compute_folder_name", store=True)
    x_purchase_type = fields.Selection(selection=[
        ('Local', 'Local'),
        ('Clearing', 'Clearing'),
        ('Forwarding', 'Forwarding'),
        ('Imported Goods', 'Imported Goods'),
        ('Shipping (Export)', 'Shipping (Export)'),
        ('Shipping (Self Pickup)', 'Shipping (Self Pickup)'),
    ], required=False, string="Purchase Type", )
    x_item_type = fields.Selection(selection=[
        ('Asset', 'Asset'),
        ('Expense', 'Expense'),
        ('Inventory', 'Inventory'),
        ('Landed Cost', 'Landed Cost'),
        ('Inventory & Asset', 'Inventory & Asset'),
        ('Cost of Freight Sold', 'Cost of Freight Sold'),
    ], string="Item Type", required=False, )
    x_weight_kg = fields.Float(string="Weight (kg)", required=False, )
    x_weight_type = fields.Selection(selection=[
        ('a', 'A: Customer Actual Weight'),
        ('v', 'V: Customer Volumetric Weight'),
        ('b', 'B: DHL Actual Weight'),
        ('w', 'W: DHL Volumetric Weight'),
        ('m', 'M: Mixed'),
    ], string="Weight Type", required=False, )
    x_purchase_order_status = fields.Selection(selection=[
        ('Valid', 'Valid'),
        ('Invalid', 'Invalid'),
    ], string="Purchase Order Status", required=False, default='Valid', )
    x_attachment = fields.Binary(string="Attachment")
    x_import_method = fields.Selection(selection=[
        ('WeBoc', 'WeBoc'),
        ('Speedy', 'Speedy'),
    ], string="Import Method", required=False, )
    x_show_forwarder_ref = fields.Boolean(string='Show forwarder ref', default=False, compute="_show_forwarder_ref", store=True)
    x_forwarder_ref = fields.Char(string='Forwarder Reference', required=False)
    x_payment_method = fields.Many2one(comodel_name="account.journal", string="Payment Method", required=True)
    x_related_po_s = fields.Many2many(comodel_name="purchase.order", relation="purchase_order_rel_1",
                                      column1="id1", column2="id2", string="Related PO(s)", )
    x_related_so_s = fields.Many2many(comodel_name="sale.order", relation="sale_order_rel_1",
                                      column1="purchase_order_id", column2="sale_order_id", string="Related Exp SO(s)", )
    x_weboc_gd = fields.Char(string="WeBoc GD#", required=False, )
    x_assessed_value = fields.Char(string="Assessed Value (Rs.)", required=False, )
    x_comments = fields.Char(string="Comments", required=False, )
    x_old_bill = fields.Boolean(string="Old Bill?", )
    x_exclude_from_dashboard = fields.Selection(string="Exclude From DSHBD?", selection=[('Yes', 'Yes'), ('No', 'No'), ], required=False, )
    x_date_dashboard = fields.Date(string='Dashboard Date', required=False)
    x_port_of_shipment = fields.Char(string="Port of Shipment", required=False, )
    x_port_of_discharge = fields.Char(string="Port of Discharge", required=False, )
    x_letter_head_report = fields.Boolean(string="Letter Head Report?", )
    x_lc_pos_count = fields.Integer(string='LC PO Count', required=False)
    # -------------------------------------- Product Kanban View --------------------------------------
    x_product_ids = fields.Many2many(comodel_name='product.product', string='Products')
    x_compute_products = fields.Boolean(string='Products', compute="_compute_products", store=True)
    x_logistics_route = fields.Boolean(string='Logistic Route', required=False)
    x_picking_type_ids = fields.Many2many(comodel_name='stock.picking.type', relation="stock_picking_type_purchase_order_rel_1",
                                          column1="purchase_order_id", column2="stock_picking_type_id",
                                          string='Deliver To', compute="_compute_picking_ids", compute_sudo=False)

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            if rec.date_approve:
                rec.x_date_dashboard = rec.date_approve.date()
        return res

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_shipped(self):
        super(PurchaseOrder, self)._compute_is_shipped()
        for order in self:
            order.is_shipped = False if any(
                x.product_qty != x.qty_received and x.product_id.type in ('product', 'consu') for x in order.order_line
            ) else True

    @api.depends('name', 'partner_id', 'partner_ref', 'company_id')
    def _compute_folder_name(self):
        for rec in self:
            rec.x_folder_name = '%s%s%s%s%s' % (
                rec.name,
                ' - TarazPK' if rec.company_id.id == 1 else ' - TarazTR',
                ' - %s' % rec.partner_id.parent_id.name if rec.partner_id.parent_id else ' - %s' % rec.partner_id.name,
                ' - %s' % rec.partner_id.parent_id.country_id.name if rec.partner_id.parent_id else ' - %s' % rec.partner_id.country_id.name,
                ' - %s' % rec.partner_ref if rec.partner_ref else '',
            )

    @api.depends('x_picking_type_ids')
    def _show_forwarder_ref(self):
        for rec in self:
            show_forwarder_ref = False
            if 'forwarder' in rec.x_picking_type_ids.mapped('x_type'):
                show_forwarder_ref = True
            rec.x_show_forwarder_ref = show_forwarder_ref

    def _compute_picking_ids(self):
        for rec in self:
            picking_type_ids = False
            if rec.x_item_type in ['Asset', 'Inventory', 'Inventory & Asset']:
                picking_ids = self.env['stock.picking'].search([('origin', '=', rec.name)])
                if picking_ids:
                    picking_type_ids = picking_ids.mapped('picking_type_id').ids
            rec.x_picking_type_ids = picking_type_ids

    def action_open_add_discount_wizard(self):
        view_id = self.env.ref('customizations.purchase_order_discount_view_form').id
        name = _('Add Discount')

        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order.discount',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_x_order_id': self.id,
            }
        }

    def action_open_add_shipping_wizard(self):
        view_id = self.env.ref('customizations.purchase_order_shipping_view_form').id
        name = _('Update shipping cost')

        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order.shipping',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_x_order_id': self.id,
            }
        }

    def action_open_remove_shipping_wizard(self):
        self.order_line.search([
            ('order_id', '=', self.id), ('x_is_shipping', '=', True), ('qty_invoiced', '=', 0)
        ]).unlink()

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        for rec in self:
            if rec.x_item_type == 'Cost of Freight Sold':
                rec.x_related_so_s.freight_calculation()
        return res

    @api.depends('order_line', 'state')
    def _compute_products(self):
        for rec in self:
            rec.x_product_ids = [(6, 0, rec.order_line.mapped('product_id').ids)]
            rec.x_compute_products = True

    # def action_view_landed_costs(self):
    #     action = self.env.ref('stock_landed_costs.action_stock_landed_cost').read()[0]
    #     action['context'] = {
    #         'default_picking_ids': self.picking_ids.ids,
    #     }
    #     action['domain'] = [('picking_ids', 'ilike', self.picking_ids.ids)]
    #     return action
    #
    # def action_view_purchase_orders(self):
    #     action = self.env.ref('customizations.act_landed_cost_purchase_orders').read()[0]
    #     action['domain'] = [('id', 'in', self.x_related_po_s.ids)]
    #     return action

    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        for record in self:
            result['context'].update({
                'default_ref': record.partner_ref,
                'default_x_operation_type': record.x_operation_type,
                'default_x_related_po_s': record.x_related_po_s.ids,
                'default_x_related_so_s': record.x_related_so_s.ids,
                'default_invoice_incoterm_id': record.incoterm_id.id,
                'default_invoice_payment_term_id': record.payment_term_id.id,
                'default_x_payment_method': record.x_payment_method.id,
                'default_x_purchase_type': record.x_purchase_type,
                'default_x_item_type': record.x_item_type,
                'default_x_import_method': record.x_import_method,
                'default_x_weboc_gd': record.x_weboc_gd,
                'default_x_assessed_value': record.x_assessed_value,
                'default_x_comments': record.x_comments,
            })
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_product_categ_id = fields.Many2one(comodel_name="product.category", string="Product Category")
    x_is_shipping = fields.Boolean(string='Is a shipping', default=False)
    x_discount = fields.Float(string='Dics.%', required=False)

    @api.onchange('product_id')
    def update_product_category(self):
        for rec in self:
            rec.x_product_categ_id = rec.product_id.categ_id.id

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'x_discount')
    def _compute_amount(self):
        super(PurchaseOrderLine, self)._compute_amount()
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        super(PurchaseOrderLine, self)._prepare_compute_all_values()
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit - (self.price_unit * self.x_discount / 100),
            'currency_id': self.order_id.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res['discount'] = self.x_discount
        return res

    def unlink(self):
        for line in self:
            if line.order_id.state in ['purchase', 'done'] and not line.x_is_shipping:
                raise UserError(_('Cannot delete a purchase order line which is in state \'%s\'.') % (line.state,))
        return super(PurchaseOrderLine, self).unlink()
