from odoo import models, fields, api, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_operation_id = fields.Many2one(
        comodel_name='mrp.routing.workcenter', string='Operation To Consume', required=False, copy=False,
    )

    def action_assign(self):
        res = super(Picking, self).action_assign()
        for picking in self:
            if picking.x_operation_id:
                picking.move_lines.filtered(
                    lambda ml: picking.x_operation_id.id not in ml.move_dest_ids.mapped('bom_line_id.operation_id').ids
                )._do_unreserve()
        return res
