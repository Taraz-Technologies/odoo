
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AdjustmentWizard(models.TransientModel):
    _name = 'adjustment.wizard'
    _description = 'Add Adjustment'

    x_round01_id = fields.Integer(string="Round Product", required=False, default=0, )
    x_unit_cost = fields.Float(string="Unit Cost",  required=False, )
    x_adjustment = fields.Float(string="Unit Adjustment",  required=False, compute="compute_adjustment", )
    x_total_unit = fields.Float(string="Total Unit",  required=False, compute="compute_adjustment", )
    x_note = fields.Char(string="Adjustment Note", required=False, )

    x_addition01_ids = fields.Many2many('adjustment.addition', 'adjustment_addition_adjustment_wizard_rel', string='Addition')
    x_subtraction01_ids = fields.Many2many('adjustment.subtraction', 'adjustment_subtraction_adjustment_wizard_rel', string='Subtraction')

    @api.depends('x_unit_cost','x_addition01_ids','x_subtraction01_ids')
    def compute_adjustment(self):
        for rec in self:
            rec.x_adjustment = 0
            for line in rec.x_addition01_ids:
                rec.x_adjustment += line.x_subtotal
            for line in rec.x_subtraction01_ids:
                rec.x_adjustment -= line.x_subtotal
            rec.x_total_unit = rec.x_unit_cost + rec.x_adjustment

    def update_data(self):
        for rec in self:
            round_id = False
            if rec.x_round01_id != 0:
                round_id = self.env['round1.product.lines'].search([('id','=',rec.x_round01_id)])
            round_id.update_from_wizard(rec.x_unit_cost,
                                        rec.x_adjustment,
                                        rec.x_total_unit,
                                        rec.x_note,
                                        rec.x_addition01_ids,
                                        rec.x_subtraction01_ids,)


    def save_and_close(self):
        self.compute_adjustment()
        self.update_data()
        return {'type': 'ir.actions.act_window_close'}

















