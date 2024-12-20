from odoo import api, fields, models
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from datetime import datetime

import requests
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProductCategory(models.Model):
    _inherit = "product.category"

    x_goods_type = fields.Selection(selection=[
        ('fg', 'FG'), ('sfg', 'SFG'), ('rm', 'RM'),
    ], string='Goods Type', required=False, tracking=True)

    x_investment_markup = fields.Float(string='Investor Markup (%)', required=False, tracking=True)
    x_bonus_percentage = fields.Float(string='Production Bonus (%)', required=False, tracking=True)

    x_form_field_03 = fields.Selection(
        selection=[
            ("Ticari-Mal", "Ticari-Mal"),
            ("Ticari Olmayan-Demirbaş", "Ticari Olmayan-Demirbaş"),
            ("Ticari Olmayan-Sarf Malzemesi", "Ticari Olmayan-Sarf Malzemesi"),
            ("Ticari Olmayan-Yatırım ve Tesis", "Ticari Olmayan-Yatırım ve Tesis"),
            ("Ticari Olmayan-Hizmet Alımı", "Ticari Olmayan-Hizmet Alımı"), ],
        string='İŞLEM KONUSU',
        tracking=True)

    x_company_id = fields.Many2one(comodel_name='res.company',string='Company', required=False)


class Product(models.Model):
    _inherit = "product.product"

    x_accessory_ids = fields.One2many(
        comodel_name='product.accessory', inverse_name='x_product_id',
        string='Product Accessories', required=False,
    )

    x_product_id = fields.Many2one(
        comodel_name="product.product", string="Product (Autofill Accessories)", domain="[('type', '=', 'product')]"
    )

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = super(Product, self).get_product_multiline_description_sale()
        if self.description:
            name = self.description
        return name

    def autofill_accessory_ids(self):
        for rec in self:
            rec.x_accessory_ids = [(2, accessory.id) for accessory in rec.x_accessory_ids]
            for accessory_id in rec.x_product_id.x_accessory_ids:
                accessory_id.copy({'x_product_id': rec.id})

    def name_get(self):
        return [(rec.id, rec.name) for rec in self]

    @api.onchange('name')
    def onchange_name_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,x_name_translation',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_name_translation,
                    value=rec.name,
                )

    @api.onchange('x_name_translation')
    def onchange_name_translation_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,name',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.name,
                    value=rec.x_name_translation,
                )

    @api.onchange('description')
    def onchange_description_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,x_description_translation',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_description_translation,
                    value=rec.description,
                )

    @api.onchange('x_description_translation')
    def onchange_description_translation_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,description',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.description,
                    value=rec.x_description_translation,
                )

    @api.onchange('x_short_description')
    def onchange_short_description_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,x_short_description_translation',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_short_description_translation,
                    value=rec.x_short_description,
                )

    @api.onchange('x_short_description_translation')
    def onchange_short_description_translation_field(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.update_translation(
                    name='product.template,x_short_description',
                    res_id=rec.product_tmpl_id._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_short_description,
                    value=rec.x_short_description_translation,
                )

    def update_translation(self, name, res_id, lang, src, value):
        # Fetch the record
        record = self.env['product.template'].browse(res_id)

        # Fetch the existing translation
        translation = self.env['ir.translation'].search([
            ('name', '=', name),
            ('lang', '=', lang),
            ('type', '=', 'model'),
            ('res_id', '=', record.id),
        ], limit=1)

        if translation:
            # Update existing translation
            translation.value = value
        else:
            # Create new translation if it doesn't exist
            self.env['ir.translation'].create({
                'name': name,
                'lang': lang,
                'type': 'model',
                'res_id': record.id,
                'src': src,  # Source value in the default language
                'value': value
            })

    @api.onchange('x_other_name_tag_ids')
    def update_product_other_names(self):
        for rec in self:
            duplicate_record_id = self.env['product.duplicate.names'].search([('x_product_id', '=', rec._origin.id)])
            if not duplicate_record_id:
                duplicate_record_id = self.env['product.duplicate.names'].create({'x_product_id': rec._origin.id})
            duplicate_record_id.x_other_name_tag_ids = rec.x_other_name_tag_ids.ids if rec.x_other_name_tag_ids else False

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = [
                '|', '|', '|',  '|', '|',
                ('name', operator, name),
                ('x_name_translation', operator, name),
                ('default_code', operator, name),
                ('x_other_name_tag_ids.x_name', operator, name),
                ('description', operator, name),
                ('x_description_translation', operator, name),
            ]
            product_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))

    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        # if 'x_custom_tag_ids' in vals:
        #     self.x_custom_tag_ids._track_many2many_changes(
        #         res, 'x_custom_tag_ids', new_values=vals['x_custom_tag_ids']
        #     )
        for rec in res:
            rec_id = '00000%s' % rec.product_tmpl_id.id
            rec_id = rec_id[-6:]
            default_code = 'P%s' % rec_id
            rec.update({'default_code': default_code})
        return res

    def write(self, vals):
        old_values = self.x_custom_tag_ids.ids
        res = super(Product, self).write(vals)
        new_values = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_values, new_values=new_values
            )
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_other_name_tag_ids = fields.Many2many(comodel_name='product.other.name.tags', string='Other Names',
                                            relation='product_other_name_tags_product_template_rel_1',
                                            column1='product_other_name_tags_id', column2='product_template_id')

    x_hide_in_report = fields.Boolean(string='Exclude', required=False)

    x_usage_count = fields.Integer(string='Usage Count', compute="_compute_usage_count", compute_sudo=False)

    x_taraz_part_number_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part#',
                                             compute="compute_taraz_part_number", store=True, copy=False)
    x_alternate_ids = fields.Many2many(comodel_name='taraz.part.alternates', string='Alternates Parts',
                                       compute="_compute_alt_and_comp", store=True)
    x_compromised_ids = fields.Many2many(comodel_name='taraz.part.compromised', string='Compromised Parts',
                                         compute="_compute_alt_and_comp", store=True)
    x_mounting_type = fields.Selection(selection=[('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER')],
                                       string='Type', tracking=True, track_visibility='always', readonly=False,
                                       related='x_taraz_part_number_id.x_mounting_type', store=True)

    x_tzp_type = fields.Selection(selection=[
        ('alternates', 'Alternates'), ('compromised', 'Compromised'), ], string='TZP Type')

    x_alternates_exist = fields.Boolean(string='Alternate Exist?', compute="_compute_alt_and_comp", store=True)
    x_compromised_exist = fields.Boolean(string='Compromised Exist?', compute="_compute_alt_and_comp", store=True)

    x_unit_weight = fields.Float(string='Weight (Fixed)', digits=(12, 5), compute="_compute_weight", store=True)
    x_gross_weight = fields.Float(string='Weight (Gross)', digits=(12, 5))

    x_purchase_history_ids = fields.One2many(comodel_name='purchase.history', inverse_name='x_product_id',
                                             string="Purchase History", readonly=True)

    x_manufacturing_history_ids = fields.One2many(comodel_name='manufacturing.history', inverse_name='x_product_id',
                                                  string="Manufacturing History", readonly=True)
    x_consumption_history_ids = fields.One2many(comodel_name='manufacturing.history', inverse_name='x_component_id',
                                                string="Consumption History", readonly=True)
    x_scrap_history_ids = fields.One2many(comodel_name='stock.scrap', inverse_name='x_product_tmpl_id',
                                          string="Scrap History", readonly=True)

    x_quotation_history_ids = fields.One2many(comodel_name='sale.history', inverse_name='x_product_quotation_id',
                                              string="Quotation History", readonly=True)
    x_sale_order_history_ids = fields.One2many(comodel_name='sale.history', inverse_name='x_product_sale_order_id',
                                               string="Sale Order History", readonly=True)

    x_quarterly_consumption_ids = fields.One2many(
        comodel_name='quarterly.consumption', inverse_name='x_product_id', string="Quarterly Consumption"
    )

    x_quarterly_consumption = fields.Float(string='Average Quarterly Consumption')

    x_total_purchased = fields.Float(string='Total Purchased', compute="_compute_stat_values", store=True)
    x_total_manufactured = fields.Float(string='Total Manufactured ', compute="_compute_stat_values", store=True)
    x_total_consumed = fields.Float(string='Total Consumed', compute="_compute_stat_values", store=True)
    x_total_sold = fields.Float(string='Total Sold', compute="_compute_stat_values", store=True)

    x_start_date = fields.Date(string='Start Date', required=False)
    x_end_date = fields.Date(string='End Date', required=False)

    x_period_purchased = fields.Float(string='Purchased in Period', compute="_compute_stat_values", store=True)
    x_period_manufactured = fields.Float(string='Manufactured in Period', compute="_compute_stat_values", store=True)
    x_period_consumed = fields.Float(string='Consumed in Period', compute="_compute_stat_values", store=True)
    x_period_sold = fields.Float(string='Sold in Period', compute="_compute_stat_values", store=True)

    x_start_inventory = fields.Float(string='Start Inventory', compute="_compute_stat_values", store=True)
    x_end_inventory = fields.Float(string='End Inventory', compute="_compute_stat_values", store=True)
    x_average_inventory = fields.Float(string='Average Inventory', compute="_compute_stat_values", store=True)
    x_cogs = fields.Float(string='COGS', compute="_compute_stat_values", store=True)

    x_inventory_turnover = fields.Float(string='Inventory Turnover', compute="_compute_stat_values", store=True)

    dk_hs_code = fields.Many2one(comodel_name='hs.code.database', string='HS Code (PK)', tracking=True,
                                 domain="[('x_country_id.name', '=', 'Pakistan')]")
    x_hs_code_tr_id = fields.Many2one(comodel_name='hs.code.database', string='HS Code (TR)', tracking=True,
                                      domain="[('x_country_id.name', '=', 'Turkey')]")

    x_period_days = fields.Float(string='Inventory Days', compute="_compute_stat_values", store=True)

    dk_get_digikey_details = fields.Boolean(string='Digi-Key Details', default=False)

    dk_digiKey_part_number = fields.Char(string='Digi-Key Part Number', tracking=True,
                                         help='This field is linked with Digi-Key API', copy=False)
    dk_manufacturer_part_number = fields.Char(string='Manufacturer Part #', tracking=True,
                                              help='This field is linked with Digi-Key API', copy=False)
    dk_product_description = fields.Char(string=' Product Description', tracking=True,
                                         help='This field is linked with Digi-Key API', copy=False)
    dk_detailed_description = fields.Text(string='Detailed Description', tracking=True,
                                          help='This field is linked with Digi-Key API', copy=False)
    dk_category = fields.Many2one(comodel_name='product.type', string='Type', related="dk_sub_category.x_type_id",
                                  copy=False, readonly=False, store=True)
    dk_sub_category = fields.Many2one(comodel_name='product.sub.type', string='Sub Type', tracking=True,
                                      help='This field is linked with Digi-Key API', copy=False)
    dk_htsus_code = fields.Many2one(comodel_name='hs.codes', string='HTSUS Code', tracking=True,
                                    help='This field is linked with Digi-Key API', copy=False)
    dk_manufacturer = fields.Char(string='Manufacturer', tracking=True,
                                  help='This field is linked with Digi-Key API', copy=False)

    x_manufacturer = fields.Many2one(comodel_name='res.partner', string='Manufacturer',
                                     compute='get_manufacturer', store=True, readonly=False,
                                     help='This field is linked with Digi-Key API',
                                     domain="[('x_manufacturer', '=', True)]", copy=False)

    x_original_htsus = fields.Char(string="Digikey HTSUS", related="dk_htsus_code.x_alternate_htsus")

    x_type_assigning = fields.Selection(selection=[
        ('auto', 'Auto'),
        ('manual', 'Manual'), ], required=False, string='Assigned',)
    x_sub_type_assigning = fields.Selection(selection=[
        ('auto', 'Auto'),
        ('manual', 'Manual'), ], required=False, string='Assigned',)
    x_htsus_assigning = fields.Selection(selection=[
        ('auto', 'Auto'),
        ('manual', 'Manual'), ], required=False, string='Assigned')

    x_type_select = fields.Boolean(string='Select', required=False)
    x_product_purchase_packaging_select = fields.Boolean(string='Select', required=False)
    x_sub_type_select = fields.Boolean(string='Select', required=False)
    x_htsus_select = fields.Boolean(string='Select', required=False)

    x_order_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', copy=False)
    x_country_ids = fields.Many2many(comodel_name='res.country', string='COOs',
                                     compute='update_coos', store=True, copy=False)
    x_total_coos = fields.Integer(string='Total COOs', compute='get_total_coos', store=True, copy=False)
    x_average_price = fields.Float(string='Cost (Average)', digits='Product Price',
                                   compute='compute_average_cost', store=True, copy=False)
    x_production_bonus = fields.Boolean(string='Production Bonus?', required=False, copy=False)

    x_goods_type = fields.Selection(related="categ_id.x_goods_type", required=False, store=True)
    x_investment_markup = fields.Float(related="categ_id.x_investment_markup", required=False, store=True)
    x_bonus_percentage = fields.Float(related="categ_id.x_bonus_percentage", required=False, store=True)

    x_turkish_description = fields.Text(string="Turkish Description", required=False)

    x_form_field_03 = fields.Selection(related="categ_id.x_form_field_03", required=False, store=True)

    x_product_purchase_packaging_id = fields.Many2one(
        comodel_name='product.purchase.packaging',
        string='Product Purchase Packaging',
        required=False)

    x_name_translation = fields.Char(string='Name Translation', index=True, translate=True)
    x_description_translation = fields.Text(string='Description Translation', index=True, translate=True)
    x_short_description_translation = fields.Char(string='Short Description Translation', index=True, translate=True)

    x_accessory_ids = fields.One2many(
        comodel_name='product.accessory',  string="Product Accessories",
        compute="_compute_accessory_ids", inverse="_set_accessory_ids"
    )

    x_product_id = fields.Many2one(
        comodel_name='product.product',  string="Product (Autofill Accessories)", domain="[('type', '=', 'product')]",
        compute="_compute_product_id", inverse="_set_product_id"
    )
    x_custom_tag_ids = fields.Many2many('custom.tags', string="Tags")

    def autofill_accessory_ids(self):
        for rec in self:
            rec.product_variant_ids.autofill_accessory_ids()

    @api.depends('product_variant_ids', 'product_variant_ids.x_product_id')
    def _compute_product_id(self):
        for p in self:
            p.x_product_id = p.product_variant_ids.x_product_id

    def _set_product_id(self):
        for p in self:
            p.product_variant_ids.x_product_id = p.x_product_id

    @api.depends('product_variant_ids', 'product_variant_ids.x_accessory_ids')
    def _compute_accessory_ids(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.x_accessory_ids = p.product_variant_ids.x_accessory_ids
            else:
                p.x_accessory_ids = False

    def _set_accessory_ids(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_ids.x_accessory_ids = p.x_accessory_ids

    @api.onchange('name')
    def onchange_name_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,x_name_translation',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_name_translation,
                    value=rec.name,
                )

    @api.onchange('x_name_translation')
    def onchange_name_translation_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,name',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.name,
                    value=rec.x_name_translation,
                )

    @api.onchange('description')
    def onchange_description_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,x_description_translation',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_description_translation,
                    value=rec.description,
                )

    @api.onchange('x_description_translation')
    def onchange_description_translation_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,description',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.description,
                    value=rec.x_description_translation,
                )

    @api.onchange('x_short_description')
    def onchange_short_description_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,x_short_description_translation',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_short_description_translation,
                    value=rec.x_short_description,
                )

    @api.onchange('x_short_description_translation')
    def onchange_short_description_translation_field(self):
        for rec in self:
            if rec._origin.id != 0 and isinstance(rec._origin.id, int):
                rec.update_translation(
                    name='product.template,x_short_description',
                    res_id=rec._origin.id,
                    lang='en_US' if self.env.user.lang == 'tr_TR' else 'tr_TR',
                    src=rec.x_short_description,
                    value=rec.x_short_description_translation,
                )

    def update_translation(self, name, res_id, lang, src, value):
        # Fetch the record
        record = self.browse(res_id)

        # Fetch the existing translation
        translation = self.env['ir.translation'].search([
            ('name', '=', name),
            ('lang', '=', lang),
            ('type', '=', 'model'),
            ('res_id', '=', record.id),
        ], limit=1)

        if translation:
            # Update existing translation
            translation.value = value
        else:
            # Create new translation if it doesn't exist
            self.env['ir.translation'].create({
                'name': name,
                'lang': lang,
                'type': 'model',
                'res_id': record.id,
                'src': src,  # Source value in the default language
                'value': value
            })

    @api.model
    def create(self, vals):
        vals['x_name_translation'] = vals.get('name')
        vals['description'] = vals.get('description') or vals.get('x_short_description')
        vals['x_description_translation'] = vals.get('description')
        vals['x_short_description'] = vals.get('x_short_description') or vals.get('description')
        vals['x_short_description_translation'] = vals.get('x_short_description')
        res = super(ProductTemplate, self).create(vals)
        # if 'x_custom_tag_ids' in vals:
        #     self.x_custom_tag_ids._track_many2many_changes(
        #         res, 'x_custom_tag_ids', new_values=vals['x_custom_tag_ids']
        #     )
        for rec in res:
            rec_id = '00000%s' % rec.id
            rec_id = rec_id[-6:]
            default_code = 'P%s' % rec_id
            rec.update({'default_code': default_code})
        return res

    def action_view_taraz_part(self):
        action = self.env.ref('cus_product_360_view.action_view_taraz_part_number').read()[0]
        form_view = [(self.env.ref('cus_product_360_view.view_taraz_part_number_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_taraz_part_number_id.id
        return action

    def action_archive(self):
        if len(self.x_taraz_part_number_id.x_alternate_ids) == 1:
            self.x_taraz_part_number_id.unlink()
        else:
            self.x_taraz_part_number_id = False
        return super(ProductTemplate, self).action_archive()

    def unlink(self):
        if len(self.x_taraz_part_number_id.x_alternate_ids) == 1:
            self.x_taraz_part_number_id.unlink()
        else:
            self.x_taraz_part_number_id = False
        return super(ProductTemplate, self).unlink()

    @api.constrains('name')
    def check_duplicate_product_name(self):
        for rec in self:
            product_ids = self.env['product.template'].search([('name', '=', rec.name)])
            if len(product_ids) != 1:
                raise UserError('Error: "%s" product name already exist!' % rec.name)
            product_id = self.env['product.template'].search([('x_other_name_tag_ids.x_name', 'ilike', rec.name)], limit=1)
            if product_id:
                raise UserError('Error: "%s" product name is other name of "%s" product!' % (rec.name, product_id.name))

    @api.depends('dk_manufacturer')
    def get_manufacturer(self):
        for rec in self:
            manufacturer_id = self.env['res.partner'].search([
                ('name', '=', rec.dk_manufacturer)], limit=1) if rec.dk_manufacturer else False
            # if not manufacturer_id:
            #     manufacturer_id = self.env['res.partner'].create({
            #         'company_type': 'company',
            #         'name': rec.dk_manufacturer,
            #         'x_partner_type': 'Vendor',
            #     })
            if manufacturer_id:
                manufacturer_id.x_manufacturer = True if manufacturer_id else False
                rec.x_manufacturer = manufacturer_id.id

    @api.depends('standard_price')
    def compute_average_cost(self):
        for rec in self:
            valuation_ids = self.env['stock.valuation.layer'].search([('product_id.product_tmpl_id', '=', rec.id)])
            quantity = sum(valuation_ids.mapped('quantity'))
            value = sum(valuation_ids.mapped('value'))
            rec.x_average_price = value / quantity if quantity != 0 else 0

    @api.depends('x_country_ids')
    def get_total_coos(self):
        for rec in self:
            rec.x_total_coos = len(rec.x_country_ids)

    @api.depends('x_country_id')
    def update_coos(self):
        for rec in self:
            rec.x_country_ids = [(4, rec.x_country_id.id)] if rec.x_country_id else False

    @api.depends('x_consumption_history_ids', 'x_scrap_history_ids', 'x_sale_order_history_ids')
    def _compute_consumption(self):
        for rec in self:
            if rec.type != 'service':
                _logger.info('_compute_consumption')
                quarters = []
                quarter_dates = []

                dates = rec.x_consumption_history_ids.mapped('x_date')
                for date in dates:
                    quarter = self.env['quarterly.consumption'].compute_quarter(date)[0]
                    if quarter not in quarters:
                        quarter_dates.append(date)
                        quarters.append(quarter)

                dates = rec.x_scrap_history_ids.mapped('date_done')
                for date in dates:
                    if date:
                        quarter = self.env['quarterly.consumption'].compute_quarter(date.date())[0]
                        if quarter not in quarters:
                            quarter_dates.append(date.date())
                            quarters.append(quarter)

                dates = rec.x_sale_order_history_ids.mapped('x_order_date')
                for date in dates:
                    quarter = self.env['quarterly.consumption'].compute_quarter(date)[0]
                    if quarter not in quarters:
                        quarter_dates.append(date)
                        quarters.append(quarter)

                quarterly_consumption_ids = []
                for idx, quarter in enumerate(quarters):
                    consumption_id = self.env['quarterly.consumption'].search([
                        ('x_product_id', '=', rec.id), ('x_quarter', '=', quarter)
                    ])
                    if not consumption_id:
                        quarterly_consumption_ids.append({'x_product_id': rec.id, 'x_date': quarter_dates[idx]})
                    else:
                        consumption_id.x_date = quarter_dates[idx]
                self.env['quarterly.consumption'].create(quarterly_consumption_ids)

                rec.x_quarterly_consumption = sum(rec.x_quarterly_consumption_ids.mapped('x_quantity')) / len(rec.x_quarterly_consumption_ids) if len(rec.x_quarterly_consumption_ids) != 0 else 0

    @api.depends('x_start_date', 'x_end_date')
    def _compute_stat_values(self):
        for rec in self:
            stat_values = rec.compute_stat_values(rec.x_start_date, rec.x_end_date)
            rec.x_period_purchased = stat_values[0]
            rec.x_period_manufactured = stat_values[1]
            rec.x_period_consumed = stat_values[2]
            rec.x_period_sold = stat_values[3]
            rec.x_inventory_turnover = stat_values[4]
            rec.x_average_inventory = stat_values[5]
            rec.x_cogs = stat_values[6]
            rec.x_total_purchased = stat_values[7]
            rec.x_total_manufactured = stat_values[8]
            rec.x_total_consumed = stat_values[9]
            rec.x_total_sold = stat_values[10]
            rec.x_start_inventory = stat_values[11]
            rec.x_end_inventory = stat_values[12]
            if rec.x_start_date and rec.x_end_date:
                rec.x_period_days = (rec.x_end_date - rec.x_start_date).days
                rec.x_period_days = rec.x_period_days / rec.x_inventory_turnover if rec.x_inventory_turnover != 0 else 0

    @api.depends('description')
    def _compute_weight(self):
        for rec in self:
            unit_weight = 0
            if rec.description and rec.type != 'service':
                weight_ids = self.env['weight.database'].search([])
                for record in weight_ids:
                    weight_matched = True
                    if record.x_description_keyword_01:
                        weight_matched = False if record.x_description_keyword_01.x_name not in rec.description else True
                    if record.x_description_keyword_02:
                        weight_matched = False if record.x_description_keyword_02.x_name not in rec.description else True
                    if record.x_description_keyword_03:
                        weight_matched = False if record.x_description_keyword_03.x_name not in rec.description else True
                    if record.x_description_keyword_04:
                        weight_matched = False if record.x_description_keyword_04.x_name not in rec.description else True
                    if record.x_description_keyword_05:
                        weight_matched = False if record.x_description_keyword_05.x_name not in rec.description else True
                    if record.x_description_keyword_06:
                        weight_matched = False if record.x_description_keyword_06.x_name not in rec.description else True
                    if record.x_description_keyword_07:
                        weight_matched = False if record.x_description_keyword_07.x_name not in rec.description else True
                    if record.x_description_keyword_08:
                        weight_matched = False if record.x_description_keyword_08.x_name not in rec.description else True
                    if record.x_description_keyword_09:
                        weight_matched = False if record.x_description_keyword_09.x_name not in rec.description else True
                    if weight_matched:
                        unit_weight = record.x_unit_weight
                        break
            rec.x_unit_weight = unit_weight

    @api.depends('description', 'used_in_bom_count', 'categ_id')
    def compute_taraz_part_number(self):
        for rec in self:
            if rec.categ_id:
                if rec.type != 'service' and not rec.x_taraz_part_number_id and 'Raw Material' in rec.categ_id.display_name:
                    taraz_part_number_id = self.env['taraz.part.number'].search([('x_name', '=', rec.name)], limit=1)
                    if not taraz_part_number_id:
                        taraz_part_number = self.env['taraz.part.number'].compute_taraz_part_number(rec.description)
                        if taraz_part_number:
                            taraz_part_number_id = self.env['taraz.part.number'].search([('x_name', '=', taraz_part_number)], limit=1)

                    if taraz_part_number_id:
                        rec.x_taraz_part_number_id = taraz_part_number_id.id
                        break

                    if rec.name:
                        rec.x_taraz_part_number_id = self.env['taraz.part.number'].create({
                            'x_name': rec.name,
                            'x_description': rec.description,
                            'x_uom_id': rec.uom_id.id,
                        })
                elif rec.type != 'service' and rec.x_taraz_part_number_id and 'Raw Material' in rec.categ_id.display_name:
                    rec.x_taraz_part_number_id.x_description = rec.description
                    rec.x_taraz_part_number_id._compute_alternates()
                    rec.x_alternate_ids = rec.x_taraz_part_number_id.x_alternate_ids.filtered(
                        lambda x: x.x_product_id.id != rec.id
                    ).ids
                    rec.x_compromised_ids = rec.x_taraz_part_number_id.x_compromised_ids.ids

    @api.depends(
        'x_taraz_part_number_id',
        'x_taraz_part_number_id.x_alternate_ids',
        'x_taraz_part_number_id.x_compromised_ids',
    )
    def _compute_alt_and_comp(self):
        for rec in self:
            rec.x_taraz_part_number_id._compute_alternates()
            rec.x_alternates_exist = False
            rec.x_compromised_exist = False
            rec.x_alternate_ids = []
            rec.x_compromised_ids = []
            if rec.x_taraz_part_number_id:
                alternate_ids = rec.x_taraz_part_number_id.x_alternate_ids.filtered(
                    lambda x: x.x_product_id.id != rec.id
                )
                if alternate_ids:
                    rec.x_alternate_ids = alternate_ids.ids
                    rec.x_alternates_exist = True
                if rec.x_taraz_part_number_id.x_compromised_ids:
                    rec.x_compromised_ids = rec.x_taraz_part_number_id.x_compromised_ids.ids
                    rec.x_compromised_exist = True

    @api.onchange('x_other_name_tag_ids')
    def update_product_other_names(self):
        for rec in self:
            duplicate_record_id = self.env['product.duplicate.names'].search([('x_product_id', '=', rec._origin.id)])
            if not duplicate_record_id:
                duplicate_record_id = self.env['product.duplicate.names'].create({'x_product_id': rec._origin.id})
            duplicate_record_id.x_other_name_tag_ids = rec.x_other_name_tag_ids.ids if rec.x_other_name_tag_ids else False

    @api.onchange('dk_hs_code', 'x_hs_code_tr_id')
    def update_assigning_status(self):
        for rec in self:
            rec.x_htsus_assigning = 'manual'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = [
                '|', '|', '|',  '|', '|',
                ('name', operator, name),
                ('x_name_translation', operator, name),
                ('default_code', operator, name),
                ('x_other_name_tag_ids.x_name', operator, name),
                ('description', operator, name),
                ('x_description_translation', operator, name),
            ]
            product_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))

    @api.model
    def get_product_details(self):
        digi_key_codes = self.env['digikey.api'].search([], limit=1)

        # L77SDBH25SOL2RM5
        # MLFA1FTC10R0

        # # PELab
        # order_ids = self.env['mrp.production'].search([('name', 'in', [
        #     'WH/MO/00668', 'WH/MO/00839', 'WH/MO/00787', 'WH/MO/00680', 'WH/MO/00804', 'WH/MO/00675', 'WH/MO/00728',
        #     'WH/MO/00667', 'WH/MO/00205', 'WH/MO/00621', 'WH/MO/00756', 'WH/MO/00738', 'WH/MO/00722', 'WH/MO/00674',
        #     'WH/MO/00806', 'WH/MO/00745', 'WH/MO/00749', 'WH/MO/00681', 'WH/MO/00474', 'WH/MO/00476', 'WH/MO/00467',
        #     'WH/MO/00661',
        # ])])
        #
        # product_ids = order_ids.mapped('move_raw_ids').mapped('product_id').mapped('product_tmpl_id')
        #
        # product_ids.update({'dk_get_digikey_details': True})
        #
        # product_ids = self.env['product.template'].search(['&', ('dk_get_digikey_details', '!=', False),
        #                                                    '|', ('dk_digiKey_part_number', '=', False),
        #                                                    '|', ('dk_manufacturer_part_number', '=', False),
        #                                                    '|', ('dk_product_description', '=', False),
        #                                                    '|', ('dk_manufacturer', '=', False),
        #                                                    '|', ('dk_category', '=', False),
        #                                                    '|', ('dk_sub_category', '=', False),
        #                                                    ('dk_htsus_code', '=', False),
        #                                                    ], limit=495)

        domain = ['|', ('dk_category', '=', False), '|', ('dk_sub_category', '=', False),
                  '|', ('dk_htsus_code', '=', False), ('dk_manufacturer', '=', False)]

        product_ids = self.env['product.template'].search(domain)

        domain = [('type', '!=', 'service'), ('categ_id', 'in', [281, 269]), ('dk_get_digikey_details', '=', False),
                  ('dk_product_description', '!=', '<Response 404>: Not Found - The product was not found')]

        product_ids = product_ids.search(domain, limit=100)

        # raise UserError(len(product_ids))

        for product in product_ids:
            product.dk_get_digikey_details = True
            product_name = product.dk_digiKey_part_number if product.dk_digiKey_part_number else product.name

            # ---------- Making an API Call ----------
            product_search_url = 'https://api.digikey.com/Search/v3/Products/' + product_name
            headers = {
                'Authorization': 'Bearer ' + digi_key_codes.x_access_token,
                'X-DIGIKEY-Client-Id': 'tOGl7XKtaAxuKpzaUYE01BlTnbsbaPyY',
            }
            res = requests.get(product_search_url, headers=headers)

            if res.status_code == 429:  # Too Many Requests - Your rate limit has been exceeded
                break
                # raise UserError('<Response 429>: Your rate limit has been exceeded. Retry after ' +
                #                 str(datetime.now() + timedelta(seconds=int(res.headers['Retry-After']))))

            if res.status_code == 401:  # Unauthorized - Token is expired (Access Token)
                # ---------- Obtaining a new access token ----------
                url = 'https://api.digikey.com/v1/oauth2/token'
                data = {
                    'client_id': 'tOGl7XKtaAxuKpzaUYE01BlTnbsbaPyY',
                    'client_secret': '57PlKpI77hnn1vpC',
                    'refresh_token': digi_key_codes.x_refresh_token,
                    'grant_type': 'refresh_token',
                }
                res = requests.post(url, data=data)

                if res.status_code == 401:  # Unauthorized - Token is expired (Refresh Token)
                    # ---------- Getting the Access Token ----------
                    url = 'https://api.digikey.com/v1/oauth2/token'
                    data = {
                        'code': digi_key_codes.x_authorization_code,
                        'client_id': 'tOGl7XKtaAxuKpzaUYE01BlTnbsbaPyY',
                        'client_secret': '57PlKpI77hnn1vpC',
                        'redirect_uri': 'https://odoo.taraztechnologies.com/',
                        'grant_type': 'authorization_code',
                    }
                    res = requests.post(url, data=data)

                    if res.status_code == 400:  # Bad Request - The input model is invalid or malformed
                        raise UserError("<Response 400>: Bad Request - "
                                        "The input model is invalid or malformed - Get new authentication Code.")

                data_dict = res.json()
                digi_key_codes.x_access_token = data_dict.get('access_token')
                digi_key_codes.x_refresh_token = data_dict.get('refresh_token')

                # ---------- Making an new API Call ----------
                headers['Authorization'] = 'Bearer ' + digi_key_codes.x_access_token
                res = requests.get(product_search_url, headers=headers)

            try:
                data_dict = res.json()
            except ValueError:
                product.dk_product_description = '<Response 404>: Not Found - The product was not found'
                continue

            label = ''
            if data_dict.get('DigiKeyPartNumber'):
                product.dk_digiKey_part_number = data_dict.get('DigiKeyPartNumber')
            if data_dict.get('ManufacturerPartNumber'):
                product.dk_manufacturer_part_number = data_dict.get('ManufacturerPartNumber')
            if data_dict.get('ProductDescription'):
                dk_product_description = data_dict.get('ProductDescription')
                product.dk_product_description = dk_product_description
                label = dk_product_description.split(' ')[0]
            if data_dict.get('DetailedDescription'):
                product.dk_detailed_description = data_dict.get('DetailedDescription')
            if data_dict.get('LimitedTaxonomy'):
                dk_category = data_dict.get('LimitedTaxonomy').get('Value')
                type_id = self.env['product.type'].search([('x_name', '=', dk_category)])
                if not type_id:
                    type_id = self.env['product.type'].create({
                        'x_label': label,
                        'x_name': dk_category,
                    })
                product.dk_category = type_id.id

                if data_dict.get('LimitedTaxonomy').get('Children')[0]:
                    dk_sub_category = data_dict.get('LimitedTaxonomy').get('Children')[0].get('Value')
                    sub_type_id = self.env['product.sub.type'].search([('x_name', '=', dk_sub_category)])
                    if not sub_type_id:
                        sub_type_id = self.env['product.sub.type'].create({
                            'x_name': dk_sub_category,
                            'x_type_id': type_id.id,
                        })
                    product.dk_sub_category = sub_type_id.id
            if data_dict.get('HTSUSCode'):
                dk_htsus_code = data_dict.get('HTSUSCode')
                if len(dk_htsus_code) > 10:
                    hs_code = dk_htsus_code.replace(dk_htsus_code[-5:], '00')
                    hs_code_id = self.env['hs.code.database'].search([('x_hs_code', '=', hs_code)])
                    htsus_code_id = self.env['hs.codes'].search([('x_htsus_code_id.x_hs_code', '=', dk_htsus_code)])
                    if not htsus_code_id:
                        htsus_code_id = self.env['hs.codes'].create({
                            'x_htsus_code_id.x_hs_code': dk_htsus_code,
                            'x_hs_code': hs_code_id.id if hs_code_id else False,
                        })
                    product.dk_htsus_code = htsus_code_id.id
            if data_dict.get('Manufacturer'):
                product.dk_manufacturer = data_dict.get('Manufacturer').get('Value')

    def action_open_in_editor(self):
        action = self.env.ref('cus_product_360_view.action_open_taraz_part_number_from_product').read()[0]
        action['res_id'] = self.x_taraz_part_number_id.id
        return action

    def remove_dk_category(self):
        for rec in self:
            record_id = self.env['product.type'].search([('id', '=', rec.dk_category.id)])
            rec.dk_category = False
            record_id.x_search_unassigned = rec.name
            record_id.filter_unassigned()

    def remove_dk_sub_category(self):
        for rec in self:
            record_id = self.env['product.sub.type'].search([('id', '=', rec.dk_sub_category.id)])
            rec.dk_sub_category = False
            record_id.x_search_unassigned = rec.name
            record_id.filter_unassigned()

    def remove_dk_htsus_code(self):
        for rec in self:
            record_id = self.env['hs.codes'].search([('id', '=', rec.dk_htsus_code.id)])
            rec.dk_htsus_code = False
            rec.dk_hs_code = False
            rec.x_hs_code_tr_id = False
            record_id.x_search_unassigned = rec.name
            record_id.update_hs_codes_list()
            record_id.filter_unassigned()

    def write(self, vals):
        for rec in self:
            old_dk_category = rec.dk_category
            old_dk_sub_category = rec.dk_sub_category
            old_dk_htsus_code = rec.dk_htsus_code

            old_values = [rec.dk_category.x_label, rec.dk_sub_category.x_name,
                          rec.dk_htsus_code.x_htsus_code_id.x_hs_code, rec.dk_hs_code.x_hs_code,
                          rec.x_hs_code_tr_id.x_hs_code]

        old_tags = self.x_custom_tag_ids.ids
        res = super(ProductTemplate, self).write(vals)
        new_tags = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_tags, new_values=new_tags
            )

        for rec in self:
            new_dk_category = rec.dk_category
            new_dk_sub_category = rec.dk_sub_category
            new_dk_htsus_code = rec.dk_htsus_code

            record_name = rec.name
            field_names = [rec._fields['dk_category'].string, rec._fields['dk_sub_category'].string,
                           rec._fields['dk_htsus_code'].string, rec._fields['dk_hs_code'].string,
                           rec._fields['x_hs_code_tr_id'].string]
            new_values = [rec.dk_category.x_label, rec.dk_sub_category.x_name,
                          rec.dk_htsus_code.x_htsus_code_id.x_hs_code, rec.dk_hs_code.x_hs_code,
                          rec.x_hs_code_tr_id.x_hs_code]
            
            if old_dk_category != new_dk_category:
                if old_dk_category:
                    old_dk_category.x_product_ids = [(3, rec.id)]
                if new_dk_category:
                    new_dk_category.x_product_ids = [(4, rec.id)]
            if old_dk_sub_category != new_dk_sub_category:
                if old_dk_sub_category:
                    old_dk_sub_category.x_product_ids = [(3, rec.id)]
                if new_dk_sub_category:
                    new_dk_sub_category.x_product_ids = [(4, rec.id)]
            if old_dk_htsus_code != new_dk_htsus_code:
                if old_dk_htsus_code:
                    old_dk_htsus_code.x_product_ids = [(3, rec.id)]
                if new_dk_htsus_code:
                    new_dk_htsus_code.x_product_ids = [(4, rec.id)]

            if old_values != new_values:
                rec.dk_htsus_code.send_record_change(record_name, field_names, old_values, new_values)
                rec.dk_category.send_record_change(record_name, field_names, old_values, new_values)
                rec.dk_sub_category.send_record_change(record_name, field_names, old_values, new_values)
        return res

    def action_view_usage(self):
        action = self.env.ref('cus_product_360_view.action_component_usage').read()[0]
        action['domain'] = [('x_alternate_id', 'in', self.x_taraz_part_number_id.x_alternate_ids.ids)]
        return action

    def _compute_usage_count(self):
        for rec in self:
            rec.x_usage_count = self.env['component.usage'].search_count(
                [('x_alternate_id', 'in', rec.x_taraz_part_number_id.x_alternate_ids.ids)])

    def update_period(self):
        self.env['product.template'].search([]).x_start_date = datetime.date.today() - relativedelta(years=1)
        self.env['product.template'].search([]).x_end_date = datetime.date.today()
        self.env['taraz.part.number'].search([]).x_start_date = datetime.date.today() - relativedelta(years=1)
        self.env['taraz.part.number'].search([]).x_end_date = datetime.date.today()

    def compute_stat_values(self, s_date, e_date):
        for rec in self:
            if rec.type != 'service':
                total_purchased = sum(rec.x_purchase_history_ids.mapped('x_received_qty'))
                total_manufactured = sum(rec.x_manufacturing_history_ids.mapped('x_product_uom_qty'))
                total_consumed = sum(rec.x_consumption_history_ids.mapped('x_quantity_done')) + sum(rec.x_scrap_history_ids.filtered(lambda s: s.date_done).mapped('scrap_qty'))
                total_sold = sum(rec.x_sale_order_history_ids.mapped('x_qty_invoiced'))

                period_purchased = 0
                period_manufactured = 0
                period_consumed = 0
                period_sold = 0
                if not s_date and not e_date:
                    period_purchased = sum(rec.x_purchase_history_ids.mapped('x_received_qty'))
                    period_manufactured = sum(rec.x_manufacturing_history_ids.mapped('x_product_uom_qty'))
                    period_consumed = (sum(rec.x_consumption_history_ids.mapped('x_quantity_done'))
                                       + sum(rec.x_scrap_history_ids.filtered(lambda s: s.date_done).mapped('scrap_qty')))
                    period_sold = sum(rec.x_sale_order_history_ids.mapped('x_qty_invoiced'))
                elif s_date and not e_date:
                    period_purchased = sum(rec.x_purchase_history_ids.filtered(lambda l: l.x_order_date >= s_date).mapped('x_received_qty'))
                    period_manufactured = sum(rec.x_manufacturing_history_ids.filtered(lambda l: l.x_date >= s_date).mapped('x_product_uom_qty'))
                    period_consumed = (sum(rec.x_consumption_history_ids.filtered(lambda l: l.x_date >= s_date).mapped('x_quantity_done'))
                                       + sum(rec.x_scrap_history_ids.filtered(lambda s: s.date_done).filtered(lambda s: s.date_done.date() >= s_date).mapped('scrap_qty')))
                    period_sold = sum(rec.x_sale_order_history_ids.filtered(lambda l: l.x_order_date >= s_date).mapped('x_qty_invoiced'))
                elif not s_date and e_date:
                    period_purchased = sum(rec.x_purchase_history_ids.filtered(lambda l: l.x_order_date <= e_date).mapped('x_received_qty'))
                    period_manufactured = sum(rec.x_manufacturing_history_ids.filtered(lambda l: l.x_date <= e_date).mapped('x_product_uom_qty'))
                    period_consumed = (sum(rec.x_consumption_history_ids.filtered(lambda l: l.x_date <= e_date).mapped('x_quantity_done'))
                                       + sum(rec.x_scrap_history_ids.filtered(lambda s: s.date_done).filtered(lambda s: s.date_done.date() <= e_date).mapped('scrap_qty')))
                    period_sold = sum(rec.x_sale_order_history_ids.filtered(lambda l: l.x_order_date <= e_date).mapped('x_qty_invoiced'))
                elif s_date and e_date:
                    period_purchased = sum(rec.x_purchase_history_ids.filtered(lambda l: s_date <= l.x_order_date <= e_date).mapped('x_received_qty'))
                    period_manufactured = sum(rec.x_manufacturing_history_ids.filtered(lambda l: s_date <= l.x_date <= e_date).mapped('x_product_uom_qty'))
                    period_consumed = (sum(rec.x_consumption_history_ids.filtered(lambda l: s_date <= l.x_date <= e_date).mapped('x_quantity_done'))
                                       + sum(rec.x_scrap_history_ids.filtered(lambda s: s.date_done).filtered(lambda s: s_date <= s.date_done.date() <= e_date).mapped('scrap_qty')))
                    period_sold = sum(rec.x_sale_order_history_ids.filtered(lambda l: s_date <= l.x_order_date <= e_date).mapped('x_qty_invoiced'))

                s_inventory = 0
                e_inventory = 0
                cogs = 0
                if s_date and e_date:
                    s_inventory += sum(rec.x_purchase_history_ids.filtered(lambda p: p.x_order_date <= s_date).mapped('x_subtotal'))
                    e_inventory += sum(rec.x_purchase_history_ids.filtered(lambda p: p.x_order_date <= e_date).mapped('x_subtotal'))

                    s_inventory += sum(rec.x_manufacturing_history_ids.filtered(lambda p: p.x_date <= s_date).mapped('x_cost'))
                    e_inventory += sum(rec.x_manufacturing_history_ids.filtered(lambda p: p.x_date <= e_date).mapped('x_cost'))

                    s_inventory -= sum(rec.x_consumption_history_ids.filtered(lambda p: p.x_date <= s_date).mapped('x_cost'))
                    e_inventory -= sum(rec.x_consumption_history_ids.filtered(lambda p: p.x_date <= e_date).mapped('x_cost'))

                    s_inventory -= sum(rec.x_scrap_history_ids.filtered(lambda p: p.date_done).filtered(lambda p: p.date_done.date() <= s_date).mapped('x_cost'))
                    e_inventory -= sum(rec.x_scrap_history_ids.filtered(lambda p: p.date_done).filtered(lambda p: p.date_done.date() <= e_date).mapped('x_cost'))

                    s_inventory -= sum(rec.x_sale_order_history_ids.filtered(lambda p: p.x_order_date <= s_date).mapped('x_cost'))
                    e_inventory -= sum(rec.x_sale_order_history_ids.filtered(lambda p: p.x_order_date <= e_date).mapped('x_cost'))

                    cogs += sum(rec.x_consumption_history_ids.filtered(lambda p: s_date <= p.x_date <= e_date).mapped('x_cost'))
                    cogs += sum(rec.x_scrap_history_ids.filtered(lambda p: p.date_done).filtered(lambda p: s_date <= p.date_done.date() <= e_date).mapped('x_cost'))
                    cogs += sum(rec.x_sale_order_history_ids.filtered(lambda p: s_date <= p.x_order_date <= e_date).mapped('x_cost'))

                a_inventory = (s_inventory + e_inventory) / 2
                inventory_turnover = round(cogs / a_inventory, 2) if a_inventory != 0 else 0

                return [
                    period_purchased,
                    period_manufactured,
                    period_consumed,
                    period_sold,
                    inventory_turnover,
                    a_inventory,
                    cogs,
                    total_purchased,
                    total_manufactured,
                    total_consumed,
                    total_sold,
                    s_inventory,
                    e_inventory
                ]
            else:
                return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def unlink(self):
        self.x_purchase_history_ids.unlink()
        self.x_consumption_history_ids.unlink()
        self.x_manufacturing_history_ids.unlink()
        return super(ProductTemplate, self).unlink()


class ProductSeries(models.Model):
    _inherit = "product.series"

    x_hs_code_id = fields.Many2one(comodel_name="hs.code.database", string="HS Code", required=False, )


class DigiKeyApi(models.Model):
    _name = "digikey.api"
    _description = "Country Scenario Rules"
    _rec_name = "x_refresh_token"

    x_access_token = fields.Char(string='Digi-Key Access Token (Validity: 30 minutes)', )
    x_refresh_token = fields.Char(string='Digi-Key Refresh Token (Validity: 90 days)', )
    x_authorization_code = fields.Char(string='Digi-Key Authorization Code (Validity: 1 minute)', )

    def open_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://api.digikey.com/v1/oauth2/authorize?response_type=code&client_id'
                   '=tOGl7XKtaAxuKpzaUYE01BlTnbsbaPyY&redirect_uri=https%3A%2F%2Fodoo.taraztechnologies.com%2F',
            'target': 'new',
        }


class ProductPurchasePackaging(models.Model):
    _name = "product.purchase.packaging"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Purchase Packaging"
    _rec_name = "display_name"

    x_name = fields.Char(
        string='Type',
        tracking=True)
    x_roq = fields.Float(
        string='Reorder Quantity',
        digits="Product Unit of Measure",
        tracking=True,
        required=False)
    x_quantity_buffer = fields.Float(
        string='Reel Loading Buffer',
        digits="Product Unit of Measure",
        tracking=True,
        required=False)

    x_search_unassigned = fields.Char(string='Search Unassigned', required=False)
    x_unassigned_categ_id = fields.Many2one(comodel_name='product.category', string='Category Unassigned', default=269,
                                            domain="[('id', 'in', [269, 271])]")

    x_unassigned_product_ids = fields.Many2many('product.template',
                                                'product_template_product_purchase_packaging_rel_1',
                                                'product_template_id_1', 'product_purchase_packaging_id_1',
                                                string='Unassigned Products', tracking=True)

    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends('x_name', 'x_roq', 'x_quantity_buffer')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s - %s (%s)' % (rec.x_name, rec.x_roq, rec.x_quantity_buffer)

    def select_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_product_purchase_packaging_select = True

    def unselect_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_product_purchase_packaging_select = False

    def update_assigned(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                if product.x_product_purchase_packaging_select:
                    product.x_product_purchase_packaging_id = rec.id
                    product.x_product_purchase_packaging_select = False
            rec.filter_unassigned()

    @api.onchange('x_unassigned_categ_id', 'x_search_unassigned')
    def filter_unassigned(self):
        for rec in self:
            domain = [('x_product_purchase_packaging_id', '=', False)]
            if rec.x_unassigned_categ_id:
                domain.append(('categ_id', '=', rec.x_unassigned_categ_id.id))
            else:
                domain.append(('categ_id', 'in', [269, 271]))

            if rec.x_search_unassigned:
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', rec.x_search_unassigned))
                domain.append(('x_taraz_part_number_id', 'ilike', rec.x_search_unassigned))
                domain.append(('description', 'ilike', rec.x_search_unassigned))

            product_ids = self.env['product.template'].search(domain).ids
            rec.x_unassigned_product_ids = [(6, 0, product_ids)]

    def send_record_change(self, record_name, field_names, old_values, new_values):
        for rec in self:
            body = "<strong>" + record_name + "<strong> <br/>"

            values = zip(field_names, old_values, new_values)

            for value in values:
                if value[1] != value[2]:
                    body += "<span style='color:#A00;font-weight: normal;'>&emsp;&#8226; " + value[0] + ": "
                    if not value[1] and value[2]:
                        body += value[2] + '</span> <br/>'
                    elif value[1] and not value[2]:
                        body += value[1] + ' &#8594</span> <br/>'
                    else:
                        body += value[1] + ' &#8594 ' + value[2] + '</span> <br/>'
            rec.message_post(message_type="comment", body=body)


class ProductType(models.Model):
    _name = "product.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Type"
    _rec_name = "display_name"

    x_name = fields.Char(string='Type', tracking=True)
    x_label = fields.Char(string='Label', tracking=True)

    x_sub_type_ids = fields.One2many(comodel_name='product.sub.type',  tracking=True,
                                     inverse_name='x_type_id', string='Sub Types')
    x_product_ids = fields.Many2many(comodel_name='product.template', string='Products', tracking=True)

    x_search_unassigned = fields.Char(string='Search Unassigned', required=False)
    x_unassigned_categ_id = fields.Many2one(comodel_name='product.category', string='Category Unassigned', default=269,
                                            domain="[('id', 'in', [269, 271])]")

    x_unassigned_product_ids = fields.Many2many('product.template', 'product_template_product_type_rel_1',
                                                'product_template_id_1', 'product_sub_id_1',
                                                string='Unassigned Products', tracking=True)

    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends('x_label', 'x_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s (%s)' % (rec.x_label, rec.x_name)

    def select_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_type_select = True

    def unselect_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_type_select = False

    def update_assigned(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                if product.x_type_select:
                    product.x_type_assigning = 'manual'
                    product.dk_category = rec.id
                    product.x_type_select = False
            rec.filter_unassigned()

    @api.onchange('x_unassigned_categ_id', 'x_search_unassigned', 'x_product_ids')
    def filter_unassigned(self):
        for rec in self:
            domain = [('dk_category', '=', False)]
            if rec.x_unassigned_categ_id:
                domain.append(('categ_id', '=', rec.x_unassigned_categ_id.id))
            else:
                domain.append(('categ_id', 'in', [269, 271]))

            if rec.x_search_unassigned:
                domain.append('|')
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', rec.x_search_unassigned))
                domain.append(('x_taraz_part_number_id', 'ilike', rec.x_search_unassigned))
                domain.append(('description', 'ilike', rec.x_search_unassigned))
                domain.append(('dk_sub_category', 'ilike', rec.x_search_unassigned))

            product_ids = self.env['product.template'].search(domain).ids
            rec.x_unassigned_product_ids = [(6, 0, product_ids)]

    def send_record_change(self, record_name, field_names, old_values, new_values):
        for rec in self:
            body = "<strong>" + record_name + "<strong> <br/>"

            values = zip(field_names, old_values, new_values)

            for value in values:
                if value[1] != value[2]:
                    body += "<span style='color:#A00;font-weight: normal;'>&emsp;&#8226; " + value[0] + ": "
                    if not value[1] and value[2]:
                        body += value[2] + '</span> <br/>'
                    elif value[1] and not value[2]:
                        body += value[1] + ' &#8594</span> <br/>'
                    else:
                        body += value[1] + ' &#8594 ' + value[2] + '</span> <br/>'
            rec.message_post(message_type="comment", body=body)

    def unlink(self):
        self.x_sub_type_ids.unlink()
        return super(ProductType, self).unlink()


class ProductSubType(models.Model):
    _name = "product.sub.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Sub Type"
    _rec_name = "x_name"

    x_name = fields.Char(string='Sub-Type', tracking=True)
    x_type_id = fields.Many2one(comodel_name="product.type", string="Type", required=True, tracking=True)
    x_product_ids = fields.Many2many(comodel_name='product.template', string='Products', tracking=True)

    x_search_unassigned = fields.Char(string='Search Unassigned', required=False)
    x_unassigned_categ_id = fields.Many2one(comodel_name='product.category', string='Category Unassigned', default=269,
                                            domain="[('id', 'in', [269, 271])]")

    x_unassigned_product_ids = fields.Many2many('product.template', 'product_template_product_sub_type_rel_1',
                                                'product_template_id_1', 'product_sub_type_id_1',
                                                string='Unassigned Products', tracking=True)

    def select_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_sub_type_select = True

    def unselect_all(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                product.x_sub_type_select = False

    def update_assigned(self):
        for rec in self:
            for product in rec.x_unassigned_product_ids:
                if product.x_sub_type_select:
                    product.x_sub_type_assigning = 'manual'
                    product.dk_sub_category = rec.id
                    product.dk_category = rec.x_type_id.id
                    product.x_sub_type_select = False
            rec.filter_unassigned()

    @api.onchange('x_unassigned_categ_id', 'x_search_unassigned', 'x_product_ids')
    def filter_unassigned(self,):
        for rec in self:
            domain = [('dk_sub_category', '=', False)]
            if rec.x_unassigned_categ_id:
                domain.append(('categ_id', '=', rec.x_unassigned_categ_id.id))
            else:
                domain.append(('categ_id', 'in', [269, 271]))

            if rec.x_search_unassigned:
                domain.append('|')
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', rec.x_search_unassigned))
                domain.append(('x_taraz_part_number_id', 'ilike', rec.x_search_unassigned))
                domain.append(('description', 'ilike', rec.x_search_unassigned))
                domain.append(('dk_category', 'ilike', rec.x_search_unassigned))

            product_ids = self.env['product.template'].search(domain).ids
            rec.x_unassigned_product_ids = [(6, 0, product_ids)]

    def send_record_change(self, record_name, field_names, old_values, new_values):
        for rec in self:
            body = "<strong>" + record_name + "<strong> <br/>"

            values = zip(field_names, old_values, new_values)

            for value in values:
                if value[1] != value[2]:
                    body += "<span style='color:#A00;font-weight: normal;'>&emsp;&#8226; " + value[0] + ": "
                    if not value[1] and value[2]:
                        body += value[2] + '</span> <br/>'
                    elif value[1] and not value[2]:
                        body += value[1] + ' &#8594</span> <br/>'
                    else:
                        body += value[1] + ' &#8594 ' + value[2] + '</span> <br/>'
            rec.message_post(message_type="comment", body=body)


class ProductAccessory(models.Model):
    _name = "product.accessory"
    _description = "Product Accessories"
    
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_accessory_id = fields.Many2one(
        comodel_name='product.product', string='Accessory',
        required=True, domain="[('type', 'in', ('product', 'consu'))]"
    )
    x_description = fields.Text(related="x_accessory_id.description")
    x_short_description = fields.Char(related="x_accessory_id.x_short_description")
    x_quantity = fields.Float(string='Quantity', required=False)
    x_uom_id = fields.Many2one(related="x_accessory_id.uom_id")
    x_comment = fields.Char(string="Comment", required=False)
    x_active = fields.Boolean(string='Active',  default=True)
    