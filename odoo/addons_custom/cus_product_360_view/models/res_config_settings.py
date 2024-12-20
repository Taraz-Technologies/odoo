from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_authorization_code = fields.Char(string='Authorization Code',
                                       config_parameter='stock.x_inclusive_of_other_costs',)
    x_access_token = fields.Char(string='Access Token',
                                 config_parameter='stock.x_inclusive_of_other_costs',)
    x_refresh_token = fields.Char(string='Refresh Token',
                                  config_parameter='stock.x_inclusive_of_other_costs',)

    x_target_rate = fields.Float(string='Target Rate', config_parameter='stock.x_target_rate',)
    x_average_lead_time = fields.Float(string='Average Lead Time', config_parameter='stock.x_average_lead_time',)
    x_calculated_with = fields.Selection(
        string='Calculate With',
        selection=[('consumption_months', 'Consumption Months'),
                   ('twelve_months', 'Last 12 Months'),
                   ('all_months', 'All Months'),],
        config_parameter='stock.x_calculated_with',
        default='consumption_months',)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('stock.x_authorization_code', self.x_authorization_code)
        self.env['ir.config_parameter'].set_param('stock.x_access_token', self.x_access_token)
        self.env['ir.config_parameter'].set_param('stock.x_refresh_token', self.x_refresh_token)
        self.env['ir.config_parameter'].set_param('stock.x_target_rate', self.x_target_rate)
        self.env['ir.config_parameter'].set_param('stock.x_average_lead_time', self.x_average_lead_time)
        self.env['ir.config_parameter'].set_param('stock.x_calculated_with', self.x_calculated_with)

