from odoo import models, fields


class ReportDownloadCartXlsx(models.AbstractModel):
    _name = 'report.cus_procurement_tool.report_download_cart_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Octopart List"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for obj in objs:
            sheet = workbook.add_worksheet(obj.x_name)

            headers = [
                'PRC Line',
                'Relation',
                'Product',
                'Type',
                'Description',
                'Quantity',
                'EOQ',
                'UoM',
                'Unit Price',
                'Extended Price',
                'Actual Unit Price',
                'Actual Extended Price',
                'Overspent (%)',
            ]

            row = 0
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size_bold)

            for line in obj.x_component_ids:
                row += 1
                part_number_id = line.x_product_id.x_taraz_part_number_id
                vals = [
                    line.x_component_id.x_product_id.name,
                    line.x_relation,
                    line.x_product_id.name,
                    dict(part_number_id._fields['x_mounting_type'].selection).get(line.x_mounting_type),
                    line.x_description,
                    line.x_quantity,
                    line.x_eoq,
                    line.x_uom_id.name,
                    line.x_unit_price,
                    line.x_ext_price,
                    line.x_actual_unit_price,
                    line.x_actual_ext_price,
                    round(line.x_overspent * 100, 2),
                ]

                for column in range(len(vals)):
                    sheet.write(row, column, vals[column], font_size)
