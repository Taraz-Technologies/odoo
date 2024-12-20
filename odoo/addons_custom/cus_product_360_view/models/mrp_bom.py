from odoo import _, api, models, fields
from odoo.exceptions import UserError

from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    x_scenario_ids = fields.Many2many(comodel_name='country.scenario.rule', string='Scenarios')

    x_desc_compare_scenario_ids = fields.Many2many('country.scenario.rule', 'country_scenario_rule_mrp_bom_rel_1',
                                                   'country_scenario_rule_id_1', 'mrp_bom_id_1',
                                                   string='HS Code Details', tracking=True)

    x_letter_head_report = fields.Boolean(string='Letter Head Report?', required=False)
    x_show_cost = fields.Boolean(string='Show Cost?', required=False)
    x_show_part = fields.Boolean(string='Show Part#?', required=False)
    x_show_hidden_countries = fields.Boolean(string='Show All COOs?', required=False)
    x_hidden_country_ids = fields.Many2many(comodel_name='res.country', string='Hide COOs')
    x_show_coo_bom_lines = fields.Boolean(string='COO BOM Lines?', required=False)
    x_show_ecommerce_values = fields.Boolean(string='Ecommerce Values?', required=False)
    x_end_date = fields.Date(string='Currency End Date', required=False)

    x_title = fields.Char(string='Report Title', required=False)
    x_revision = fields.Char(string='Report Revision', required=False)
    x_revision_details = fields.Html(string='Revision Details', required=False)
    x_about_taraz = fields.Html(string='About Taraz', required=False)
    x_disclaimer = fields.Html(string='Disclaimer', required=False)

    x_heading_0 = fields.Char(string='Report Heading', required=False)
    x_comment_0 = fields.Html(string='Report Comment', required=False)

    x_disable_1 = fields.Boolean(string='Disable Table 1', required=False)
    x_heading_1 = fields.Char(string='Table 1 Heading', required=False)
    x_comment_1_top = fields.Html(string='Table 1 Top Text', required=False)
    x_comment_1_bot = fields.Html(string='Table 1 Bottom Text', required=False)

    x_disable_2 = fields.Boolean(string='Disable Table 2', required=False)
    x_heading_2 = fields.Char(string='Table 2 Heading', required=False)
    x_comment_2_top = fields.Html(string='Table 2 Top Text', required=False)
    x_comment_2_bot = fields.Html(string='Table 2 Bottom Text', required=False)

    x_disable_3 = fields.Boolean(string='Disable Table 3', required=False)
    x_heading_3 = fields.Char(string='Table 3 Heading', required=False)
    x_comment_3_top = fields.Html(string='Table 3 Top Text', required=False)
    x_comment_3_bot = fields.Html(string='Table 3 Bottom Text', required=False)

    x_disable_4 = fields.Boolean(string='Disable Table 4', required=False)
    x_heading_4 = fields.Char(string='Table 4 Heading', required=False)
    x_comment_4_top = fields.Html(string='Table 4 Top Text', required=False)
    x_comment_4_bot = fields.Html(string='Table 4 Bottom Text', required=False)

    x_disable_5 = fields.Boolean(string='Disable Table 5', required=False)
    x_heading_5 = fields.Char(string='Table 5 Heading', required=False)
    x_comment_5_top = fields.Html(string='Table 5 Top Text', required=False)
    x_comment_5_bot = fields.Html(string='Table 5 Bottom Text', required=False)

    x_disable_6 = fields.Boolean(string='Disable Table 6', required=False)
    x_heading_6 = fields.Char(string='Table 6 Heading', required=False)
    x_comment_6_top = fields.Html(string='Table 6 Top Text', required=False)
    x_comment_6_bot = fields.Html(string='Table 6 Bottom Text', required=False)

    x_disable_7 = fields.Boolean(string='Disable Table 7', required=False)
    x_heading_7 = fields.Char(string='Table 7 Heading', required=False)
    x_comment_7_top = fields.Html(string='Table 7 Top Text', required=False)
    x_comment_7_bot = fields.Html(string='Table 7 Bottom Text', required=False)

    x_disable_8 = fields.Boolean(string='Disable Table 8', required=False)
    x_heading_8 = fields.Char(string='Table 8 Heading', required=False)
    x_comment_8_top = fields.Html(string='Table 8 Top Text', required=False)
    x_comment_8_bot = fields.Html(string='Table 8 Bottom Text', required=False)

    x_disable_9 = fields.Boolean(string='Disable Table 9', required=False)
    x_heading_9 = fields.Char(string='Table 9 Heading', required=False)
    x_comment_9_top = fields.Html(string='Table 9 Top Text', required=False)
    x_comment_9_bot = fields.Html(string='Table 9 Bottom Text', required=False)

    x_disable_10 = fields.Boolean(string='Disable Table 10', required=False)
    x_heading_10 = fields.Char(string='Table 10 Heading', required=False)
    x_comment_10_top = fields.Html(string='Table 10 Top Text', required=False)
    x_comment_10_bot = fields.Html(string='Table 10 Bottom Text', required=False)

    x_disable_11 = fields.Boolean(string='Disable Table 11', required=False)
    x_heading_11 = fields.Char(string='Table 11 Heading', required=False)
    x_comment_11_top = fields.Html(string='Table 11 Top Text', required=False)
    x_comment_11_bot = fields.Html(string='Table 11 Bottom Text', required=False)

    x_disable_12 = fields.Boolean(string='Disable Table 12', required=False)
    x_heading_12 = fields.Char(string='Table 12 Heading', required=False)
    x_comment_12_top = fields.Html(string='Table 12 Top Text', required=False)
    x_comment_12_bot = fields.Html(string='Table 12 Bottom Text', required=False)

    x_disable_13 = fields.Boolean(string='Disable Table 13', required=False)
    x_heading_13 = fields.Char(string='Table 13 Heading', required=False)
    x_comment_13_top = fields.Html(string='Table 13 Top Text', required=False)
    x_comment_13_bot = fields.Html(string='Table 13 Bottom Text', required=False)

    def get_bom_data(self):
        for rec in self:
            bom_data = [{
                'id': rec.id,
                'bom_qty': rec.product_qty,
                'product_qty': rec.product_qty,
            }]

            for line in rec.bom_line_ids:
                if line.product_id.categ_id.id not in [269, 271]:
                    domain = [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)]
                    bom_id_1 = self.env['mrp.bom'].search(domain, order="id desc", limit=1)
                    bom_data.append({
                        'id': bom_id_1.id,
                        'bom_qty': bom_id_1.product_qty,
                        'product_qty': line.product_qty,
                    })
                    for line_1 in bom_id_1.bom_line_ids:
                        if line_1.product_id.categ_id.id not in [269, 271]:
                            domain = [('product_tmpl_id', '=', line_1.product_id.product_tmpl_id.id)]
                            bom_id_2 = self.env['mrp.bom'].search(domain, order="id desc", limit=1)
                            bom_data.append({
                                'id': bom_id_2.id,
                                'bom_qty': bom_id_2.product_qty,
                                'product_qty': line.product_qty,
                            })
                            for line_2 in bom_id_2.bom_line_ids:
                                if line_2.product_id.categ_id.id not in [269, 271]:
                                    domain = [('product_tmpl_id', '=', line_2.product_id.product_tmpl_id.id)]
                                    bom_id_3 = self.env['mrp.bom'].search(domain, order="id desc", limit=1)
                                    bom_data.append({
                                        'id': bom_id_3.id,
                                        'bom_qty': bom_id_3.product_qty,
                                        'product_qty': line.product_qty,
                                    })
                                    for line_3 in bom_id_3.bom_line_ids:
                                        if line_3.product_id.categ_id.id not in [269, 271]:
                                            domain = [('product_tmpl_id', '=', line_3.product_id.product_tmpl_id.id)]
                                            bom_id_4 = self.env['mrp.bom'].search(domain, order="id desc", limit=1)
                                            bom_data.append({
                                                'id': bom_id_4.id,
                                                'bom_qty': bom_id_4.product_qty,
                                                'product_qty': line.product_qty,
                                            })
                                            for line_4 in bom_id_4.bom_line_ids:
                                                if line_4.product_id.categ_id.id not in [269, 271]:
                                                    domain = [('product_tmpl_id', '=', line_4.product_id.product_tmpl_id.id)]
                                                    bom_id_5 = self.env['mrp.bom'].search(domain, order="id desc", limit=1)
                                                    bom_data.append({
                                                        'id': bom_id_5.id,
                                                        'bom_qty': bom_id_5.product_qty,
                                                        'product_qty': line.product_qty,
                                                    })

            return bom_data

    def get_components_hs_code(self):
        for rec in self:
            default_scenario_id = self.env['country.scenario.rule'].search([('x_default_scenario', '!=', False)])

            country_data = []
            for scenario in rec.x_scenario_ids:
                country_data.append({
                    'label': scenario.x_label,
                    'country': scenario.x_country_id.name,
                    # Cost Breakdown
                    'assessed_value': 0,
                    'duties_cost': 0,
                    'vat_cost': 0,
                    'it_cost': 0,
                    'total_cost': 0,
                    # Tax Breakdown
                    'cd_total': 0,
                    'acd_total': 0,
                    'rd_total': 0,
                    'st_total': 0,
                    'ast_total': 0,
                    'it_total': 0,
                    'cess_total': 0,
                    'tax_total': 0,
                    # Labels
                    'av_label': scenario.x_av_label,
                    'cd_label': scenario.x_cd_label,
                    'acd_label': scenario.x_acd_label,
                    'rd_label': scenario.x_rd_label,
                    'st_label': scenario.x_st_label,
                    'ast_label': scenario.x_ast_label,
                    'it_label': scenario.x_it_label,
                    'cess_label': scenario.x_cess_label,
                })

            bom_data = rec.get_bom_data()

            bom_ids = [bom_id['id'] for bom_id in bom_data]
            bom_ids = self.env['mrp.bom'].search([('id', 'in', bom_ids)])

            hs_codes_data = []
            hs_codes_list = []
            for bom in bom_ids:
                for line in bom.bom_line_ids:
                    hs_code = line.product_id.dk_hs_code

                    if line.product_id.categ_id.id in [269, 271] and hs_code:
                        part_type = 'Imported' if line.product_id.categ_id.id == 269 else 'Local'
                        hs_code_part_type = hs_code.x_hs_code + part_type

                        if hs_code_part_type not in hs_codes_list:
                            hs_codes_list.append(hs_code_part_type)
                            values = {
                                'hs_code': hs_code.x_hs_code,
                                # Taxes
                                'country_data': [],
                                'default_total_tax': 0,
                                # Parts Detail
                                'part_type': part_type,
                                'line_count': 0,
                                'cnf_value': 0,
                                'parts_detail': [],
                                'category_list': [],
                                'sub_category_list': [],
                                'htsus_code_list': [],
                            }
                            hs_codes_data.append(values)

                        for scenario in rec.x_scenario_ids:
                            for hs_code_data in hs_codes_data:
                                country_hs_code = False
                                if scenario.x_country_id.name == 'Pakistan':
                                    country_hs_code = line.product_id.dk_hs_code
                                elif scenario.x_country_id.name == 'Turkey':
                                    country_hs_code = line.product_id.x_hs_code_tr_id
                                elif line.product_id.dk_htsus_code:
                                    country_hs_code = line.product_id.dk_htsus_code.x_hs_code_ids.filtered(
                                        lambda l: l.x_country_id.id == scenario.x_country_id.id)

                                country_zone = False
                                hs_code_tariff = False
                                av_p = 0
                                if country_hs_code:
                                    if line.product_id.x_country_id:
                                        change_id = country_hs_code.x_financial_changes_ids.filtered(
                                            lambda l: l.x_country_id.id == line.product_id.x_country_id.id
                                                      and l.x_start_date <= datetime.now().date()
                                            # and l.x_start_date <= datetime.now().date() <= l.x_end_date
                                        )
                                        av_p = 100 + change_id.x_change if change_id else 0
                                    for tariff in country_hs_code.x_country_tariff_ids:
                                        if tariff.x_scenario_id.id == scenario.id:
                                            zone = tariff.x_import_zone_id
                                            if line.product_id.x_country_id.id in zone.x_country_ids.ids:
                                                country_zone = tariff.x_import_zone_id
                                                hs_code_tariff = tariff
                                                break

                                    change_id = country_hs_code.x_financial_changes_ids.filtered(
                                        lambda l: l.x_country_id.id == line.product_id.x_country_id.id
                                                  and l.x_start_date <= datetime.now().date()
                                    )
                                    av_p = 100 + change_id.x_change if change_id else 0

                                assessed_value_p = hs_code_tariff.x_assessed_value if hs_code_tariff else 0
                                assessed_value_p = assessed_value_p if av_p == 0 else av_p
                                custom_duty = hs_code_tariff.x_custom_duty if hs_code_tariff else 0
                                additional_cd = hs_code_tariff.x_additional_custom_duty if hs_code_tariff else 0
                                regulatory_duty = hs_code_tariff.x_regulatory_duty if hs_code_tariff else 0
                                flat_cd = hs_code_tariff.x_flat_cd if hs_code_tariff else 0
                                sale_tax = hs_code_tariff.x_sale_tax if hs_code_tariff else 0
                                additional_st = hs_code_tariff.x_additional_sale_tax if hs_code_tariff else 0
                                income_tax = hs_code_tariff.x_income_tax if hs_code_tariff else 0
                                cess = hs_code_tariff.x_cess if hs_code_tariff else 0

                                if hs_code_data['hs_code'] == hs_code.x_hs_code \
                                        and hs_code_data['part_type'] == part_type and country_zone:

                                    add_country_data = True
                                    for data in hs_code_data['country_data']:
                                        if data['hs_code'] == country_hs_code.x_hs_code \
                                                and data['zone'] == country_zone:
                                            add_country_data = False
                                            break

                                    if not add_country_data:
                                        break

                                    hs_code_data['country_data'].append({
                                        'label': scenario.x_label,
                                        'country': scenario.x_country_id.name,
                                        'country_code': scenario.x_country_id.code,
                                        'hs_code': country_hs_code.x_hs_code if country_hs_code else '',
                                        'desc_0': country_hs_code.x_chapter_description if country_hs_code else '',
                                        'desc_1': country_hs_code.x_heading_description if country_hs_code else '',
                                        'desc_2': country_hs_code.x_level_1_description if country_hs_code else '',
                                        'desc_3': country_hs_code.x_level_2_description if country_hs_code else '',
                                        'desc_4': country_hs_code.x_level_3_description if country_hs_code else '',
                                        'desc_5': country_hs_code.x_level_4_description if country_hs_code else '',
                                        'desc_6': country_hs_code.x_level_5_description if country_hs_code else '',
                                        'desc_7': country_hs_code.x_level_6_description if country_hs_code else '',
                                        'desc_8': country_hs_code.x_hs_code_description if country_hs_code else '',
                                        'zone': country_zone,
                                        'coos': '',
                                        # Taxes
                                        'assessed_value_p': assessed_value_p if 'Imported' in hs_code_part_type else 0,
                                        'custom_duty': custom_duty if 'Imported' in hs_code_part_type else 0,
                                        'additional_custom_duty': additional_cd if 'Imported' in hs_code_part_type else 0,
                                        'regulatory_duty': regulatory_duty if 'Imported' in hs_code_part_type else 0,
                                        'flat_cd': flat_cd if 'Imported' in hs_code_part_type else 0,
                                        'sale_tax': sale_tax if 'Imported' in hs_code_part_type else 0,
                                        'additional_sale_tax': additional_st if 'Imported' in hs_code_part_type else 0,
                                        'income_tax': income_tax if 'Imported' in hs_code_part_type else 0,
                                        'cess': cess if 'Imported' in hs_code_part_type else 0,
                                        # Taxes Formula
                                        'cd_formula': scenario.x_cd_formula,
                                        'acd_formula': scenario.x_acd_formula,
                                        'rd_formula': scenario.x_rd_formula,
                                        'st_formula': scenario.x_st_formula,
                                        'ast_formula': scenario.x_ast_formula,
                                        'it_formula': scenario.x_it_formula,
                                        'cess_formula': scenario.x_cess_formula,
                                        # Cost
                                        'assessed_value': 0,
                                        'cd_value': 0,
                                        'acd_value': 0,
                                        'rd_value': 0,
                                        'st_value': 0,
                                        'ast_value': 0,
                                        'it_value': 0,
                                        'cess_value': 0,
                                        'total_tax': 0,
                                        'total_cost': 0,
                                    })
                                    break

            hs_codes_data.append({
                'hs_code': 'UNDEFINED',
                # Taxes
                'country_data': [],
                'default_total_tax': 0,
                # Parts Detail
                'part_type': 'Imported',
                'line_count': 0,
                'cnf_value': 0,
                'parts_detail': [],
                'category_list': [],
                'sub_category_list': [],
                'htsus_code_list': [],
            })

            total = {
                'cnf_value': 0,
                'line_count': 0,
                'part_count': 0,
                'imported_parts': 0,
                'local_parts': 0,
                'ecommerce_stores': 0,
                'conventional_stores': 0,
                'us_codes': 0,
                'pk_codes': 0,
                'tr_codes': 0,
            }

            vendors = []

            coo_countries = []
            coo_data = []
            sourcing_countries = []
            sourcing_data = []
            ecia_vendors = []
            hs_code_group = []
            total_us_codes = []
            total_pk_codes = []
            total_tr_codes = []
            htsus_codes = []
            hs_code_mapping = []
            parts_by_hs_code = [{
                'parts': [],
                'us_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'pk_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'tr_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'group_cnf': 0,
                'htsus_code': 'Undefined',
            }]

            for data_list in hs_codes_data:
                for bom_id in bom_ids:
                    bom_qty = next((bom['bom_qty'] for bom in bom_data if bom['id'] == bom_id.id), None)
                    product_qty = next((bom['product_qty'] for bom in bom_data if bom['id'] == bom_id.id), None)
                    qty_multiplier = product_qty / bom_qty if bom_qty != 0 else 0

                    for line in bom_id.bom_line_ids:
                        if line.product_id.categ_id.id in [269, 271]:
                            hs_code = line.product_id.dk_hs_code
                            coo = line.product_id.x_country_id
                            if hs_code.x_hs_code == data_list['hs_code'] \
                                    or (not hs_code and data_list['hs_code'] == 'UNDEFINED'):
                                product_type = line.product_id.dk_category
                                product_sub_type = line.product_id.dk_sub_category
                                htsus_code = line.product_id.dk_htsus_code
                                pk_hs_code = line.product_id.dk_hs_code
                                tr_hs_code = line.product_id.x_hs_code_tr_id
                                line_quantity = line.product_qty * qty_multiplier

                                if htsus_code not in htsus_codes:
                                    htsus_codes.append(htsus_code)
                                    in_hs_code = False
                                    for code in htsus_code.x_hs_code_ids:
                                        if code.x_country_id.name == 'India':
                                            in_hs_code = code.x_hs_code
                                            break

                                    hs_code_mapping.append({
                                        'us_hs_code': htsus_code.x_htsus_code_id.x_hs_code,
                                        'pk_hs_code': pk_hs_code.x_hs_code,
                                        'tr_hs_code': tr_hs_code.x_hs_code,
                                        'in_hs_code': in_hs_code,
                                    })

                                line_price = 0
                                if line.product_id.x_purchase_history_ids:
                                    history_id = line.product_id.x_purchase_history_ids.filtered(
                                        lambda l: l.id == max(line.product_id.x_purchase_history_ids.ids)
                                    )
                                    line_price = history_id.x_unit_cnf * line_quantity

                                    sourcing_country = history_id.x_partner_id.country_id

                                    partner_tags = history_id.x_partner_id.category_id

                                    if history_id.x_partner_id not in vendors:
                                        vendors.append(history_id.x_partner_id)

                                        if sourcing_country not in sourcing_countries:
                                            sourcing_countries.append(sourcing_country)
                                            sourcing_data.append({
                                                'country': sourcing_country.name,
                                                'value': 0,
                                                'vendors': 1,
                                                'ecommerce_stores': 1 if 419 in partner_tags.ids else 0,
                                                'ecommerce_value': 0,
                                            })
                                        else:
                                            for data in sourcing_data:
                                                vendor_country = sourcing_country.name
                                                if data['country'] == vendor_country:
                                                    data['vendors'] += 1
                                                    data['ecommerce_stores'] += 1 if 419 in partner_tags.ids else 0
                                                    break

                                        if 422 in partner_tags.ids:
                                            ecia_vendors.append({
                                                'name': history_id.x_partner_id.name,
                                                'country': sourcing_country.name,
                                            })

                                    for data in sourcing_data:
                                        if data['country'] == sourcing_country.name:
                                            data['value'] += line_price
                                            data['ecommerce_value'] += line_price if 419 in partner_tags.ids else 0
                                            break

                                    if 419 in partner_tags.ids:
                                        total['ecommerce_stores'] += line_price
                                    else:
                                        total['conventional_stores'] += line_price

                                if not rec.x_show_hidden_countries and coo.id in rec.x_hidden_country_ids.ids:
                                    coo_name = 'Other'
                                else:
                                    coo_name = coo.name + ' (' + coo.code + ')' if coo else 'Other'

                                if coo_name not in coo_countries:
                                    coo_countries.append(coo_name)
                                    coo_data.append({
                                        'country': coo_name,
                                        'product_type': [product_type.x_label],
                                        'line_count': 0,
                                        'value': line_price,
                                    })
                                else:
                                    for data in coo_data:
                                        if data['country'] == coo_name:
                                            data['value'] += line_price
                                            if product_type.x_label not in data['product_type']:
                                                data['product_type'].append(product_type.x_label)
                                            break

                                data_list['cnf_value'] += line_price

                                desc = line.product_id.dk_product_description

                                part_detail = next((part for part in data_list['parts_detail']
                                                    if part['name'] == line.product_id.name), None)

                                if part_detail:
                                    part_detail['cnf'] += line_price

                                    for part_by_hs_code in parts_by_hs_code:
                                        for part in part_by_hs_code['parts']:
                                            if part['name'] == line.product_id.name:
                                                part['qty'] += line_quantity
                                                part['cnf'] += line_price
                                                break
                                else:
                                    total['line_count'] += 1
                                    data_list['line_count'] += 1

                                    for data in coo_data:
                                        if data['country'] == coo_name:
                                            data['line_count'] += 1
                                            break

                                    data_list['parts_detail'].append({
                                        'name': line.product_id.name,
                                        'coo': coo.code if coo_name != 'Other' else 'OT',
                                        'country': coo.name,
                                        'cnf': line_price,
                                    })

                                    if htsus_code not in total_us_codes and htsus_code:
                                        total_us_codes.append(htsus_code)
                                    if pk_hs_code not in total_pk_codes and pk_hs_code:
                                        total_pk_codes.append(pk_hs_code)
                                    if tr_hs_code not in total_tr_codes and tr_hs_code:
                                        total_tr_codes.append(tr_hs_code)

                                    if htsus_code and pk_hs_code and tr_hs_code:
                                        group = htsus_code.x_htsus_code_id.x_hs_code + \
                                                pk_hs_code.x_hs_code + tr_hs_code.x_hs_code
                                        if group not in hs_code_group:
                                            hs_code_group.append(group)
                                            parts_by_hs_code.append({
                                                'parts': [{
                                                    'coo': coo.code if coo_name != 'Other' else 'OT',
                                                    'name': line.product_id.name,
                                                    'category': product_type.x_name if product_type else 'Undefined',
                                                    'sub_category': product_sub_type.x_name if product_sub_type else 'Undefined',
                                                    'desc': desc if desc else line.product_id.description,
                                                    'qty': line_quantity,
                                                    'cnf': line_price,
                                                }],
                                                'us_hs_code': {
                                                    'code': htsus_code.x_htsus_code_id.x_hs_code,
                                                    'desc_0': htsus_code.x_chapter_description,
                                                    'desc_1': htsus_code.x_heading_description,
                                                    'desc_2': htsus_code.x_level_1_description,
                                                    'desc_3': htsus_code.x_level_2_description,
                                                    'desc_4': htsus_code.x_level_3_description,
                                                    'desc_5': htsus_code.x_level_4_description,
                                                    'desc_6': htsus_code.x_level_5_description,
                                                    'desc_7': htsus_code.x_level_6_description,
                                                    'desc_8': htsus_code.x_hs_code_description,
                                                },
                                                'pk_hs_code': {
                                                    'code': pk_hs_code.x_hs_code,
                                                    'desc_0': pk_hs_code.x_chapter_description,
                                                    'desc_1': pk_hs_code.x_heading_description,
                                                    'desc_2': pk_hs_code.x_level_1_description,
                                                    'desc_3': pk_hs_code.x_level_2_description,
                                                    'desc_4': pk_hs_code.x_level_3_description,
                                                    'desc_5': pk_hs_code.x_level_4_description,
                                                    'desc_6': pk_hs_code.x_level_5_description,
                                                    'desc_7': pk_hs_code.x_level_6_description,
                                                    'desc_8': pk_hs_code.x_hs_code_description,
                                                },
                                                'tr_hs_code': {
                                                    'code': tr_hs_code.x_hs_code,
                                                    'desc_0': tr_hs_code.x_chapter_description,
                                                    'desc_1': tr_hs_code.x_heading_description,
                                                    'desc_2': tr_hs_code.x_level_1_description,
                                                    'desc_3': tr_hs_code.x_level_2_description,
                                                    'desc_4': tr_hs_code.x_level_3_description,
                                                    'desc_5': tr_hs_code.x_level_4_description,
                                                    'desc_6': tr_hs_code.x_level_5_description,
                                                    'desc_7': tr_hs_code.x_level_6_description,
                                                    'desc_8': tr_hs_code.x_hs_code_description,
                                                },
                                                'group_cnf': line_price,
                                                'htsus_code': htsus_code.x_htsus_code_id.x_hs_code,
                                            })
                                        else:
                                            for part in parts_by_hs_code:
                                                if part['us_hs_code']['code'] == htsus_code.x_htsus_code_id.x_hs_code \
                                                        and part['pk_hs_code']['code'] == pk_hs_code.x_hs_code \
                                                        and part['tr_hs_code']['code'] == tr_hs_code.x_hs_code:
                                                    part['parts'].append({
                                                        'coo': coo.code if coo_name != 'Other' else 'OT',
                                                        'name': line.product_id.name,
                                                        'category': product_type.x_name if product_type else 'Undefined',
                                                        'sub_category': product_sub_type.x_name if product_sub_type else 'Undefined',
                                                        'desc': desc if desc else line.product_id.description,
                                                        'qty': line_quantity,
                                                        'cnf': line_price,
                                                    })
                                                    part['group_cnf'] += line_price
                                                    break
                                    else:
                                        for part in parts_by_hs_code:
                                            if part['us_hs_code']['code'] == 'Undefined':
                                                part['parts'].append({
                                                    'coo': coo.code if coo_name != 'Other' else 'OT',
                                                    'name': line.product_id.name,
                                                    'category': product_type.x_name if product_type else 'Undefined',
                                                    'sub_category': product_sub_type.x_name if product_sub_type else 'Undefined',
                                                    'desc': desc if desc else line.product_id.description,
                                                    'qty': line_quantity,
                                                    'cnf': line_price,
                                                })
                                                part['group_cnf'] += line_price
                                                break

                                if product_type:
                                    if product_type.x_name not in data_list['category_list']:
                                        data_list['category_list'].append(product_type.x_name)
                                if line.product_id.dk_sub_category:
                                    if line.product_id.dk_sub_category.x_name not in data_list['sub_category_list']:
                                        data_list['sub_category_list'].append(line.product_id.dk_sub_category.x_name)
                                if htsus_code:
                                    if htsus_code.x_htsus_code_id.x_hs_code not in data_list['htsus_code_list']:
                                        data_list['htsus_code_list'].append(htsus_code.x_htsus_code_id.x_hs_code)

                                total['cnf_value'] += line_price
                                total['part_count'] += line_quantity
                                total['imported_parts'] += line_price if line.product_id.categ_id.id == 269 else 0
                                total['local_parts'] += line_price if line.product_id.categ_id.id == 271 else 0

            total['us_codes'] = len(total_us_codes)
            total['pk_codes'] = len(total_pk_codes)
            total['tr_codes'] = len(total_tr_codes)

            sourcing_data = sorted(sourcing_data, key=lambda d: d['value'], reverse=True)
            coo_data = sorted(coo_data, key=lambda d: d['value'], reverse=True)
            # hs_code_mapping = sorted(hs_code_mapping, key=lambda d: d['us_hs_code'], reverse=True)
            parts_by_hs_code = sorted(parts_by_hs_code, key=lambda d: d['htsus_code'], reverse=True)

            sr_no = 1
            for part_by_hs_code in parts_by_hs_code:
                part_by_hs_code['parts'] = \
                    sorted(part_by_hs_code['parts'], key=lambda d: d['sub_category'], reverse=True)
                for part in part_by_hs_code['parts']:
                    part['sr_no'] = sr_no
                    sr_no += 1

            if total['cnf_value'] != 0:
                total['imported_parts'] = total['imported_parts'] / total['cnf_value'] * 100
                total['local_parts'] = total['local_parts'] / total['cnf_value'] * 100
                total['ecommerce_stores'] = total['ecommerce_stores'] / total['cnf_value'] * 100
                total['conventional_stores'] = total['conventional_stores'] / total['cnf_value'] * 100

            taxes = ['AV', 'CD', 'ACD', 'RD', 'ST', 'AST', 'IT', 'CESS']
            for data_list in hs_codes_data:
                for data in data_list['country_data']:

                    cnf = 0
                    for part in data_list['parts_detail']:
                        add_part = False

                        part_id = self.env['product.template'].search([('name', '=', part['name'])])
                        if part_id.categ_id.id != 269:
                            add_part = False
                        elif data['country'] == 'Turkey' and part_id.x_hs_code_tr_id.x_hs_code == data['hs_code']:
                            add_part = True
                        elif data['country'] == 'Pakistan' and part_id.dk_hs_code.x_hs_code == data['hs_code']:
                            add_part = True
                        elif data['country'] not in ['Turkey', 'Pakistan']:
                            add_part = True

                        if add_part:
                            for country in data['zone'].x_country_ids:
                                if part['country'] == country.name:
                                    cnf += part['cnf']
                                    if part['coo'] not in data['coos']:
                                        data['coos'] += part['coo'] + ','
                                    break

                    av = cnf * data['assessed_value_p'] / 100

                    tax_amounts = [av, 0, 0, 0, 0, 0, 0, 0]

                    if data['flat_cd'] == 0:
                        amount = 0
                        formula = data['cd_formula']
                        if formula:
                            for t in range(7):
                                amount += tax_amounts[t] if taxes[t] in formula else 0
                            tax_amounts[1] = amount * data['custom_duty'] / 100
                    else:
                        tax_amounts[1] = data['flat_cd']

                    amount = 0
                    formula = data['acd_formula']
                    if formula:
                        for t in range(7):
                            amount += tax_amounts[t] if taxes[t] in formula else 0
                        tax_amounts[2] = amount * data['additional_custom_duty'] / 100

                    if data['country'] == 'India':
                        amount = 0
                        formula = data['st_formula']
                        if formula:
                            for t in range(7):
                                amount += tax_amounts[t] if taxes[t] in formula else 0
                            tax_amounts[4] = amount * data['sale_tax'] / 100

                    amount = 0
                    formula = data['rd_formula']
                    if formula:
                        for t in range(7):
                            amount += tax_amounts[t] if taxes[t] in formula else 0
                        tax_amounts[3] = amount * data['regulatory_duty'] / 100

                    if data['country'] != 'India':
                        amount = 0
                        formula = data['st_formula']
                        if formula:
                            for t in range(7):
                                amount += tax_amounts[t] if taxes[t] in formula else 0
                            tax_amounts[4] = amount * data['sale_tax'] / 100

                    amount = 0
                    formula = data['ast_formula']
                    if formula:
                        for t in range(7):
                            amount += tax_amounts[t] if taxes[t] in formula else 0
                        tax_amounts[5] = amount * data['additional_sale_tax'] / 100

                    amount = 0
                    formula = data['it_formula']
                    if formula:
                        for t in range(7):
                            amount += tax_amounts[t] if taxes[t] in formula else 0
                        tax_amounts[6] = amount * data['income_tax'] / 100

                    amount = 0
                    formula = data['cess_formula']
                    if formula:
                        for t in range(7):
                            amount += tax_amounts[t] if taxes[t] in formula else 0
                        tax_amounts[7] = amount * data['cess'] / 100

                    cd = tax_amounts[1]
                    acd = tax_amounts[2]
                    rd = tax_amounts[3]
                    st = tax_amounts[4]
                    ast = tax_amounts[5]
                    it = tax_amounts[6]
                    cess = tax_amounts[7]

                    data['assessed_value'] = av
                    data['cd_value'] = cd
                    data['acd_value'] = acd
                    data['rd_value'] = rd
                    data['st_value'] = st
                    data['ast_value'] = ast
                    data['it_value'] = it
                    data['cess_value'] = cess

                    data['total_tax'] = cd + acd + rd + st + ast + it + cess
                    data['total_cost'] = av + cd + acd + rd + st + ast + it + cess

                    index = next((country_data.index(c) for c in country_data if c['label'] == data['label']), None)
                    country_data[index]['assessed_value'] += av
                    country_data[index]['duties_cost'] += cd + acd + rd + cess
                    country_data[index]['vat_cost'] += st + ast
                    country_data[index]['it_cost'] += it

                    country_data[index]['cd_total'] += cd
                    country_data[index]['acd_total'] += acd
                    country_data[index]['rd_total'] += rd
                    country_data[index]['st_total'] += st
                    country_data[index]['ast_total'] += ast
                    country_data[index]['it_total'] += it
                    country_data[index]['cess_total'] += cess
                    country_data[index]['tax_total'] += cd + acd + rd + st + ast + it + cess

                for data in data_list['country_data']:
                    if data['label'] == default_scenario_id.x_label:
                        data_list['default_total_tax'] = data['total_tax']

            for data_list in country_data:
                data_list['total_cost'] = total['cnf_value'] + data_list['tax_total']

            vals = {
                'hs_code': 'UNDEFINED',
                # Taxes
                'country_data': [],
                'default_total_tax': 0,
                # Parts Detail
                'part_type': 'Imported',
                'line_count': 0,
                'cnf_value': 0,
                'parts_detail': [],
                'category_list': [],
                'sub_category_list': [],
                'htsus_code_list': [],
            }
            if vals in hs_codes_data:
                hs_codes_data.remove(vals)

            vals = {
                'parts': [],
                'us_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'pk_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'tr_hs_code': {
                    'code': 'Undefined',
                    'desc_0': '',
                    'desc_1': '',
                    'desc_2': '',
                    'desc_3': '',
                    'desc_4': '',
                    'desc_5': '',
                    'desc_6': '',
                    'desc_7': '',
                    'desc_8': '',
                },
                'group_cnf': 0,
                'htsus_code': 'Undefined',
            }
            if vals in parts_by_hs_code:
                parts_by_hs_code.remove(vals)

            hs_codes_data = sorted(hs_codes_data, key=lambda d: d['default_total_tax'], reverse=True)

            # Currency Depreciation Effect
            e_date = rec.x_end_date if rec.x_end_date else datetime.now().date()
            e_date = date(e_date.year, e_date.month + 1, 1) if e_date.month != 12 else date(e_date.year + 1, 1, 1)
            date_by_months = [e_date - relativedelta(months=month) for month in range(13)]

            currency_rates = self.env['res.currency.rate'].search([
                ('currency_id', '=', 165), ('name', '>=', e_date - relativedelta(years=1, days=1))])
            currency_rates = zip(currency_rates.mapped('name'), currency_rates.mapped('rate'))

            loss_by_month = [[0, 0] for x in range(12)]
            for currency_rate in currency_rates:
                for x in range(12):
                    if date_by_months[x] > currency_rate[0] >= date_by_months[x + 1]:
                        loss_by_month[11 - x][0] += currency_rate[1]
                        loss_by_month[11 - x][1] += 1
                        if len(loss_by_month[11 - x]) != 3:
                            loss_by_month[11 - x].append(currency_rate[0].strftime("%b") + '-' +
                                                         currency_rate[0].strftime("%y"))

            pkr_reserved = 0
            for rate in loss_by_month:
                pkr_rate = rate[0] / rate[1] if rate[1] != 0 else 0
                if pkr_reserved == 0:
                    pkr_reserved = total['cnf_value'] * total['imported_parts'] / 100 * pkr_rate
                usd_available = pkr_reserved / pkr_rate if pkr_rate != 0 else 0
                usd_delta = total['cnf_value'] * total['imported_parts'] / 100 - usd_available

                rate[0] = pkr_rate
                rate.append(usd_available)
                rate.append(usd_delta)
                rate[1] = round(usd_delta / total['cnf_value'] * 100, 2) if total['cnf_value'] != 0 else 0

            return {
                'default_scenario_id': default_scenario_id,
                'total': total,
                'country_data': country_data,
                'coo_data': coo_data,
                'ecia_vendors': ecia_vendors,
                'hs_codes_data': hs_codes_data,
                'sourcing_data': sourcing_data,
                'total_vendors': len(vendors),
                'loss_by_month': loss_by_month,
                'hs_code_mapping': hs_code_mapping,
                'parts_by_hs_code': parts_by_hs_code,
            }

    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        for rec in self:
            for line in rec.bom_line_ids:
                domain = [('x_alternate_id', 'in', line.product_id.x_taraz_part_number_id.x_alternate_ids.ids)]
                product_ids = self.env['component.usage'].search(domain).mapped('x_product_id')
                if rec.product_tmpl_id.id not in product_ids.ids:
                    for alternate in line.product_id.x_taraz_part_number_id.x_alternate_ids:
                        alternate.x_product_usage_ids = [(0, 0, {'x_product_id': rec.product_tmpl_id.id})]
                    for compromised in line.product_id.x_taraz_part_number_id.x_compromised_ids:
                        compromised.x_product_usage_ids = [(0, 0, {'x_product_id': rec.product_tmpl_id.id})]
        return res
