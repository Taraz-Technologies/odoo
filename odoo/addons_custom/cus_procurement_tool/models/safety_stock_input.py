from odoo import models, fields, api, _


class SafetyStockInput(models.Model):
    _name = 'safety.stock.input'
    _description = 'Safety Stock Input'

    x_procurement_cycle_id = fields.Many2one(
        comodel_name='procurement.cycle',
        string='Procurement Cycle',
        required=False)

    x_taraz_part_id = fields.Many2one(
        comodel_name='taraz.part.number',
        string='Taraz Part #',
        required=False)

    x_consider_compromised = fields.Boolean(
        related='x_taraz_part_id.x_consider_compromised',
        store=True)

    x_description = fields.Text(
        related='x_taraz_part_id.x_description')

    x_product_purchase_packaging_id = fields.Many2one(
        related='x_taraz_part_id.x_product_purchase_packaging_id',
        store=True)
    x_virtual_available = fields.Float(
        related='x_taraz_part_id.x_virtual_available',
        store=True)
    x_backorder_qty = fields.Float(
        related='x_taraz_part_id.x_backorder_qty',
        store=True)
    x_qty_available = fields.Float(
        related='x_taraz_part_id.x_qty_available',
        store=True)
    x_quantity_buffer = fields.Float(
        related='x_taraz_part_id.x_quantity_buffer',
        store=True)
    x_safety_stock = fields.Float(
        related='x_taraz_part_id.x_safety_stock',
        store=True)
    x_reorder_point = fields.Float(
        related='x_taraz_part_id.x_reorder_point',
        store=True)
    x_order_quantity = fields.Float(
        related='x_taraz_part_id.x_order_quantity',
        store=True,
        readonly=False)
    x_roq = fields.Float(
        related='x_taraz_part_id.x_roq',
        store=True)

    x_uom_id = fields.Many2one(
        related='x_taraz_part_id.x_uom_id',
        store=True)

    x_alternate_ids = fields.One2many(
        related='x_taraz_part_id.x_alternate_ids')
    x_compromised_ids = fields.One2many(
        related='x_taraz_part_id.x_compromised_ids')
    x_tag_ids = fields.Many2many(
        related='x_taraz_part_id.x_tag_ids')

    x_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=False)

    x_product_description = fields.Text(
        related='x_product_id.description',
        store=True)

    x_quantity = fields.Float(
        string='Quantity',
        required=False)

    x_unit_price = fields.Float(
        compute='_compute_unit_price_last_purchase',
        string='Unit Price',
        store=True,
        readonly=False)

    x_subtotal = fields.Float(
        compute='_compute_subtotal',
        string='Ext. Price',
        store=True)
    
    x_product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Part Usage',
        readonly=True)
    
    @api.depends('x_product_id')
    def _compute_unit_price_last_purchase(self):
        for rec in self:
            if rec.x_product_id.x_purchase_history_ids:
                purchase_history_ids = rec.x_product_id.x_purchase_history_ids
                purchase_history_id = purchase_history_ids[len(purchase_history_ids) - 1]
                rec.x_unit_price = purchase_history_id.x_unit_fob
            else:
                rec.x_unit_price = 0.0

    @api.depends('x_quantity', 'x_unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.x_subtotal = rec.x_unit_price * rec.x_quantity


