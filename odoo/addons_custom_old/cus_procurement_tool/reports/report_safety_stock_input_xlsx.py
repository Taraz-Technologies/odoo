from odoo import models, fields


class ReportSafetyStockInputXlsx(models.AbstractModel):
    _name = 'report.cus_procurement_tool.report_safety_stock_input_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Report Safety StockInput Xlsx"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for obj in objs:
            sheet = workbook.add_worksheet(obj.x_name)

            headers = [
                'Taraz Part #',
                'Consider Compromised',
                'Actual Forecasted',
                'Safety Stock',
                'Reorder Point',
                'Product',
                'Product Category',
                'Mounting Type',
                'Quantity',
                'Unit of Measure',
                'Unit Price',
                'Total Price',
            ]

            row = 0
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size_bold)

            for line in obj.x_safety_stock_input_ids:
                row += 1
                vals = [
                    line.x_taraz_part_id.x_name,
                    line.x_consider_compromised,
                    line.x_qty_available,
                    line.x_safety_stock,
                    line.x_reorder_point,
                    line.x_product_id.name,
                    line.x_product_id.categ_id.name,
                    line.x_product_id.x_mounting_type,
                    line.x_quantity,
                    line.x_uom_id.name,
                    line.x_unit_price,
                    line.x_subtotal,
                ]

                for column in range(len(vals)):
                    sheet.write(row, column, vals[column], font_size)
