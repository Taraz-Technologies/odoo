from odoo import models
from odoo.exceptions import UserError


class PurchaseOrderLinesXlsx(models.AbstractModel):
    _name = 'report.cus_stock.report_shipping_invoice_lines_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Shipping Invoice Lines Products"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet(rec.name)

            row = 0
            sheet.write(row, 0, 'Product', font_size_bold)
            sheet.merge_range(row, 1, row, 2, 'Description', font_size_bold)
            sheet.write(row, 3, 'HS Code', font_size_bold)
            sheet.write(row, 4, 'COO', font_size_bold)
            sheet.write(row, 5, 'Quantity', font_size_bold)
            sheet.write(row, 6, 'UoM', font_size_bold)
            sheet.write(row, 7, 'Unit Price', font_size_bold)
            sheet.write(row, 8, 'Subtotal', font_size_bold)

            for line in rec.x_shipping_invoice_lines:
                row += 1
                sheet.write(row, 0, line.product_id.name, font_size)
                sheet.merge_range(row, 1, row, 2, line.name, font_size)
                sheet.write(row, 3, line.hs_code_id.x_hs_code, font_size)
                sheet.write(row, 4, line.country_id.name, font_size)
                sheet.write(row, 5, line.quantity, font_size)
                sheet.write(row, 6, line.product_uom_id.name, font_size)
                sheet.write(row, 7, line.unit_price, font_size)
                sheet.write(row, 8, line.amount, font_size)











