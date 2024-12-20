from odoo import models
from odoo.exceptions import UserError


class DhlItemList(models.AbstractModel):
    _name = 'report.cus_logistics_tracking.report_dhl_item_list'
    _inherit = 'report.report_xlsx.abstract'
    _description = "DHL Item List"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size = workbook.add_format({'font_size': 12})
        for rec in objs:
            sheet = workbook.add_worksheet('in')

            row = 0
            for line in rec.x_shipping_invoice_lines:
                sheet.write(row, 0, row + 1, font_size)
                sheet.write(row, 1, line.product_id.name, font_size)
                sheet.write(row, 2, line.name, font_size)
                sheet.write(row, 3, line.hs_code_id.x_hs_code, font_size)
                sheet.write(row, 4, line.quantity, font_size)
                sheet.write(row, 5, line.product_uom_id.name, font_size)
                sheet.write(row, 6, line.amount, font_size)
                sheet.write(row, 7, line.currency_id.name, font_size)
                sheet.write(row, 8, line.weight, font_size)
                sheet.write(row, 9, '', font_size)
                sheet.write(row, 10, line.country_id.name, font_size)
                sheet.write(row, 11, 'SON', font_size)
                sheet.write(row, 12, '12AB', font_size)
                sheet.write(row, 13, 'N', font_size)
                row += 1


