from odoo import models


class InventorySaleReportExcel(models.AbstractModel):
    _name = 'report.cus_product_360_view.inventory_sale_report_excel'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Inventory Sale Report Excel"

    def generate_xlsx_report(self, workbook, data, objs):
        for obj in objs:
            font_size = workbook.add_format({'font_size': 12})
            heading = workbook.add_format({'font_size': 12, 'bold': 1})
            heading_center = workbook.add_format({'font_size': 12, 'bold': 1, 'align': 'center'})
            # Raw Material to be Purchased (Summary)
            sheet = workbook.add_worksheet('Raw Material to be Purchased (Summary)')

            sheet.merge_range('A1:B1', 'Raw Material to be Purchased', heading)
            sheet.merge_range('C1:D1', 'Turkey', heading_center)
            sheet.merge_range('E1:F1', 'Abroad', heading_center)

            row = 1
            sheet.write(row, 0, 'Name of the Good', heading)
            sheet.write(row, 1, 'Tariff Number', heading)
            sheet.write(row, 2, 'Quantity', heading_center)
            sheet.write(row, 3, 'Value', heading_center)
            sheet.write(row, 4, 'Quantity', heading_center)
            sheet.write(row, 5, 'Value', heading_center)

            report_data = obj.report_data()
            raw_material_data = report_data['raw_material_data']

            total_1 = 0
            total_2 = 0
            total_3 = 0
            total_4 = 0
            for data in raw_material_data:
                row += 1
                sheet.write(row, 0, data['column_8'], font_size)
                sheet.write(row, 1, data['column_3'], font_size)
                sheet.write(row, 2, data['column_4'], font_size)
                sheet.write(row, 3, data['column_5'], font_size)
                sheet.write(row, 4, data['column_6'], font_size)
                sheet.write(row, 5, data['column_7'], font_size)
                total_1 += data['column_4']
                total_2 += data['column_5']
                total_3 += data['column_6']
                total_4 += data['column_7']

            row += 1
            sheet.merge_range('A%s:B%s' % (row + 1, row + 1), 'Total', heading)
            sheet.write(row, 2, total_1, heading)
            sheet.write(row, 3, total_2, heading)
            sheet.write(row, 4, total_3, heading)
            sheet.write(row, 5, total_4, heading)

            # Raw Material to be Purchased (Details)
            sheet = workbook.add_worksheet('Raw Material to be Purchased (Details)')

            sheet.merge_range('A1:B1', 'Raw Material to be Purchased', heading)
            sheet.merge_range('C1:D1', 'Turkey', heading_center)
            sheet.merge_range('E1:F1', 'Abroad', heading_center)

            row = 1
            sheet.write(row, 0, 'Name of the Good', heading)
            sheet.write(row, 1, 'Tariff Number', heading)
            sheet.write(row, 2, 'Quantity', heading_center)
            sheet.write(row, 3, 'Value', heading_center)
            sheet.write(row, 4, 'Quantity', heading_center)
            sheet.write(row, 5, 'Value', heading_center)

            for data in obj.x_raw_material_line_ids:
                row += 1
                sheet.write(row, 0, data.x_product_id.name, font_size)
                sheet.write(row, 1, data.x_hs_code_id.x_hs_code, font_size)
                sheet.write(row, 2, data.x_local_qty, font_size)
                sheet.write(row, 3, data.x_local_value, font_size)
                sheet.write(row, 4, data.x_export_qty, font_size)
                sheet.write(row, 5, data.x_export_value, font_size)

            row += 1
            sheet.merge_range('A%s:B%s' % (row + 1, row + 1), 'Total', heading)
            sheet.write(row, 2, total_1, heading)
            sheet.write(row, 3, total_2, heading)
            sheet.write(row, 4, total_3, heading)
            sheet.write(row, 5, total_4, heading)

            # Goods to be Produced
            sheet = workbook.add_worksheet('Goods to be Produced')

            sheet.merge_range('A1:D1', 'Goods to be Produced', heading)
            row = 1
            sheet.write(row, 0, 'Name of the Good', heading)
            sheet.write(row, 1, 'Tariff Number', heading)
            sheet.write(row, 2, 'Quantity', heading)
            sheet.write(row, 3, 'Value', heading)

            manufacturing_data = report_data['manufacturing_data']

            total_1 = 0
            total_2 = 0
            for data in manufacturing_data:
                row += 1
                sheet.write(row, 0, data['column_1'], font_size)
                sheet.write(row, 1, data['column_3'], font_size)
                sheet.write(row, 2, data['column_4'], font_size)
                sheet.write(row, 3, data['column_5'], font_size)
                total_1 += data['column_4']
                total_2 += data['column_5']

            row += 1
            sheet.merge_range('A%s:B%s' % (row + 1, row + 1), 'Total', heading)
            sheet.write(row, 2, total_1, heading)
            sheet.write(row, 3, total_2, heading)

            # Goods to be Sold
            sheet = workbook.add_worksheet('Goods to be Sold')

            sheet.merge_range('A1:B1', 'Goods to be Sold', heading)
            sheet.merge_range('C1:D1', 'Turkey', heading_center)
            sheet.merge_range('E1:F1', 'Abroad', heading_center)

            row = 1
            sheet.write(row, 0, 'Name of the Good', heading)
            sheet.write(row, 1, 'Tariff Number', heading)
            sheet.write(row, 2, 'Quantity', heading_center)
            sheet.write(row, 3, 'Value', heading_center)
            sheet.write(row, 4, 'Quantity', heading_center)
            sheet.write(row, 5, 'Value', heading_center)

            sales_data = report_data['sales_data']

            total_1 = 0
            total_2 = 0
            total_3 = 0
            total_4 = 0
            for data in sales_data:
                row += 1
                sheet.write(row, 0, data['column_1'], font_size)
                sheet.write(row, 1, data['column_3'], font_size)
                sheet.write(row, 2, data['column_4'], font_size)
                sheet.write(row, 3, data['column_5'], font_size)
                sheet.write(row, 4, data['column_6'], font_size)
                sheet.write(row, 5, data['column_7'], font_size)
                total_1 += data['column_4']
                total_2 += data['column_5']
                total_3 += data['column_6']
                total_4 += data['column_7']

            row += 1
            sheet.merge_range('A%s:B%s' % (row + 1, row + 1), 'Total', heading)
            sheet.write(row, 2, total_1, heading)
            sheet.write(row, 3, total_2, heading)
            sheet.write(row, 4, total_3, heading)
            sheet.write(row, 5, total_4, heading)

