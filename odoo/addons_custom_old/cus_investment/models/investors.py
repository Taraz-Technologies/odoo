from odoo import _, api, fields, models


class Investors(models.Model):
    _name = "res.investors"
    _description = "Investment Investor"
    _rec_name = "x_partner_id"
    _order = "x_date desc"

    x_investment_id = fields.Many2one(comodel_name="res.investment", string="Investment", required=False, )
    x_date = fields.Date(string="Date", required=True, )
    x_partner_id = fields.Many2one(comodel_name="res.partner", string="Investor", required=True, )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", related="x_investment_id.x_currency_id", )
    x_investment_value = fields.Monetary(string="Investment Value", required=False, )
    x_invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice", required=True, domain="[('type', '=', 'out_invoice')]")