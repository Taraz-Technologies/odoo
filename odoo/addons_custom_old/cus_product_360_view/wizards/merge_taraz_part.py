from odoo import api, fields, models
from odoo.exceptions import UserError


class MergeTarazPartsWizard(models.TransientModel):
    _name = "merge.taraz.parts.wizard"
    _description = "Merge Taraz Part"

    x_taraz_part_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part # (Parent)', required=False)
    x_taraz_part_ids = fields.Many2many(comodel_name='taraz.part.number', string='Taraz Part # (Children)')

    @api.model
    def default_get(self, fields_list):
        res = super(MergeTarazPartsWizard, self).default_get(fields_list)
        res.update({'x_taraz_part_id': self.env.context.get('active_id')})
        return res

    def merge_taraz_parts(self):
        for rec in self:
            rec.x_taraz_part_id.x_enable_safety_stock = any(
                taraz_part.x_enable_safety_stock for taraz_part in rec.x_taraz_part_ids)
            rec.x_taraz_part_ids.mapped('x_alternate_ids').mapped('x_product_id').update({
                'x_taraz_part_number_id': rec.x_taraz_part_id.id,
            })
            rec.x_taraz_part_ids.mapped('x_compromised_ids').mapped('x_product_usage_ids').unlink()
            rec.x_taraz_part_ids.mapped('x_compromised_ids').update({
                'x_taraz_part_number_id': rec.x_taraz_part_id.id,
            })
            rec.x_taraz_part_ids.filtered(lambda x: x.id != rec.x_taraz_part_id.id).unlink()
            if rec.x_taraz_part_id.x_enable_safety_stock:
                rec.x_taraz_part_id.compute_safety_stock()
