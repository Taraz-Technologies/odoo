from odoo import models
from odoo.exceptions import UserError


class PurchaseOrderLinesXlsx(models.AbstractModel):
    _name = 'report.cus_purchase.report_purchase_order_lines_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Consolidation Products"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet(rec.name)

            row = 0
            sheet.write(row, 0, 'Product', font_size_bold)
            sheet.write(row, 1, 'Description', font_size_bold)
            sheet.write(row, 2, 'Quantity', font_size_bold)
            sheet.write(row, 3, 'UoM', font_size_bold)
            sheet.write(row, 4, 'Unit Price', font_size_bold)
            sheet.write(row, 5, 'Ext. Price', font_size_bold)
            sheet.write(row, 6, 'HS Code', font_size_bold)
            sheet.write(row, 7, 'GTIP Code', font_size_bold)
            sheet.write(row, 8, 'COO', font_size_bold)

            for line in rec.order_line:
                row += 1
                sheet.write(row, 0, line.product_id.name, font_size)
                sheet.write(row, 1, line.name, font_size)
                sheet.write(row, 2, line.product_qty, font_size)
                sheet.write(row, 3, line.product_uom.name, font_size)
                sheet.write(row, 4, line.price_unit, font_size)
                sheet.write(row, 5, line.price_subtotal, font_size)
                sheet.write(row, 6, line.product_id.dk_hs_code.x_hs_code, font_size)
                sheet.write(row, 7, line.product_id.x_hs_code_tr_id.x_hs_code, font_size)
                sheet.write(row, 8, line.product_id.x_country_id.name, font_size)











