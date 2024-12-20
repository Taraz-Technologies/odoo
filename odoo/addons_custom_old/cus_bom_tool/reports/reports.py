from odoo import models


class BaseBomLinesExcelReport(models.AbstractModel):
    _name = 'report.cus_bom_tool.base_bom_lines_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "BoM Lines Excel Report"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for obj in objs:
            sheet = workbook.add_worksheet(obj.x_base_bom_id.x_name)

            headers = [
                'Part # (Design)', 'Description (Design)', 'RefDes',
                'Old Part #', 'Taraz Part #', 'Part #',
                'Line Quantity', 'Line UoM', 'Real Quantity',
                'Product UoM', 'Description', 'Block',
                'Notes', 'Moved to', 'Mounting Type',
                'DNP', 'Critical', 'Variant',
                'Investor Product', 'Design (New)', 'Design (Modified)',
                'Design (Deleted)', 'Odoo (New)', 'Odoo (Modified)',
                'Odoo (Deleted)'
            ]

            row = 0
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size_bold)

            for line in obj.x_base_bom_id.x_bom_line_ids:
                row += 1
                vals = [
                    line.x_name, line.x_part_description, line.x_ref_des,
                    line.x_old_product_id.name, line.x_taraz_part_id.x_name, line.x_product_id.name,
                    line.x_quantity, line.x_uom_id.name, line.x_real_quantity,
                    line.x_product_id.uom_id.name, line.x_description, line.x_line_block_id.x_name,
                    line.x_notes, line.x_move_to_tool_id.x_name, line.x_type,
                    line.x_dnp, line.x_critical, line.x_variant,
                    line.x_investor_product, line.x_design_new, line.x_design_modified,
                    line.x_design_deleted, line.x_new, line.x_modified,
                    line.x_deleted
                ]
                for column in range(len(vals)):
                    sheet.write(row, column, vals[column], font_size)










