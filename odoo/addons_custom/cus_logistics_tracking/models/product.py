from odoo import api, fields, models

import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductCategory(models.Model):
    _inherit = "product.category"

    x_otb_category_id = fields.Many2one(comodel_name='product.category', string='OTB Category', required=False)


class Product(models.Model):
    _inherit = "product.product"


class ProductTemplate(models.Model):
    _inherit = "product.template"
