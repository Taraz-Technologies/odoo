from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_child_ids = fields.One2many(
        comodel_name='mrp.production.child',
        inverse_name='manufacturing_id',
        string='Child Manufacturing Orders',
        required=False)

    def action_compute_child_manufacturing_orders(self):
        super(MrpProduction, self).action_compute_child_manufacturing_orders()
        for rec in self:
            rec.x_child_ids = [(2, line.id) for line in rec.x_child_ids]

            manufacturing_ids = self.env['mrp.source.details'].search([
                ('x_master_order_id', '=', rec.id)
            ]).mapped('x_manufacturing_id').filtered(lambda l: l.state not in ('cancel'))

            rec.x_child_ids = [(0, 0, {'child_manufacturing_id': line.id}) for line in manufacturing_ids]

    def action_merge_manufacturing_orders(self):
        data = super(MrpProduction, self).action_merge_manufacturing_orders()
        child_orders = data[0].mapped('x_child_ids')
        for child_order in child_orders:
            child_order.copy({'manufacturing_id': data[1].id})
        # Update Master MO Child MOs
        master_order_ids = data[1].x_mrp_demand_ids.mapped('x_master_order_id')
        for order in master_order_ids:
            order.x_child_ids = [(2, line.id) for line in order.x_child_ids]

            manufacturing_ids = self.env['mrp.source.details'].search([
                ('x_master_order_id', '=', order.id)
            ]).mapped('x_manufacturing_id').filtered(lambda l: l.state not in ('cancel'))

            order.x_child_ids = [(0, 0, {'child_manufacturing_id': line.id}) for line in manufacturing_ids]
        # Update Child MOs Master MO
        data[1].x_child_ids.mapped('child_manufacturing_id').mapped('x_mrp_demand_ids').filtered(
            lambda m: m.x_master_order_id.id in data[0].ids
        ).update({'x_master_order_id': data[1].id})
        return data[0], data[1]
