from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError


class LandedCostHistory(models.Model):
    _name = "landed.cost.history"
    _description = "Landed Cost History"
    _rec_name = "x_product_id"

    x_purchase_history_id = fields.Many2one(comodel_name='purchase.history', string='Purchase History')
    x_adjust_line_id = fields.Many2one(comodel_name='stock.valuation.adjustment.lines', string='Adjustment Line')

    x_landed_cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', related='x_adjust_line_id.cost_id')
    x_landed_cost_date = fields.Date(string='Date', related="x_adjust_line_id.cost_id.date")

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_cost_line_id = fields.Many2one('stock.landed.cost.lines', 'Cost Line', related='x_adjust_line_id.cost_line_id')
    x_split_method = fields.Selection(string="Split Method", related='x_adjust_line_id.x_split_method')
    x_product_qty = fields.Float(string='Received', related='x_adjust_line_id.quantity')
    x_currency_id = fields.Many2one('res.currency', 'Currency', related="x_adjust_line_id.cost_id.currency_id")
    x_former_cost = fields.Float(string="Original Value", related='x_adjust_line_id.former_cost')
    x_final_cost = fields.Float(string="New Value", related='x_adjust_line_id.final_cost')
    x_landed_cost = fields.Float("Additional Cost", related='x_adjust_line_id.additional_landed_cost', digits=(12, 4))


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    x_landed_cost_history_id = fields.Many2one(comodel_name='landed.cost.history', string='Landed Cost History',
                                               compute="update_landed_cost_history", store=True)

    @api.depends('cost_id.state', 'cost_id.date', 'cost_id.cost_lines', 'cost_id.picking_ids', 'cost_id.vendor_bill_id',
                 'final_cost', 'additional_landed_cost', 'move_id')
    def update_landed_cost_history(self):
        for rec in self:
            if rec.cost_id.state == 'cancel' and rec.x_landed_cost_history_id:
                rec.x_landed_cost_history_id.unlink()
            elif rec.cost_id.state != 'cancel' and rec.additional_landed_cost != 0 and rec.move_id.purchase_line_id:
                rec.move_id.update_receipt_history()
                vals = {
                    'x_adjust_line_id': rec._origin.id,
                    'x_product_id': rec.product_id.product_tmpl_id.id,
                }
                if rec.x_landed_cost_history_id:
                    rec.x_landed_cost_history_id.update(vals)
                else:
                    rec.x_landed_cost_history_id = self.env['landed.cost.history'].create(vals)
                if rec.move_id.purchase_line_id.x_purchase_history_id:
                    purchase_history_id = rec.move_id.purchase_line_id.x_purchase_history_id
                    purchase_history_id.x_landed_cost_history_ids = [(4, rec.x_landed_cost_history_id.id)]


