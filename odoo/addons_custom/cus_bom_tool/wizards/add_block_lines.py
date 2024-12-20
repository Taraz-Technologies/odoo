from odoo import api, fields, models
from odoo.exceptions import UserError


class BlockAdditionWizard(models.TransientModel):
    _name = "block.addition.wizard"
    _description = "Block Addition"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)

    x_attached_block_ids = fields.Many2many(comodel_name='bom.tool.blocks', string=' Add Blocks')

    @api.model
    def default_get(self, fields_list):
        res = super(BlockAdditionWizard, self).default_get(fields_list)
        res.update({
            'x_bom_tool_id': self.env.context.get('active_id'),
            'x_attached_block_ids': self.env['bom.tool'].browse(self.env.context.get('active_id')).x_attached_block_ids.ids,
        })
        return res

    def add_blocks_data(self):
        for rec in self:
            for line in rec.x_bom_tool_id.x_attached_block_ids:
                if line.id not in rec.x_attached_block_ids.ids:
                    line.unlink()
            for line in rec.x_attached_block_ids:
                line.x_bom_tool_id = rec.x_bom_tool_id.id
            rec.x_bom_tool_id.add_blocks_data()





