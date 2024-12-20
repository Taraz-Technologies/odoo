# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InvestmentReturn(models.Model):
    _name = "res.investment.return"
    _description = "Investment Return"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True, )
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True)
    x_investment_ids = fields.Many2many(comodel_name='res.investment', string='Investments')
    x_investment_required = fields.Float(string="Investment required", compute="_compute_investment_values", store=True, )
    x_investment_raised = fields.Float(string="Investment raised", compute="_compute_investment_values", store=True, )
    x_bill_id = fields.Many2one(comodel_name='account.move', string='Bill', required=False)

    @api.depends(
        'x_investment_ids',
        'x_investment_ids.x_investment_required',
        'x_investment_ids.x_investment_raised',
    )
    def _compute_investment_values(self):
        for rec in self:
            rec.x_investment_required = sum(rec.x_investment_ids.mapped('x_investment_required'))
            rec.x_investment_raised = sum(rec.x_investment_ids.mapped('x_investment_raised'))