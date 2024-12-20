from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProductionChild(models.Model):
    _name = 'mrp.production.child'
    _description = 'Child MOs'

    manufacturing_id = fields.Many2one(comodel_name='mrp.production', string='Manufacturing Order', required=False)
    child_manufacturing_id = fields.Many2one(comodel_name='mrp.production', string='Child Order', required=False)
    company_id = fields.Many2one(related='child_manufacturing_id.company_id', store=True, readonly=False)
    picking_type_id = fields.Many2one(
        related='child_manufacturing_id.picking_type_id',
        domain=[('code', '=', 'mrp_operation')],
        store=True, readonly=False,
    )
    product_id = fields.Many2one(related='child_manufacturing_id.product_id')
    product_qty = fields.Float(related='child_manufacturing_id.product_qty', string='Quantity')
    product_uom_id = fields.Many2one(related='child_manufacturing_id.product_uom_id', string="UoM")
    bom_id = fields.Many2one(related='child_manufacturing_id.bom_id', store=True, readonly=False, string="BoM")
    state = fields.Selection(related="child_manufacturing_id.state")
    to_consume_qty = fields.Float(string='To Consume', compute="_compute_to_consume_qty")

    @api.depends(
        'manufacturing_id',
        'manufacturing_id.move_raw_ids',
        'manufacturing_id.move_raw_ids.product_id',
        'manufacturing_id.move_raw_ids.product_uom_qty',
    )
    def _compute_to_consume_qty(self):
        for rec in self:
            rec.to_consume_qty = sum(rec.manufacturing_id.move_raw_ids.filtered(
                lambda l: l.product_id.id == rec.product_id.id
            ).mapped('product_uom_qty'))

    @api.onchange('picking_type_id')
    def update_manufacturing_operation(self):
        for rec in self:
            if 'done' in rec.child_manufacturing_id.picking_ids.mapped('state'):
                raise UserError(_(
                    'Manufacturing order is done or in progress.\nYou cannot update manufacturing operation.'
                ))
            elif rec.child_manufacturing_id.picking_ids:
                rec.child_manufacturing_id.update({
                    'company_id': rec.picking_type_id.company_id.id,
                })
                rec.child_manufacturing_id.picking_ids.filtered(lambda l: l.state == 'assigned').do_unreserve()
                rec.child_manufacturing_id.picking_ids.update({
                    'picking_type_id': 43 if rec.picking_type_id.id == 45 else 6,
                    'location_id': 1297 if rec.picking_type_id.id == 45 else 8,
                    'location_dest_id': 1302 if rec.picking_type_id.id == 45 else 17,
                })
                rec.child_manufacturing_id.picking_ids.onchange_picking_type()
                rec.child_manufacturing_id.picking_ids.move_ids_without_package.update({
                    'company_id': 2 if rec.picking_type_id.id == 45 else 1,
                    'picking_type_id': 43 if rec.picking_type_id.id == 45 else 6,
                    'location_id': 1297 if rec.picking_type_id.id == 45 else 8,
                    'location_dest_id': 1302 if rec.picking_type_id.id == 45 else 17,
                    'rule_id': 50 if rec.picking_type_id.id == 45 else 45,
                })
                rec.child_manufacturing_id.picking_ids.action_assign()




