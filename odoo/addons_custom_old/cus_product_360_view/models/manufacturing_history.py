import datetime

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ManufacturingHistory(models.Model):
    _name = "manufacturing.history"
    _description = "Manufacturing History"
    _rec_name = "x_product_id"

    x_type = fields.Selection([('consumption', 'Consumption'), ('manufacturing', 'Manufacturing')],  'Type')
    x_order_id = fields.Many2one(comodel_name='mrp.production', string='Manufacturing Order')
    x_date = fields.Date(string='Date', required=False)

    x_component_id = fields.Many2one(comodel_name='product.template', string='Component')
    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_master_product_id = fields.Many2one(comodel_name='product.template', string='Master Product')

    x_product_uom_qty = fields.Float(string='To Consume', required=False)
    x_reserved_availability = fields.Float(string='Reserved', required=False)
    x_quantity_done = fields.Float(string='Consumed', required=False)
    x_product_uom = fields.Many2one(comodel_name='uom.uom', string='UoM')
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=2)
    x_unit_cost = fields.Float(string="Unit Cost", digits=(12, 4))
    x_cost = fields.Monetary(string="Cost")

    x_tzp_type = fields.Selection(selection=[
        ('alternates', 'Alternates'), ('compromised', 'Compromised'), ], string='TZP Type')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_update_history = fields.Boolean(string='Update History', compute="_compute_history")

    @api.depends('state')
    def _compute_history(self):
        for rec in self:
            _logger.info('_compute_history')
            manufacturing_history = self.env['manufacturing.history']
            if rec.state == 'cancel':
                manufacturing_history.search([('x_order_id', '=', rec.id)]).unlink()
                return
            elif rec.state != 'done':
                return

            product_id = rec.product_id.product_tmpl_id
            history_ids = manufacturing_history.search([
                ('x_product_id', '=', product_id.id), ('x_order_id', '=', rec.id)
            ])

            subtotal_cost = sum(
                rec.move_finished_ids.filtered(
                    lambda f: f.state == 'done'
                ).mapped('stock_valuation_layer_ids').mapped('value')
            )

            vals = {
                'x_type': 'manufacturing',
                'x_order_id': rec.id,
                'x_date': rec.date_finished.date() if rec.date_finished else False,
                'x_product_uom_qty': rec.product_qty,
                'x_product_uom': rec.product_uom_id.id,
                'x_unit_cost': subtotal_cost / rec.product_qty if rec.product_qty != 0 else 0,
                'x_cost': subtotal_cost,
            }

            if not history_ids:
                vals['x_product_id'] = product_id.id
                manufacturing_history.create(vals)
            else:
                history_ids.update(vals)

            for move in rec.move_raw_ids:
                product_id = move.product_id.product_tmpl_id
                history_ids = manufacturing_history.search([
                    ('x_component_id', '=', product_id.id), ('x_order_id', '=', rec.id)
                ])
                cost = -sum(move.stock_valuation_layer_ids.mapped('value'))

                vals = {
                    'x_type': 'consumption',
                    'x_order_id': rec.id,
                    'x_date': rec.date_finished.date() if rec.date_finished else False,
                    'x_master_product_id': rec.product_id.product_tmpl_id.id,
                    'x_product_uom_qty': move.product_uom_qty,
                    'x_reserved_availability': move.reserved_availability,
                    'x_quantity_done': move.quantity_done,
                    'x_product_uom': move.product_uom.id,
                    'x_unit_cost': cost / move.quantity_done if move.quantity_done != 0 else 0,
                    'x_cost': cost,
                }

                if not history_ids:
                    vals['x_component_id'] = product_id.id
                    manufacturing_history.create(vals)
                else:
                    history_ids.update(vals)
            rec.x_update_history = True
