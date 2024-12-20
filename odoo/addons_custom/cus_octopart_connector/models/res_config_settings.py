from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    client_id = fields.Char(string="CLIENT ID")
    client_secret = fields.Char(string="CLIENT SECRET")

    def set_values(self):
        """Octopart API setting field values"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('cus_octopart_connector.client_id', self.client_id)
        self.env['ir.config_parameter'].set_param('cus_octopart_connector.client_secret', self.client_secret)
        return res

    def get_values(self):
        """Octopart API getting field values"""
        res = super(ResConfigSettings, self).get_values()
        client_id = self.env['ir.config_parameter'].sudo().get_param('cus_octopart_connector.client_id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('cus_octopart_connector.client_secret')
        res.update(
           client_id=client_id,
           client_secret=client_secret,
        )
        return res





