from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_demand_list_ids = fields.Many2many(related="purchase_id.x_demand_list_ids")
    x_proc_cycle_id = fields.Many2one(related="purchase_id.x_proc_cycle_id")

