from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', required=False)
    x_consolidation_ref = fields.Char(related="x_consolidation_id.x_consolidation_ref")
    x_shipping_invoice_name = fields.Char(related="x_consolidation_id.x_shipping_invoice_name")
    x_shipping_invoice = fields.Binary(related="x_consolidation_id.x_shipping_invoice")

    x_free_zone_operation_id = fields.Many2one(
        comodel_name='free.zone.operations', string='Free Zone Operation', required=False
    )
    x_operation_type = fields.Selection(selection=[
        ('free', 'FZ Operation'), ('otb', 'OTB Operation'),
    ], string='Operation (FZ/OTB)', help="Free Zone or OTB Operation")

    @api.onchange('x_operation_type')
    def update_order_line_product_category(self):
        for rec in self:
            for line in rec.order_line:
                if rec.x_operation_type == 'free':
                    line.x_product_categ_id = line.product_id.categ_id.id
                else:
                    line.x_product_categ_id = line.product_id.categ_id.x_otb_category_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_form_field_03 = fields.Selection(related="product_id.categ_id.x_form_field_03", readonly=False, store=True)

    @api.onchange('product_id')
    def update_product_category(self):
        for rec in self:
            if rec.order_id.x_operation_type == 'free':
                rec.x_product_categ_id = rec.product_id.categ_id.id
            else:
                rec.x_product_categ_id = rec.product_id.categ_id.x_otb_category_id.id

    @api.onchange('product_id', 'x_product_categ_id', 'x_form_field_03')
    def update_product_category_company(self):
        for rec in self:
            if rec.order_id.company_id.id == 2:
                rec.product_id.categ_id.x_company_id = rec.order_id.company_id.id
