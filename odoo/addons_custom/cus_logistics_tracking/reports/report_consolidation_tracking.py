from odoo import models
from odoo.exceptions import UserError


class ExportConsolidationProducts(models.AbstractModel):
    _name = 'report.cus_logistics_tracking.consolidation_products_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Consolidation Products"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet('Products Data - %s' % rec.x_name)

            row = 0
            sheet.write(row, 0, 'Receipt', font_size)
            sheet.write(row, 1, 'Product', font_size)
            sheet.write(row, 2, 'Description', font_size)
            sheet.write(row, 3, 'HS Code', font_size)
            sheet.write(row, 4, 'COO', font_size)
            sheet.write(row, 5, 'Unit Weight', font_size)
            sheet.write(row, 6, 'UoM', font_size)
            sheet.write(row, 7, 'Quantity', font_size)
            sheet.write(row, 8, 'Unit Price', font_size)
            sheet.write(row, 9, 'Subtotal', font_size)

            for line in rec.x_product_ids:
                country_id = rec.x_country_id if not line.x_country_id else line.x_country_id
                country_id = rec.x_country_id if country_id in rec.x_country_ids.ids else country_id
                row += 1
                sheet.write(row, 0, line.x_picking_id.name, font_size)
                sheet.write(row, 1, line.x_product_id.name, font_size)
                sheet.write(row, 2, line.x_description, font_size)
                sheet.write(row, 3, line.x_dk_hs_code.x_hs_code, font_size)
                sheet.write(row, 4, country_id.name, font_size)
                sheet.write(row, 5, line.x_unit_weight, font_size)
                sheet.write(row, 6, line.x_uom_id.name, font_size)
                sheet.write(row, 7, line.x_uv_quantity, font_size)
                sheet.write(row, 8, round(line.x_uv_unit_price, 2), font_size)
                sheet.write(row, 9, round(line.x_uv_subtotal, 2), font_size)











