from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductDeliveryStatus(models.Model):
    _inherit = 'product.delivery.status'

    @api.depends(
        'x_move_id.product_uom_qty',
        'x_move_id.reserved_availability',
        'x_mrp_demand_id',
        'x_mrp_demand_id.x_reserved',
        'x_mrp_demand_id.x_demand',
        'x_manufacturing_id',
        'x_manufacturing_id.state',
        'x_manufacturing_id.x_bom_tool_status',
        'x_manufacturing_id.x_production_status',
        'x_manufacturing_id.x_child_ids',
        'x_manufacturing_id.x_child_ids.child_manufacturing_id',
        'x_manufacturing_id.x_child_ids.child_manufacturing_id.state',
        'x_manufacturing_id.workorder_ids',
        'x_manufacturing_id.workorder_ids.state',
        'x_manufacturing_id.workorder_ids.workcenter_id',
    )
    def _compute_status(self):
        super(ProductDeliveryStatus, self)._compute_status()
        for rec in self:
            if not rec.x_manufacturing_id:
                rec.x_status = False
            elif rec.x_move_id.product_uom_qty == rec.x_move_id.reserved_availability and rec.x_move_id.reserved_availability:
                rec.x_status = 'packing'
            elif rec.x_mrp_demand_id.x_reserved == rec.x_mrp_demand_id.x_demand and rec.x_mrp_demand_id:
                rec.x_status = 'packing'
            elif rec.x_manufacturing_id.x_production_status == 'done' or rec.x_manufacturing_id.state == 'done':
                rec.x_status = 'packing'
            elif rec.x_manufacturing_id.workorder_ids.filtered(lambda w: w.state in ('progress', 'done') and w.workcenter_id.id == 16):
                rec.x_status = 'packing'
            elif (rec.x_manufacturing_id.workorder_ids.filtered(lambda w: w.state == 'progress' and w.workcenter_id.id == 17)
                  or rec.x_manufacturing_id.x_production_status == 'in_quality_control'):
                rec.x_status = 'quality'
                rec.x_manufacturing_id.x_production_status = 'in_quality_control'
            elif (rec.x_manufacturing_id.state == 'progress'
                  or any(state == 'progress' for state in rec.x_manufacturing_id.x_child_ids.mapped('child_manufacturing_id').mapped('state'))
                  or any(state == 'in_production' for state in rec.x_manufacturing_id.x_child_ids.mapped('child_manufacturing_id').mapped('x_production_status'))
                  or rec.x_manufacturing_id.x_production_status == 'in_production'):
                rec.x_status = 'production'
                rec.x_manufacturing_id.x_production_status = 'in_production'
            elif (rec.x_manufacturing_id.x_bom_tool_status != 'defined' and rec.x_manufacturing_id.state == 'draft'
                    or rec.x_manufacturing_id.x_production_status in ('bom_tool_not_defined', 'bom_to_be_review')):
                rec.x_status = 'bom'
            elif rec.x_manufacturing_id or rec.x_manufacturing_id.x_production_status in ('proc_required', 'proc_in_progress'):
                rec.x_status = 'procurement'
            else:
                rec.x_status = False
