from odoo import models
from odoo.exceptions import UserError


class PurchaseOrderLinesXlsx(models.AbstractModel):
    _name = 'report.cus_sale.report_sale_order_lines_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Sale Order Lines Products"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet(rec.name)

            row = 0
            sheet.write(row, 0, 'Product', font_size_bold)
            sheet.merge_range(row, 1, row, 2, 'Description', font_size_bold)
            sheet.write(row, 3, 'Quantity', font_size_bold)
            sheet.write(row, 4, 'Unit Price', font_size_bold)
            sheet.write(row, 5, 'Subtotal', font_size_bold)

            for line in rec.order_line:
                row += 1
                sheet.write(row, 0, line.product_id.name, font_size)
                sheet.merge_range(row, 1, row, 2, line.name, font_size)
                sheet.write(row, 3, line.product_uom_qty, font_size)
                sheet.write(row, 4, line.price_unit, font_size)
                sheet.write(row, 5, line.price_subtotal, font_size)











