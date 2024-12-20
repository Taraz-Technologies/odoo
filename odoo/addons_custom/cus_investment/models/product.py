# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

# from odoo import api, fields, models
#
#
# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#
#     x_investor_product = fields.Boolean(string="Investor Product?", )
#     x_investment_id = fields.Many2one(comodel_name="res.investment", string="Investment", required=False, )
#
#     @api.onchange('x_investor_product')
#     def update_investment(self):
#         for rec in self:
#             if not rec.x_investor_product:
#                 rec.x_investment_id = False
#
#     @api.onchange('x_investment_id')
#     def update_investment_product(self):
#         for rec in self:
#             investment_product_id = self.env['investment.product'].search([('x_product_id.product_tmpl_id.id', '=', rec._origin.id)], limit=1)
#             if rec.x_investment_id and investment_product_id:
#                 investment_product_id.x_investment_id = rec.x_investment_id.id
#             elif not rec.x_investment_id and investment_product_id:
#                 investment_product_id.unlink()
#             elif rec.x_investment_id and not investment_product_id:
#                 product_id = self.env['product.product'].search([('product_tmpl_id.id', '=', rec._origin.id)], limit=1)
#                 rec.x_investment_id.x_product_ids = [(0, 0, {
#                     'x_product_id': product_id.id,
#                     'x_investment_id': rec.x_investment_id.id,
#                 })]
#
#
# class ProductProduct(models.Model):
#     _inherit = "product.product"
#
#     @api.onchange('x_investor_product')
#     def update_investment(self):
#         for rec in self:
#             if not rec.x_investor_product:
#                 rec.x_investment_id = False
#
#     @api.onchange('x_investment_id')
#     def update_investment_product(self):
#         for rec in self:
#             investment_product_id = self.env['investment.product'].search([('x_product_id.id', '=', rec._origin.id)], limit=1)
#             if rec.x_investment_id and investment_product_id:
#                 investment_product_id.x_investment_id = rec.x_investment_id.id
#             elif not rec.x_investment_id and investment_product_id:
#                 investment_product_id.unlink()
#             elif rec.x_investment_id and not investment_product_id:
#                 rec.x_investment_id.x_product_ids = [(0, 0, {
#                     'x_product_id': rec._origin.id,
#                     'x_investment_id': rec.x_investment_id.id,
#                 })]


