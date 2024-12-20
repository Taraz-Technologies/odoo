from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_bulk_stock_months = fields.Float(string='Bulk Stock Months', config_parameter='stock.x_bulk_stock_months',)
    x_cost_overhead = fields.Float(string='Cost Overhead', config_parameter='stock.x_cost_overhead',)
    # x_preferred_partner_ids = fields.Many2many(
    #     comodel_name='res.partner',
    #     string='Preferred Suppliers',
    #     config_parameter='stock.x_preferred_partner_ids',)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('stock.x_bulk_stock_months', self.x_bulk_stock_months)
        self.env['ir.config_parameter'].set_param('stock.x_cost_overhead', self.x_cost_overhead)
        # self.env['ir.config_parameter'].set_param('stock.x_preferred_partner_ids', self.x_preferred_partner_ids)

