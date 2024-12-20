import datetime

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    x_prc_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='PRC Cycle')
    x_prc_line_id = fields.Many2one(comodel_name='component.list', string='PRC Line')
    x_prc_cart_id = fields.Many2one(comodel_name='procurement.cycle.cart.details', string='Cart#')
    x_prc_product_id = fields.Many2one(comodel_name='product.product', string='Cart Product')
    x_prc_purchase_id = fields.Many2one(comodel_name='purchase.order', string='PRC Purchase')
    x_prc_picking_ids = fields.Many2many(comodel_name='stock.picking', string='PRC Receipts')
    x_prc_picking_date = fields.Datetime(string='Expected Date')
    x_prc_picking_days = fields.Char(string='Expected Days')

    x_available = fields.Boolean(string='Available')
    x_alternate_available = fields.Boolean(string='Alt. Available')

    def get_prc_details(self):
        for rec in self:
            prc_cycle_id = False
            prc_line_id = False
            prc_cart_id = False
            prc_product_id = False
            prc_purchase_id = False
            prc_picking_ids = False
            prc_picking_date = False
            prc_picking_days = False

            if rec.x_demand_batch_id:
                cycle_id = self.env['procurement.cycle'].search([
                    ('x_demand_batch_ids', 'ilike', rec.x_demand_batch_id.id)
                ], limit=1)
                if cycle_id:
                    prc_cycle_id = cycle_id.id
                    line_id = cycle_id.x_short_component_ids.filtered(
                        lambda x: x.x_product_id.id == rec.product_id.id
                    )
                    if line_id:
                        prc_line_id = line_id[0].id
                        cart_line_id = line_id[0].mapped('x_quantities_ids').filtered(lambda x: x.x_prc_cart_id)
                        if cart_line_id:
                            prc_product_id = cart_line_id[0].x_product_id.id
                            prc_cart_id = cart_line_id[0].x_prc_cart_id.id
                            prc_purchase_id = cart_line_id[0].x_prc_cart_id.x_purchase_id.id
                            picking_ids = self.env['stock.move'].search([
                                ('picking_id', 'in', cart_line_id[0].x_prc_cart_id.x_purchase_id.picking_ids.ids),
                                ('product_id', '=', cart_line_id[0].x_product_id.id)
                            ]).mapped('picking_id')
                            prc_picking_ids = picking_ids.ids
                            if picking_ids.filtered(lambda p: p.x_expected_date).mapped('x_expected_date'):
                                prc_picking_date = max(
                                    picking_ids.filtered(lambda p: p.x_expected_date).mapped('x_expected_date')
                                )
                                prc_picking_days = '%s days' % (
                                    prc_picking_date - datetime.datetime.now()
                                ).days

            rec.update({
                'x_prc_cycle_id': prc_cycle_id,
                'x_prc_line_id': prc_line_id,
                'x_prc_cart_id': prc_cart_id,
                'x_prc_product_id': prc_product_id,
                'x_prc_purchase_id': prc_purchase_id,
                'x_prc_picking_ids': prc_picking_ids,
                'x_prc_picking_date': prc_picking_date,
                'x_prc_picking_days': prc_picking_days,
            })

            available = rec.x_prc_product_id.free_qty or rec.product_id.free_qty
            required = rec.product_uom_qty - rec.reserved_availability
            rec.x_available = True if available >= required else False

            available = rec.product_id.x_taraz_part_number_id.x_alternate_ids.mapped('x_product_id').mapped(
                'product_variant_id'
            ).filtered(
                lambda x: x.free_qty > rec.product_uom_qty - rec.reserved_availability and x.id != rec.product_id.id
            )
            rec.x_alternate_available = True if available else False
