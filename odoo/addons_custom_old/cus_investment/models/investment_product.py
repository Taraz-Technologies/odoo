from odoo import api, fields, models


class InvestmentProducts(models.Model):
    _name = "investment.product"
    _description = "Investment Products"
    _rec_name = "x_product_id"
    _order = "x_product_id"

    x_investment_id = fields.Many2one(comodel_name="res.investment", string="Investment", required=False, )
    x_product_id = fields.Many2one(
        comodel_name="product.product", string="Product", required=True,
        domain="[('categ_id', 'ilike', 'Finished Goods')]",
    )
    x_quantity = fields.Float(string="Quantity",  required=False, )
    x_unit_cost = fields.Float(string="Unit Cost",  required=False, )
    x_adjustment = fields.Float(string="Unit Adjustment",  required=False, )
    x_note = fields.Char(string="Comments", required=False, )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, related="x_investment_id.x_currency_id", )
    x_subtotal = fields.Float(string="Subtotal",  required=False, compute="_compute_subtotal", store=True, )

    # @api.model
    # def create(self, values):
    #     res = super(InvestmentProducts, self).create(values)
    #     product_id = self.env['product.product'].search([('id', '=', values.get('x_product_id'))], limit=1)
    #     if product_id:
    #         product_id.x_investor_product = True
    #         product_id.x_investment_id = values.get('x_investment_id')
    #     return res
    #
    # def unlink(self):
    #     for rec in self:
    #         rec.x_product_id.x_investor_product = False
    #         rec.x_product_id.x_investment_id = False
    #     return super(InvestmentProducts, self).unlink()

    @api.depends('x_quantity', 'x_unit_cost', 'x_adjustment')
    def _compute_subtotal(self):
        for rec in self:
            rec.x_subtotal = rec.x_quantity * (rec.x_unit_cost + rec.x_adjustment)