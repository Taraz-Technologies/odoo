from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    x_product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related="product_id.currency_id")
    x_cost = fields.Float(string='Cost', compute="_compute_cost", store=True)

    @api.depends('product_id', 'state', 'name')
    def _compute_cost(self):
        for rec in self:
            account_move_line_id = self.env['account.move.line'].search([
                ('name', '=', rec.name + ' - ' + rec.product_id.name), ('account_id', '=', 643)])
            if account_move_line_id:
                rec.x_cost = account_move_line_id.debit
