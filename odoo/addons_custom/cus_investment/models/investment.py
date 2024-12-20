from odoo import api, fields, models


class Investment(models.Model):
    _name = "res.investment"
    _description = "Investment"
    _rec_name = "x_name"

    x_name = fields.Char(string="Project", required=True, )
    x_date = fields.Date(string="Date", required=True, )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=True, )
    x_investment_required = fields.Float(string="Investment required",  required=False, compute="_compute_investment_required", store=True, )
    x_investment_raised = fields.Float(string="Investment raised",  required=False, compute="_compute_investment_raised", store=True, )

    x_product_ids = fields.One2many(comodel_name="investment.product", inverse_name="x_investment_id", string="Products", required=False, )
    x_investor_ids = fields.One2many(comodel_name="res.investors", inverse_name="x_investment_id", string="Investments", required=False, )

    @api.depends('x_product_ids', 'x_product_ids.x_subtotal')
    def _compute_investment_required(self):
        for rec in self:
            rec.x_investment_required = sum(rec.x_product_ids.mapped('x_subtotal'))

    @api.depends('x_investor_ids', 'x_investor_ids.x_investment_value')
    def _compute_investment_raised(self):
        for rec in self:
            rec.x_investment_raised = sum(rec.x_investor_ids.mapped('x_investment_value'))
