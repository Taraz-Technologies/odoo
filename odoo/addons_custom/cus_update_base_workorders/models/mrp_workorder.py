from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        for workorder in self:
            child_workorder_ids = workorder.production_id.mapped('x_child_ids').mapped(
                'child_manufacturing_id').filtered(
                lambda x: x.x_bom_tool_id.id == workorder.production_id.x_bom_tool_id.id
            ).mapped('workorder_ids').filtered(
                lambda x: x.workcenter_id.id == workorder.workcenter_id.id and not x.is_user_working
            )
            for child_workorder_id in child_workorder_ids:
                child_workorder_id.qty_producing = workorder.qty_producing
                child_workorder_id.button_start()
        return super(MrpWorkorder, self).button_start()

    def record_production(self):
        for workorder in self:
            child_workorder_ids = workorder.production_id.mapped('x_child_ids').mapped(
                'child_manufacturing_id').filtered(
                lambda x: x.x_bom_tool_id.id == workorder.production_id.x_bom_tool_id.id
            ).mapped('workorder_ids').filtered(
                lambda x: x.workcenter_id.id == workorder.workcenter_id.id and x.is_user_working
            )
            for child_workorder_id in child_workorder_ids:
                child_workorder_id.record_production()
                child_workorder_id.button_pending()
        return super(MrpWorkorder, self).record_production()

    def button_pending(self):
        for workorder in self:
            child_workorder_ids = workorder.production_id.mapped('x_child_ids').mapped(
                'child_manufacturing_id').filtered(
                lambda x: x.x_bom_tool_id.id == workorder.production_id.x_bom_tool_id.id
            ).mapped('workorder_ids').filtered(
                lambda x: x.workcenter_id.id == workorder.workcenter_id.id and x.is_user_working
            )
            for child_workorder_id in child_workorder_ids:
                child_workorder_id.button_pending()
        return super(MrpWorkorder, self).button_pending()
