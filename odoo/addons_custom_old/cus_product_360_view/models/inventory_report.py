from odoo import api, fields, models
from odoo.exceptions import UserError

import math

from dateutil import relativedelta


class InventorySaleReport(models.Model):
    _name = 'inventory.sale.report'
    _description = 'Inventory Sale Report'
    _rec_name = 'x_name'

    x_name = fields.Char(string='Name', default='Inventory Sale Report')
    x_compute_report_lines = fields.Boolean(string='Compute Report Lines', compute='update_report_lines', store=True)
    x_letter_head_report = fields.Boolean(string='Letter Head Report?', required=False)

    x_date_from = fields.Datetime(string='Date From', required=True)
    x_date_to = fields.Datetime(string='Date From', required=True)
    x_apply_date_range = fields.Boolean(string='Apply Date Range', required=False)
    x_order_ids = fields.Many2many(comodel_name='sale.order', string='Sale Orders')
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True, default=2)
    x_rounding = fields.Boolean(string='Rounding', required=False)
    x_rounding_number = fields.Integer(string='Rounding Number', required=False)
    x_months = fields.Integer(string='Months', required=False)
    x_excluded_product_ids = fields.Many2many(comodel_name='product.product', string='Excluded Products',
                                              domain="[('categ_id.name', 'ilike', 'Finished')]")

    x_sale_group_by = fields.Selection(selection=[
        ('hs_code', 'HS Code'),
        ('series', 'Series'),
    ], required=False, string='Group By', )
    x_sale_table_text = fields.Html(string='Text at Table End', required=False)
    x_sale_line_ids = fields.One2many(comodel_name='report.sale.lines', inverse_name='x_report_id',
                                      string='Sale Lines', required=False)
    x_manual_sale_line_ids = fields.One2many(comodel_name='manual.report.sale.lines', inverse_name='x_report_id',
                                             string='Sale Lines', required=False)

    x_manufacturing_group_by = fields.Selection(selection=[
        ('hs_code', 'HS Code'),
        ('series', 'Series'),
    ], required=False, string='Group By', )
    x_manufacturing_table_text = fields.Html(string='Text at Table End', required=False)
    x_workmanship = fields.Boolean(string='Workmanship', required=False)
    x_persons = fields.Integer(string='# of Person', required=False)
    x_salary = fields.Monetary(string='Salary', required=False)
    x_electricity = fields.Boolean(string='Electricity', required=False)
    x_units = fields.Integer(string='Units', required=False)
    x_rate = fields.Monetary(string='Rate', required=False)
    x_rent = fields.Boolean(string='Rent', required=False)
    x_rent_amount = fields.Monetary(string='Rent Amount', required=False)
    x_manufacturing_line_ids = fields.One2many(comodel_name='report.manufacturing.lines', inverse_name='x_report_id',
                                               string='Manufacturing Lines', required=False)

    x_raw_material_group_by = fields.Selection(selection=[
        ('hs_code', 'HS Code'),
        ('sub_type', 'Sub-Type'),
    ], required=True, string='Group By', default='hs_code', )
    x_raw_material_show_by = fields.Selection(selection=[
        ('part', 'Part Number'),
        ('sub_type', 'Sub-Type'),
        ('type', 'Type'),
    ], required=True, string='Show in 1st Column', default='type', )
    x_raw_material_table_text = fields.Html(string='Text at Table End', required=False)
    x_raw_material_line_ids = fields.One2many(comodel_name='report.raw.material.lines', inverse_name='x_report_id',
                                              string='Raw Material Lines', required=False)

    x_production_process = fields.Html(string='Production Process', required=False)
    x_smt_assembly = fields.Binary(string="SMT Assembly", store=True, )
    x_making_process = fields.Binary(string="Making Process", store=True, )
    x_final_assembly = fields.Binary(string="Final Assembly", store=True, )

    x_portfolio_products_ids = fields.One2many(comodel_name='portfolio.products', inverse_name='x_report_id',
                                               string='Portfolio Products', required=False)

    @api.depends('x_apply_date_range', 'x_date_from', 'x_date_to', 'x_rounding', 'x_rounding_number',
                 'x_excluded_product_ids', 'x_manual_sale_line_ids', 'x_workmanship', 'x_persons', 'x_salary',
                 'x_electricity', 'x_units', 'x_rate', 'x_rent', 'x_rent_amount')
    def update_report_lines(self):
        for rec in self:
            order_ids = self.env['sale.order'].search([('date_order', '>=', rec.x_date_from),
                                                       ('date_order', '<=', rec.x_date_to),
                                                       ('x_tracking_reference', '!=', '')])

            rec.x_order_ids = order_ids.ids
            order_line_ids = order_ids.mapped('x_cgs_line_ids')

            rec.x_sale_line_ids = [(5, 0)]
            for line in order_line_ids.filtered(
                    lambda l: 'Finished' in l.x_product_id.categ_id.name and 'BOS-' not in l.x_product_id.name):
                if line.x_type == 'price':
                    line_id = rec.x_sale_line_ids.filtered(lambda l: l.x_product_id.id == line.x_product_id.id)
                    if line_id:
                        line_id.x_export_qty += line.x_quantity
                        line_id.x_export_value += line.x_price_subtotal
                    elif line.x_product_id.id not in rec.x_excluded_product_ids.ids:
                        rec.x_sale_line_ids = [(0, 0, {
                            'x_product_id': line.x_product_id.id,
                            'x_export_qty': line.x_quantity,
                            'x_export_value': line.x_price_subtotal,
                        })]

            rec.x_manufacturing_line_ids = [(5, 0)]
            sale_line_ids = rec.x_sale_line_ids if rec.x_apply_date_range else rec.x_manual_sale_line_ids
            for line in sale_line_ids:
                if not line.x_product_id.x_hide_in_report:
                    rec.x_manufacturing_line_ids = [(0, 0, {
                        'x_product_id': line.x_product_id.id,
                        'x_export_qty': line.x_export_qty,
                    })]

            if rec.x_rounding and rec.x_apply_date_range:
                for line in rec.x_sale_line_ids:
                    line_qty = math.ceil(line.x_export_qty / rec.x_rounding_number) * rec.x_rounding_number
                    line_value = (line.x_export_value / line.x_export_qty) * line_qty
                    line.x_export_qty = line_qty
                    line.x_export_value = line_value
                for line in rec.x_manufacturing_line_ids:
                    line_qty = math.ceil(line.x_export_qty / rec.x_rounding_number) * rec.x_rounding_number
                    line.x_export_qty = line_qty

            rec.x_raw_material_line_ids = [(5, 0)]
            for line in rec.x_manufacturing_line_ids:
                export_value = 0
                domain = [('product_tmpl_id', '=', line.x_product_id.product_tmpl_id.id)]
                bom_id_0 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')

                for line_0 in bom_id_0.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                    quantity_0 = line_0.product_qty / bom_id_0.product_qty * line.x_export_qty
                    value = quantity_0 * line_0.x_unit_cost
                    export_value += value
                    line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_0.product_id.id)
                    if 'Local' in line_0.product_id.categ_id.name:
                        if line_id:
                            line_id.x_local_qty += quantity_0
                            line_id.x_local_value += value
                        else:
                            rec.x_raw_material_line_ids = [(0, 0, {
                                'x_product_id': line_0.product_id.id,
                                'x_local_qty': quantity_0,
                                'x_local_value': value,
                            })]
                    elif 'Imported' in line_0.product_id.categ_id.name:
                        if line_id:
                            line_id.x_export_qty += quantity_0
                            line_id.x_export_value += value
                        else:
                            rec.x_raw_material_line_ids = [(0, 0, {
                                'x_product_id': line_0.product_id.id,
                                'x_export_qty': quantity_0,
                                'x_export_value': value,
                            })]

                for line_0 in bom_id_0.bom_line_ids.filtered(lambda l: 'Finished' in l.product_id.categ_id.name):
                    quantity_0 = line_0.product_qty / bom_id_0.product_qty * line.x_export_qty
                    domain = [('product_tmpl_id', '=', line_0.product_id.product_tmpl_id.id)]
                    bom_id_1 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')
                    for line_1 in bom_id_1.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                        quantity_1 = line_1.product_qty / bom_id_1.product_qty * quantity_0
                        value = quantity_1 * line_1.x_unit_cost
                        export_value += value
                        line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_1.product_id.id)
                        if 'Local' in line_1.product_id.categ_id.name:
                            if line_id:
                                line_id.x_local_qty += quantity_1
                                line_id.x_local_value += value
                            else:
                                rec.x_raw_material_line_ids = [(0, 0, {
                                    'x_product_id': line_1.product_id.id,
                                    'x_local_qty': quantity_1,
                                    'x_local_value': value,
                                })]
                        elif 'Imported' in line_1.product_id.categ_id.name:
                            if line_id:
                                line_id.x_export_qty += quantity_1
                                line_id.x_export_value += value
                            else:
                                rec.x_raw_material_line_ids = [(0, 0, {
                                    'x_product_id': line_1.product_id.id,
                                    'x_export_qty': quantity_1,
                                    'x_export_value': value,
                                })]

                    for line_1 in bom_id_1.bom_line_ids.filtered(lambda l: 'Finished' in l.product_id.categ_id.name):
                        quantity_1 = line_1.product_qty / bom_id_1.product_qty * quantity_0
                        domain = [('product_tmpl_id', '=', line_1.product_id.product_tmpl_id.id)]
                        bom_id_2 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')
                        for line_2 in bom_id_2.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                            quantity_2 = line_2.product_qty / bom_id_2.product_qty * quantity_1
                            value = quantity_2 * line_2.x_unit_cost
                            export_value += value
                            line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_2.product_id.id)
                            if 'Local' in line_2.product_id.categ_id.name:
                                if line_id:
                                    line_id.x_local_qty += quantity_2
                                    line_id.x_local_value += value
                                else:
                                    rec.x_raw_material_line_ids = [(0, 0, {
                                        'x_product_id': line_2.product_id.id,
                                        'x_local_qty': quantity_2,
                                        'x_local_value': value,
                                    })]
                            elif 'Imported' in line_2.product_id.categ_id.name:
                                if line_id:
                                    line_id.x_export_qty += quantity_2
                                    line_id.x_export_value += value
                                else:
                                    rec.x_raw_material_line_ids = [(0, 0, {
                                        'x_product_id': line_2.product_id.id,
                                        'x_export_qty': quantity_2,
                                        'x_export_value': value,
                                    })]

                        for line_2 in bom_id_2.bom_line_ids.filtered(lambda l: 'Finished' in l.product_id.categ_id.name):
                            quantity_2 = line_2.product_qty / bom_id_2.product_qty * quantity_1
                            domain = [('product_tmpl_id', '=', line_2.product_id.product_tmpl_id.id)]
                            bom_id_3 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')
                            for line_3 in bom_id_3.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                                quantity_3 = line_3.product_qty / bom_id_3.product_qty * quantity_2
                                value = quantity_3 * line_3.x_unit_cost
                                export_value += value
                                line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_3.product_id.id)
                                if 'Local' in line_3.product_id.categ_id.name:
                                    if line_id:
                                        line_id.x_local_qty += quantity_3
                                        line_id.x_local_value += value
                                    else:
                                        rec.x_raw_material_line_ids = [(0, 0, {
                                            'x_product_id': line_3.product_id.id,
                                            'x_local_qty': quantity_3,
                                            'x_local_value': value,
                                        })]
                                elif 'Imported' in line_3.product_id.categ_id.name:
                                    if line_id:
                                        line_id.x_export_qty += quantity_3
                                        line_id.x_export_value += value
                                    else:
                                        rec.x_raw_material_line_ids = [(0, 0, {
                                            'x_product_id': line_3.product_id.id,
                                            'x_export_qty': quantity_3,
                                            'x_export_value': value,
                                        })]

                            for line_3 in bom_id_3.bom_line_ids.filtered(lambda l: 'Finished' in l.product_id.categ_id.name):
                                quantity_3 = line_3.product_qty / bom_id_3.product_qty * quantity_2
                                domain = [('product_tmpl_id', '=', line_3.product_id.product_tmpl_id.id)]
                                bom_id_4 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')
                                for line_4 in bom_id_4.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                                    quantity_4 = line_4.product_qty / bom_id_4.product_qty * quantity_3
                                    value = quantity_4 * line_4.x_unit_cost
                                    export_value += value
                                    line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_4.product_id.id)
                                    if 'Local' in line_4.product_id.categ_id.name:
                                        if line_id:
                                            line_id.x_local_qty += quantity_4
                                            line_id.x_local_value += value
                                        else:
                                            rec.x_raw_material_line_ids = [(0, 0, {
                                                'x_product_id': line_4.product_id.id,
                                                'x_local_qty': quantity_4,
                                                'x_local_value': value,
                                            })]
                                    elif 'Imported' in line_4.product_id.categ_id.name:
                                        if line_id:
                                            line_id.x_export_qty += quantity_4
                                            line_id.x_export_value += value
                                        else:
                                            rec.x_raw_material_line_ids = [(0, 0, {
                                                'x_product_id': line_4.product_id.id,
                                                'x_export_qty': quantity_4,
                                                'x_export_value': value,
                                            })]

                                for line_4 in bom_id_4.bom_line_ids.filtered(lambda l: 'Finished' in l.product_id.categ_id.name):
                                    quantity_4 = line_4.product_qty / bom_id_4.product_qty * quantity_3
                                    domain = [('product_tmpl_id', '=', line_4.product_id.product_tmpl_id.id)]
                                    bom_id_5 = self.env['mrp.bom'].search(domain, limit=1, order='id desc')
                                    for line_5 in bom_id_5.bom_line_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name):
                                        quantity_5 = line_5.product_qty / bom_id_5.product_qty * quantity_4
                                        value = quantity_5 * line_5.x_unit_cost
                                        export_value += value
                                        line_id = rec.x_raw_material_line_ids.filtered(lambda l: l.x_product_id.id == line_5.product_id.id)
                                        if 'Local' in line_5.product_id.categ_id.name:
                                            if line_id:
                                                line_id.x_local_qty += quantity_5
                                                line_id.x_local_value += value
                                            else:
                                                rec.x_raw_material_line_ids = [(0, 0, {
                                                    'x_product_id': line_5.product_id.id,
                                                    'x_local_qty': quantity_5,
                                                    'x_local_value': value,
                                                })]
                                        elif 'Imported' in line_5.product_id.categ_id.name:
                                            if line_id:
                                                line_id.x_export_qty += quantity_5
                                                line_id.x_export_value += value
                                            else:
                                                rec.x_raw_material_line_ids = [(0, 0, {
                                                    'x_product_id': line_5.product_id.id,
                                                    'x_export_qty': quantity_5,
                                                    'x_export_value': value,
                                                })]

                line.x_export_value = export_value

            date_delta = relativedelta.relativedelta(rec.x_date_to, rec.x_date_from)
            months = date_delta.months + 1

            rec.x_months = months

            workmanship = rec.x_persons * rec.x_salary * months if rec.x_workmanship else 0
            electricity = rec.x_units * rec.x_rate * months if rec.x_electricity else 0
            rent = rec.x_rent_amount * months if rec.x_rent else 0

            fix_expenses = workmanship + electricity + rent
            total_cgs = sum(rec.x_manufacturing_line_ids.mapped('x_export_value'))
            for line in rec.x_manufacturing_line_ids:
                line.x_export_value += line.x_export_value / total_cgs * fix_expenses if total_cgs != 0 else 0

    def report_data(self):
        for rec in self:
            sale_line_ids = rec.x_sale_line_ids if rec.x_apply_date_range else rec.x_manual_sale_line_ids

            sales_data = []
            for line in sale_line_ids:
                vals = {
                    'column_1': line.x_product_id.name,
                    'column_2': line.x_product_id.x_short_description,
                    'column_3': line.x_hs_code_id.x_hs_code,
                    'column_4': line.x_local_qty,
                    'column_5': line.x_local_value,
                    'column_6': line.x_export_qty,
                    'column_7': line.x_export_value,
                }
                if rec.x_sale_group_by == 'hs_code' and not line.x_product_id.x_hide_in_report:
                    sales_data.append(vals)
                elif rec.x_sale_group_by == 'series' and not line.x_product_id.x_hide_in_report:
                    sales_data.append(vals)
                elif not line.x_product_id.x_hide_in_report:
                    sales_data.append(vals)

            sales_data = sorted(sales_data, key=lambda d: d['column_7'], reverse=True)

            manufacturing_data = []
            for line in rec.x_manufacturing_line_ids:
                vals = {
                    'column_1': line.x_product_id.name,
                    'column_2': line.x_product_id.x_short_description,
                    'column_3': line.x_hs_code_id.x_hs_code,
                    'column_4': line.x_export_qty,
                    'column_5': line.x_export_value,
                }
                if rec.x_sale_group_by == 'hs_code' and not line.x_product_id.x_hide_in_report:
                    manufacturing_data.append(vals)
                elif rec.x_sale_group_by == 'series' and not line.x_product_id.x_hide_in_report:
                    manufacturing_data.append(vals)
                elif not line.x_product_id.x_hide_in_report:
                    manufacturing_data.append(vals)

            manufacturing_data = sorted(manufacturing_data, key=lambda d: d['column_5'], reverse=True)

            raw_material_data = []
            for line in rec.x_raw_material_line_ids:
                product = line.x_product_id.name
                type = line.x_product_id.dk_category.x_name if line.x_product_id.dk_category else 'Undefined'
                sub_type = line.x_sub_type_id.x_name if line.x_sub_type_id else 'Undefined'
                hs_code = line.x_hs_code_id.x_hs_code if line.x_hs_code_id else 'Undefined'
                vals = {
                    'column_1': product,
                    'column_2': sub_type,
                    'column_3': hs_code,
                    'column_4': line.x_local_qty,
                    'column_5': line.x_local_value,
                    'column_6': line.x_export_qty,
                    'column_7': line.x_export_value,
                    'column_8': type,
                }
                if rec.x_raw_material_group_by == 'hs_code':
                    val = next((item for item in raw_material_data if item['column_3'] == hs_code), None)
                    if val:
                        val['column_1'] += ', ' + product if product not in val['column_1'] else ''
                        val['column_2'] += ', ' + sub_type if sub_type not in val['column_2'] else ''
                        val['column_4'] += line.x_local_qty
                        val['column_5'] += line.x_local_value
                        val['column_6'] += line.x_export_qty
                        val['column_7'] += line.x_export_value
                        val['column_8'] += ', ' + type if type not in val['column_8'] else ''
                    else:
                        raw_material_data.append(vals)
                elif rec.x_raw_material_group_by == 'sub_type':
                    val = next((item for item in raw_material_data if item['column_2'] == sub_type), None)
                    if val:
                        val['column_1'] += ', ' + product if product not in val['column_1'] else ''
                        val['column_3'] += ', ' + hs_code if hs_code not in val['column_3'] else ''
                        val['column_4'] += line.x_local_qty
                        val['column_5'] += line.x_local_value
                        val['column_6'] += line.x_export_qty
                        val['column_7'] += line.x_export_value
                        val['column_8'] += ', ' + type if type not in val['column_8'] else ''
                    else:
                        raw_material_data.append(vals)

            raw_material_data = sorted(raw_material_data, key=lambda d: d['column_7'], reverse=True)

            return {
                'sales_data': sales_data,
                'manufacturing_data': manufacturing_data,
                'raw_material_data': raw_material_data,
            }

    def unlink(self):
        for rec in self:
            rec.x_sale_line_ids.unlink()
            rec.x_manufacturing_line_ids.unlink()
            rec.x_raw_material_line_ids.unlink()
        return super(InventorySaleReport, self).unlink()


class ManualReportSaleLines(models.Model):
    _name = 'manual.report.sale.lines'
    _description = 'Manual Report Sale Lines'
    _rec_name = 'x_product_id'
    _order = 'x_export_value desc'

    x_report_id = fields.Many2one(comodel_name='inventory.sale.report', string='Report', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related='x_report_id.x_currency_id')

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False,
                                   domain="[('categ_id.name', 'ilike', 'Finished')]")
    x_hide_in_report = fields.Boolean(string='Exclude', store=True, readonly=False,
                                      related='x_product_id.x_hide_in_report')
    x_product_series_id = fields.Many2one(comodel_name='product.series', string='Product Series', store=True,
                                          readonly=False, related='x_product_id.x_product_series')
    x_hs_code_id = fields.Many2one(comodel_name='hs.code.database', string='HS Code', store=True, readonly=False,
                                   related='x_product_id.x_hs_code_tr_id')

    x_local_qty = fields.Integer(string='Turkey Qty', required=False)
    x_local_value = fields.Monetary(string='Turkey Value', required=False)

    x_export_qty = fields.Integer(string='Abroad Qty', required=False)
    x_export_value = fields.Monetary(string='Abroad Value', required=False)

    @api.onchange('x_local_qty')
    def update_local_value(self):
        for rec in self:
            rec.x_local_value = rec.x_product_id.lst_price * rec.x_local_qty

    @api.onchange('x_export_qty')
    def update_local_value(self):
        for rec in self:
            rec.x_export_value = rec.x_product_id.lst_price * rec.x_export_qty


class ReportSaleLines(models.Model):
    _name = 'report.sale.lines'
    _description = "Report Sale Lines"
    _rec_name = 'x_product_id'
    _order = 'x_export_value desc'

    x_report_id = fields.Many2one(comodel_name='inventory.sale.report', string='Report', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related='x_report_id.x_currency_id')

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False,
                                   domain="[('categ_id.name', 'ilike', 'Finished')]")
    x_hide_in_report = fields.Boolean(string='Exclude', store=True, readonly=False,
                                      related='x_product_id.x_hide_in_report')
    x_product_series_id = fields.Many2one(comodel_name='product.series', string='Product Series', store=True,
                                          readonly=False, related='x_product_id.x_product_series')
    x_hs_code_id = fields.Many2one(comodel_name='hs.code.database', string='HS Code', store=True, readonly=False,
                                   related='x_product_id.x_hs_code_tr_id')

    x_local_qty = fields.Integer(string='Turkey Qty', required=False)
    x_local_value = fields.Monetary(string='Turkey Value', required=False)

    x_export_qty = fields.Integer(string='Abroad Qty', required=False)
    x_export_value = fields.Monetary(string='Abroad Value', required=False)


class ReportManufacturingLines(models.Model):
    _name = 'report.manufacturing.lines'
    _description = "Report Manufacturing Lines"
    _rec_name = 'x_product_id'
    _order = 'x_export_value desc'

    x_report_id = fields.Many2one(comodel_name='inventory.sale.report', string='Report', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related='x_report_id.x_currency_id')

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False,
                                   domain="[('categ_id.name', 'ilike', 'Finished')]")
    x_product_series_id = fields.Many2one(comodel_name='product.series', string='Product Series', store=True,
                                          readonly=False, related='x_product_id.x_product_series')
    x_hs_code_id = fields.Many2one(comodel_name='hs.code.database', string='HS Code', store=True, readonly=False,
                                   related='x_product_id.x_hs_code_tr_id')

    x_export_qty = fields.Integer(string='Quantity', required=False)
    x_export_value = fields.Monetary(string='Value', required=False)


class ReportRawMaterialLines(models.Model):
    _name = 'report.raw.material.lines'
    _description = "Report Raw Material Lines"
    _rec_name = 'x_product_id'
    _order = 'x_export_value desc'

    x_report_id = fields.Many2one(comodel_name='inventory.sale.report', string='Report', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related='x_report_id.x_currency_id')

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False,
                                   domain="[('categ_id.name', 'ilike', 'Finished')]")
    x_sub_type_id = fields.Many2one(comodel_name='product.sub.type', string='Sub Type', store=True,
                                    readonly=False, related='x_product_id.dk_sub_category')
    x_hs_code_id = fields.Many2one(comodel_name='hs.code.database', string='HS Code', store=True, readonly=False,
                                   related='x_product_id.x_hs_code_tr_id')

    x_local_qty = fields.Integer(string='Turkey Qty', required=False)
    x_local_value = fields.Monetary(string='Turkey Value', required=False)

    x_export_qty = fields.Integer(string='Abroad Qty', required=False)
    x_export_value = fields.Monetary(string='Abroad Value', required=False)


class PortfolioProducts(models.Model):
    _name = 'portfolio.products'
    _description = 'Portfolio Products'
    _rec_name = 'x_product_id'
    _order = 'sequence'

    x_report_id = fields.Many2one(comodel_name='inventory.sale.report', string='Report', required=False)
    sequence = fields.Integer(string='Sequence', required=False)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False,
                                   domain="[('categ_id.name', 'ilike', 'Finished')]")


