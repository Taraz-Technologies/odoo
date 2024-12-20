from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductVariantAttributeLines(models.Model):
    _name = 'product.variant.attribute.lines'
    _description = 'Product Variant'
    _rec_name = "x_attribute_id"
    _order = 'sequence'

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    sequence = fields.Integer(string='Sequence', required=False)
    x_attribute_id = fields.Many2one(comodel_name='product.variant.attribute', string='Attribute', required=True)
    x_attribute_tag_ids = fields.Many2many(comodel_name='product.variant.tags', string='Values', required=True)


class ProductVariantAttribute(models.Model):
    _name = 'product.variant.attribute'
    _description = 'Product Variant'
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=True)


class ProductVariantTags(models.Model):
    _name = "product.variant.tags"
    _description = "Product Variant Tags"
    _rec_name = "display_name"

    x_name = fields.Char(string='Name')
    x_description = fields.Char(string='Description')
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends('x_name', 'x_description')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s [%s]' % (rec.x_name, rec.x_description)


def update_product_data(bom_tool_id, product_id):
    if product_id:
        product_id.update({
            'x_bom_tool_id': bom_tool_id.id,
            'image_1920': product_id.image_1920 or bom_tool_id.x_base_product_id.image_1920,
            'categ_id': product_id.categ_id.id or bom_tool_id.x_product_categ_id.id,
            'barcode': product_id.barcode or product_id.name,
            'x_product_group': bom_tool_id.x_product_group.id,
            'x_product_series': bom_tool_id.x_product_series.id,
            'x_product_division': bom_tool_id.x_product_division.id,
            'dk_hs_code': bom_tool_id.dk_hs_code.id,
            'x_hs_code_tr_id': bom_tool_id.x_hs_code_tr_id.id,
            'x_country_id': bom_tool_id.x_country_id.id,
        })


class ProductVariantLines(models.Model):
    _name = "product.variant.lines"
    _description = "Product Variant"
    _rec_name = "x_name"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)

    x_description = fields.Text(string="Description", readonly=False)
    x_short_description = fields.Char(string='Short Description', readonly=False)
    x_description_pickingout = fields.Text(string="Delivery Description", readonly=False)
    x_description_sale = fields.Text(string="Sales Description", readonly=False)

    x_name = fields.Char(string='Variant Name', required=False)

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product', compute='get_product', store=True)
    x_currency_id = fields.Many2one(related="x_product_id.currency_id", readonly=False, store=True)
    x_list_price = fields.Float(related="x_product_id.list_price", readonly=False, store=True)
    x_weight = fields.Float(related="x_product_id.weight", readonly=False, store=True)
    x_categ_id = fields.Many2one(related="x_product_id.categ_id", readonly=False, store=True)

    x_var_short_description = fields.Char(related="x_product_id.x_short_description", readonly=False, store=True)
    x_var_description = fields.Text(related="x_product_id.description", readonly=False, store=True)
    x_var_description_pickingout = fields.Text(related="x_product_id.description_pickingout", readonly=False, store=True)
    x_var_description_sale = fields.Text(related="x_product_id.description_sale", readonly=False, store=True)

    @api.depends('x_name')
    def get_product(self):
        for rec in self:
            if rec.x_product_id:
                rec.x_product_id.name = rec.x_name
            else:
                product_id = self.env['product.template'].search([('name', '=', rec.x_name)], limit=1)
                if product_id:
                    rec.x_product_id = product_id.id

            if rec.x_product_id not in rec.x_bom_tool_id.x_variant_ids.mapped('x_product_id') and rec.x_product_id:
                variant_id = self.env['product.variant'].create({
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'x_product_id': rec.x_product_id.id,
                })
                variant_id.generate_variant_base_bom()

            update_product_data(rec.x_bom_tool_id, rec.x_product_id)

    def create_product(self):
        for rec in self:
            if rec.x_product_id:
                rec.x_product_id.name = rec.x_name
            else:
                product_id = self.env['product.template'].search([('name', '=', rec.x_name)], limit=1)
                if product_id:
                    rec.x_product_id = product_id.id
                else:
                    rec.x_product_id = self.env['product.template'].create({
                        'name': rec.x_name,
                        'type': 'product',
                        'route_ids': [5],
                        'categ_id': rec.x_bom_tool_id.x_product_categ_id.id if rec.x_bom_tool_id.x_product_categ_id else 275,
                    }).id

            # Create Product BoM if No BoM exist
            bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', rec.x_product_id.id)])
            if not bom_id:
                self.env['mrp.bom'].create({'product_tmpl_id': rec.x_product_id.id,
                                            'product_qty': 1, 'code': rec.x_bom_tool_id.x_name})

            if rec.x_product_id not in rec.x_bom_tool_id.x_variant_ids.mapped('x_product_id') and rec.x_product_id:
                variant_id = self.env['product.variant'].create({
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'x_product_id': rec.x_product_id.id,
                })
                variant_id.generate_variant_base_bom()

            update_product_data(rec.x_bom_tool_id, rec.x_product_id)

    def unlink(self):
        for rec in self:
            rec.x_product_id.x_bom_tool_id = False
            rec.x_bom_tool_id.x_variant_ids.filtered(lambda l: not l.x_product_id).unlink()
        return super(ProductVariantLines, self).unlink()


class ProductVariant(models.Model):
    _name = "product.variant"
    _description = "Product Variant"
    _rec_name = "x_product_id"

    x_selected = fields.Boolean(string='Selected Variant', required=False)
    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_product_id = fields.Many2one(comodel_name='product.template', string='Product', required=False)
    x_bom_id = fields.Many2one(comodel_name='base.bom', string='Input BoM', required=False)
    x_status = fields.Selection(selection=[
        ('defined', 'Defined'), ('undefined', 'Undefined'),
    ], string='Status', default='undefined', )

    def generate_variant_base_bom(self):
        for rec in self:
            if not rec.x_bom_tool_id.x_base_bom_id:
                raise UserError('Base BoM is not defined.')

            if rec.x_bom_id:
                rec.x_bom_id.x_name = "BOM-TZV"
                rec.x_bom_id.x_product_id = rec.x_product_id.id
                rec.get_bom_lines()
                continue

            vals = {
                'x_name': "BOM-TZV",
                'x_product_id': rec.x_product_id.id,
                'x_bom_tool_id': rec.x_bom_tool_id.id,
            }

            line_ids = []
            bom_line_ids = rec.x_bom_tool_id.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_variant)
            for bom_line in bom_line_ids:
                line_ids.append((0, 0, {
                    'x_name': bom_line.x_name,
                    'x_part_description': bom_line.x_part_description,
                    'x_ref_des': bom_line.x_ref_des,
                    'x_old_product_id': bom_line.x_old_product_id.id,
                    'x_taraz_part_id': bom_line.x_taraz_part_id.id,
                    'x_product_id': bom_line.x_product_id.id,
                    'x_quantity': bom_line.x_quantity,
                    'x_uom_id': bom_line.x_uom_id.id,
                    'x_line_block_id': bom_line.x_line_block_id.id,
                    'x_dnp': bom_line.x_dnp,
                    'x_critical': bom_line.x_critical,
                    'x_variant': bom_line.x_variant,
                    'x_notes': bom_line.x_notes,
                }))

            line_ids.append((0, 0, {
                'x_name': 'Base Product',
                'x_part_description': 'Base Product',
                'x_ref_des': 'TZB01',
                'x_old_product_id': False,
                'x_taraz_part_id': rec.x_bom_tool_id.x_base_product_id.x_taraz_part_number_id.id,
                'x_product_id': rec.x_bom_tool_id.x_base_product_id.id,
                'x_quantity': 1,
                'x_uom_id': rec.x_bom_tool_id.x_base_product_id.uom_id.id,
                'x_line_block_id': False,
                'x_dnp': False,
                'x_critical': False,
                'x_variant': 'variant',
                'x_notes': 'Base Product',
            }))
            vals['x_bom_line_ids'] = line_ids

            bom_id = self.env['base.bom'].create(vals)
            rec.x_bom_id = bom_id.id

    def get_bom_lines(self):
        for rec in self:
            rec.x_bom_tool_id.x_bom_ids = rec.x_bom_tool_id.x_variant_ids.mapped('x_bom_id').ids
            rec.x_bom_tool_id.x_variant_ids.filtered(lambda l: l.x_selected).x_selected = False
            rec.x_selected = True
            rec.x_bom_tool_id.x_variant_bom_id = rec.x_bom_id.id
            rec.x_bom_tool_id.x_variant_id = rec.x_product_id.id
            rec.x_bom_tool_id.x_variant_bom_line_ids = [(6, 0, rec.x_bom_id.x_bom_line_ids.ids)]
            rec.x_bom_tool_id.filter_variant_bom_lines()

    def unlink(self):
        for rec in self:
            rec.x_bom_id.unlink()
        return super(ProductVariant, self).unlink()


