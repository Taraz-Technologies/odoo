from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseHistory(models.Model):
    _name = "purchase.history"
    _description = "Purchase History"
    _rec_name = "x_product_id"

    x_order_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')
    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    x_order_date = fields.Date(string='Order Date')

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related="x_product_id.currency_id")
    x_product_qty = fields.Float(string='Purchased', required=False)
    x_received_qty = fields.Float(string='Received', required=False, compute="_compute_received_qty", store=True)
    x_product_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM')
    x_unit_fob = fields.Float(string="Unit Price (FOB)", required=False, digits=(12, 4))
    x_subtotal_fob = fields.Float(string="Subtotal (FOB)", required=False)

    x_unit_cnf = fields.Float(string="Unit Price (CNF)", required=False, digits=(12, 4))
    x_subtotal_cnf = fields.Float(string="Subtotal (CNF)", required=False)
    x_unit_lc = fields.Float(string="Unit Price (LC)", compute="_compute_cost", store=True, digits=(12, 4))
    x_subtotal_lc = fields.Float(string="Subtotal (LC)", compute="_compute_cost", store=True)
    x_unit_price = fields.Float(string="Unit Price", compute="_compute_cost", store=True, digits=(12, 4))
    x_subtotal = fields.Float(string="Subtotal", compute="_compute_cost", store=True)

    x_lc_percentage = fields.Float(string='Landed Cost (%)', compute="_compute_lc_percentage", store=True)
    x_lc_factor = fields.Float(string='Landed Cost Factor', compute="_compute_lc_percentage", store=True)

    x_receipt_history_ids = fields.One2many(comodel_name='receipt.history', inverse_name='x_purchase_history_id',
                                            string='Receipt History', required=False, readonly=True)
    x_landed_cost_history_ids = fields.One2many('landed.cost.history', inverse_name='x_purchase_history_id',
                                                string='Landed Cost History', required=False, readonly=True)

    x_tzp_type = fields.Selection(selection=[
        ('alternates', 'Alternates'),
        ('compromised', 'Compromised'),
    ], string='TZP Type')

    @api.depends('x_subtotal_fob', 'x_landed_cost_history_ids', 'x_landed_cost_history_ids.x_landed_cost')
    def _compute_cost(self):
        for rec in self:
            rec.x_subtotal_lc = sum(rec.x_landed_cost_history_ids.mapped('x_landed_cost'))
            rec.x_unit_lc = rec.x_subtotal_lc / rec.x_received_qty if rec.x_received_qty != 0 else 0
            rec.x_subtotal = rec.x_subtotal_cnf + rec.x_subtotal_lc if rec.x_received_qty != 0 else 0
            rec.x_unit_price = rec.x_subtotal / rec.x_received_qty if rec.x_received_qty != 0 else 0

    @api.depends('x_receipt_history_ids', 'x_product_uom_id')
    def _compute_received_qty(self):
        for rec in self:
            received_qty = 0
            for receipt_history in rec.x_receipt_history_ids:
                received_qty += receipt_history.x_product_uom_id._compute_quantity(
                    receipt_history.x_received_qty, rec.x_product_uom_id, round=False
                )
            rec.x_received_qty = received_qty

    @api.depends('x_subtotal', 'x_subtotal_lc', 'x_subtotal_fob')
    def _compute_lc_percentage(self):
        for rec in self:
            rec.x_lc_percentage = rec.x_subtotal_lc / rec.x_subtotal if rec.x_subtotal != 0 else 0
            rec.x_lc_factor = rec.x_subtotal / rec.x_subtotal_fob if rec.x_subtotal_fob != 0 else 0

    def unlink(self):
        self.x_receipt_history_ids.unlink()
        self.x_landed_cost_history_ids.unlink()
        return super(PurchaseHistory, self).unlink()


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_shipping_charges = fields.Float(string='Shipping Charges', compute="_compute_weight", store=True)
    x_shipment_weight = fields.Float(string='Shipment Weight (kg)', compute="_compute_weight", store=True)

    @api.depends('order_line', 'order_line.price_subtotal')
    def _compute_weight(self):
        for rec in self:
            rec.x_shipment_weight = sum(line.product_id.weight * line.product_qty for line in rec.order_line)
            rec.x_shipping_charges = sum(
                rec.order_line.filtered(
                    lambda o: o.product_id
                ).filtered(
                    lambda o: 'Freight' in o.product_id.name
                ).mapped('price_subtotal')
            )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_purchase_history_id = fields.Many2one(comodel_name='purchase.history', string='Purchase History',
                                            compute="update_purchase_history", store=True)

    @api.depends(
        'order_id.state', 'order_id.date_approve', 'order_id.date_order', 'order_id.partner_ref',
        'product_id', 'product_qty', 'product_uom', 'price_unit', 'price_subtotal'
    )
    def update_purchase_history(self):
        for rec in self:
            _logger.info('update_purchase_history')
            if rec.order_id.state == 'cancel' and rec.x_purchase_history_id:
                rec.x_purchase_history_id.unlink()
            elif rec.order_id.state in ('purchase', 'done') and rec.product_id.type not in ('service', False):
                order_date = rec.order_id.date_order.date() if rec.order_id.date_order else False
                order_date = rec.order_id.date_approve.date() if rec.order_id.date_approve else order_date
                shipping_charges = rec.order_id.x_shipping_charges
                shipment_weight = rec.order_id.x_shipment_weight
                product_weight = rec.product_id.weight * rec.product_qty
                shipping_charges = shipping_charges * product_weight / shipment_weight if shipment_weight != 0 else 0
                shipping_charges = rec.currency_id._convert(
                    shipping_charges, rec.product_id.currency_id, self.env.company, order_date
                )
                unit_shipping_charges = shipping_charges / rec.product_qty if rec.product_qty != 0 else 0
                price_unit = rec.price_unit
                price_unit = rec.currency_id._convert(
                    price_unit, rec.product_id.currency_id, self.env.company, order_date
                )
                price_subtotal = rec.price_subtotal
                price_subtotal = rec.currency_id._convert(
                    price_subtotal, rec.product_id.currency_id, self.env.company, order_date
                )
                vals = {
                    'x_product_id': rec.product_id.product_tmpl_id.id,
                    'x_partner_id': rec.order_id.partner_id.id,
                    'x_order_date': order_date,
                    'x_order_id': rec.order_id._origin.id,
                    'x_product_qty': rec.product_qty,
                    'x_product_uom_id': rec.product_uom.id,
                    'x_unit_fob': price_unit,
                    'x_subtotal_fob': price_subtotal,
                    'x_unit_cnf': price_unit + unit_shipping_charges,
                    'x_subtotal_cnf': price_subtotal + shipping_charges,
                }
                if rec.x_purchase_history_id:
                    rec.x_purchase_history_id.update(vals)
                else:
                    rec.x_purchase_history_id = self.env['purchase.history'].create(vals)
                history_id = rec.product_id.product_tmpl_id.x_purchase_history_ids.filtered(
                    lambda l: l.id == max(rec.product_id.product_tmpl_id.x_purchase_history_ids.ids))
                rec.product_id.product_tmpl_id.x_order_id = history_id.x_order_id.id

    def unlink(self):
        self.x_purchase_history_id.unlink()
        return super(PurchaseOrderLine, self).unlink()
