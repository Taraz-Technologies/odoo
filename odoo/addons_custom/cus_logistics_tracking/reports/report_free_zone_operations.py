from odoo import models
from odoo.exceptions import UserError


class FreeZoneProductDetails(models.AbstractModel):
    _name = 'report.cus_logistics_tracking.free_zone_product_details'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Free Zone Product Details"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet('Product Details - %s' % rec.x_form_field_01)

            row = 0
            if rec.x_value_mismatch_warning:
                sheet.write(row, 0, rec.x_value_mismatch_warning, font_size_bold)
                row += 1

            sheet.write(row, 0, 'Product', font_size_bold)
            sheet.write(row, 1, 'İşlem Konusu', font_size_bold)
            sheet.write(row, 2, 'Menşei', font_size_bold)
            sheet.write(row, 3, 'Description EN', font_size_bold)
            sheet.write(row, 4, 'Malın Cinsi', font_size_bold)
            sheet.write(row, 5, 'GTIP', font_size_bold)
            sheet.write(row, 6, 'Quantity', font_size_bold)
            sheet.write(row, 7, 'Unit', font_size_bold)
            sheet.write(row, 8, 'Unit Price', font_size_bold)
            sheet.write(row, 9, 'Ext. Price', font_size_bold)
            sheet.write(row, 10, 'Currency', font_size_bold)
            sheet.write(row, 11, 'Unit Weight', font_size_bold)
            sheet.write(row, 12, 'Ext. Weight', font_size_bold)

            total_weight = 0
            for line in rec.x_product_ids:
                row += 1
                sheet.write(row, 0, line.x_product_id.name, font_size)
                sheet.write(row, 1, line.x_form_field_03, font_size)
                if line.x_country_id.x_turkish_translation:
                    sheet.write(row, 2, line.x_country_id.x_turkish_translation, font_size)
                else:
                    sheet.write(row, 2, line.x_country_id.name, font_size)
                sheet.write(row, 3, line.x_product_id.with_context(lang='en_US').description, font_size)
                sheet.write(row, 4, "%s - %s" % (line.x_product_id.with_context(lang='tr_TR').name, line.x_product_id.with_context(lang='tr_TR').description), font_size)
                sheet.write(row, 5, line.x_hs_code_tr_id.x_hs_code, font_size)
                sheet.write(row, 6, round(line.x_quantity, 2), font_size)
                sheet.write(row, 7, line.x_uom_id.name, font_size)
                sheet.write(row, 8, line.x_new_unit or line.x_unit_price, font_size)
                sheet.write(row, 9, line.x_new_subtotal or line.x_subtotal, font_size)
                sheet.write(row, 10, rec.x_currency_id.name, font_size)
                sheet.write(row, 11, line.x_unit_weight, font_size)
                sheet.write(row, 12, round(line.x_quantity * line.x_unit_weight, 2), font_size)
                total_weight += line.x_quantity * line.x_unit_weight

            row += 1
            sheet.write(row, 9, sum(rec.x_product_ids.mapped('x_new_subtotal')) or sum(rec.x_product_ids.mapped('x_subtotal')), font_size)
            sheet.write(row, 10, rec.x_currency_id.name, font_size)
            sheet.write(row, 12, round(total_weight, 2), font_size)


