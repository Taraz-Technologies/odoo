
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import xlsxwriter


class ReportBOMXlsx(models.AbstractModel):
    _name = 'report.cable_assembly.cable_assembly_bom_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Cable Assembly BOM"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size = workbook.add_format({'font_size': 12})
        for bom in objs.x_bom_ids:
            sheet = workbook.add_worksheet(bom.x_product_id.name + " - BOM")

            row = 0
            sheet.write(row, 0, 'Value', font_size)
            sheet.write(row, 1, 'Name', font_size)
            sheet.write(row, 2, 'RefDes', font_size)
            sheet.write(row, 3, 'Quantity', font_size)
            sheet.write(row, 4, 'Pattern', font_size)
            sheet.write(row, 5, 'X (mm)', font_size)
            sheet.write(row, 6, 'Y (mm)', font_size)
            sheet.write(row, 7, 'Side', font_size)
            sheet.write(row, 8, 'Rotate', font_size)
            sheet.write(row, 9, 'Hierarchy', font_size)

            for line in bom.x_product_bom_id.x_bom_line_ids:
                if line.x_start_connector.x_product_id:
                    row += 1
                    sheet.write(row, 0, line.x_start_connector.x_product_id.name, font_size)
                    sheet.write(row, 1, line.x_start_connector.x_product_id.description, font_size)
                    sheet.write(row, 2, 'P' + str(row), font_size)
                if line.x_end_connector.x_product_id:
                    row += 1
                    sheet.write(row, 0, line.x_end_connector.x_product_id.name, font_size)
                    sheet.write(row, 1, line.x_end_connector.x_product_id.description, font_size)
                    sheet.write(row, 2, 'P' + str(row), font_size)
                if line.x_wire.x_product_id:
                    row += 1
                    sheet.write(row, 0, line.x_wire.x_product_id.name, font_size)
                    sheet.write(row, 1, line.x_wire.x_product_id.description, font_size)
                    sheet.write(row, 2, 'P' + str(row), font_size)

        # bom_lines = []
        # bom_products = []
        # for line in objs.x_wiring_lines:
        #     if line.x_ref_des.x_start_connector.x_product_id:
        #         bom_line = [line.x_ref_des.x_start_connector.x_product_id.name, line.x_ref_des.x_start_connector.x_product_id.description, line.x_quantity]
        #         bom_lines.append(bom_line)
        #         if not line.x_ref_des.x_start_connector.x_product_id.name in bom_products:
        #             bom_products.append(line.x_ref_des.x_start_connector.x_product_id.name)
        #     if line.x_ref_des.x_end_connector.x_product_id:
        #         bom_line = [line.x_ref_des.x_end_connector.x_product_id.name, line.x_ref_des.x_end_connector.x_product_id.description, line.x_quantity]
        #         bom_lines.append(bom_line)
        #         if not line.x_ref_des.x_end_connector.x_product_id.name in bom_products:
        #             bom_products.append(line.x_ref_des.x_end_connector.x_product_id.name)
        #     if line.x_ref_des.x_wire.x_product_id:
        #         bom_line = [line.x_ref_des.x_wire.x_product_id.name, line.x_ref_des.x_wire.x_product_id.description, line.x_quantity]
        #         bom_lines.append(bom_line)
        #         if not line.x_ref_des.x_wire.x_product_id.name in bom_products:
        #             bom_products.append(line.x_ref_des.x_wire.x_product_id.name)
        #
        # for product in bom_products:
        #     quantity = 0
        #     description = ''
        #     for line in bom_lines:
        #         if product == line[0]:
        #             description = line[1]
        #             quantity += line[2]
        #     row += 1
        #     sheet.write(row, 0, product, font_size)
        #     sheet.write(row, 1, description, font_size)
        #     sheet.write(row, 2, quantity, font_size)


class ReportWireLabele800tkXlsx(models.AbstractModel):
    _name = 'report.cable_assembly.cable_assembly_wire_label_e800tk_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Wire Label e800tk"

    def generate_xlsx_report(self, workbook, data, objs):
        e800tk = workbook.add_worksheet(objs.x_name + " - Wire Label - E800TK")
        font_size = workbook.add_format({'font_size': 12})

        row_e800tk = 0
        e800tk.write(row_e800tk, 0, 'Label', font_size)
        e800tk.write(row_e800tk, 1, 'Printer', font_size)

        harness = []
        core = []
        for line in objs.x_wiring_lines:
            printer = False
            harness_printer = False
            if line.x_ref_des.x_start_connector:
                if line.x_ref_des.x_start_connector.x_printer:
                    printer = line.x_ref_des.x_start_connector.x_printer
            if line.x_ref_des.x_end_connector:
                if line.x_ref_des.x_end_connector.x_printer:
                    printer = line.x_ref_des.x_end_connector.x_printer
            if line.x_ref_des.x_harness.x_printer:
                harness_printer = line.x_ref_des.x_harness.x_printer
            if not line.x_harness in harness:
                harness.append(line.x_harness)
                for qty in range(line.x_quantity):
                    if harness_printer == 'E800TK':
                        if line.x_harness_label:
                            row_e800tk += 1
                            e800tk.write(row_e800tk, 0, line.x_harness.x_name, font_size)
                            e800tk.write(row_e800tk, 1, harness_printer, font_size)
            if not line.x_wire_core in core:
                core.append(line.x_wire_core)
                for qty in range(line.x_quantity):
                    if printer == 'E800TK':
                        if line.x_core_label:
                            row_e800tk += 1
                            e800tk.write(row_e800tk, 0, line.x_wire_core.x_name, font_size)
                            e800tk.write(row_e800tk, 1, printer, font_size)
            for qty in range(line.x_quantity):
                if printer == 'E800TK':
                    if line.x_start_label:
                        row_e800tk += 1
                        e800tk.write(row_e800tk, 0, line.x_start_heat_shrink_label, font_size)
                        e800tk.write(row_e800tk, 1, printer, font_size)
                    if line.x_end_label:
                        row_e800tk += 1
                        e800tk.write(row_e800tk, 0, line.x_end_heat_shrink_label, font_size)
                        e800tk.write(row_e800tk, 1, printer, font_size)
                    if line.x_wire_label:
                        row_e800tk += 1
                        e800tk.write(row_e800tk, 0, line.x_name, font_size)
                        e800tk.write(row_e800tk, 1, printer, font_size)


class ReportWireLabelp600Xlsx(models.AbstractModel):
    _name = 'report.cable_assembly.cable_assembly_wire_label_p600_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Wire Label p600'

    def generate_xlsx_report(self, workbook, data, objs):
        p600 = workbook.add_worksheet(objs.x_name + " - Wire Label - P600")
        font_size = workbook.add_format({'font_size': 12})

        row_p600 = 0
        p600.write(row_p600, 0, 'Label', font_size)
        p600.write(row_p600, 1, 'Printer', font_size)

        harness = []
        core = []
        for line in objs.x_wiring_lines:
            printer = False
            harness_printer = False
            if line.x_ref_des.x_start_connector:
                if line.x_ref_des.x_start_connector.x_printer:
                    printer = line.x_ref_des.x_start_connector.x_printer
            if line.x_ref_des.x_end_connector:
                if line.x_ref_des.x_end_connector.x_printer:
                    printer = line.x_ref_des.x_end_connector.x_printer
            if line.x_ref_des.x_harness.x_printer:
                harness_printer = line.x_ref_des.x_harness.x_printer
            if not line.x_harness in harness:
                harness.append(line.x_harness)
                for qty in range(line.x_quantity):
                    if harness_printer == 'P600':
                        if line.x_harness_label:
                            row_p600 += 1
                            p600.write(row_p600, 0, line.x_harness.x_name, font_size)
                            p600.write(row_p600, 1, harness_printer, font_size)
            if not line.x_wire_core in core:
                core.append(line.x_wire_core)
                for qty in range(line.x_quantity):
                    if printer == 'P600':
                        if line.x_core_label:
                            row_p600 += 1
                            p600.write(row_p600, 0, line.x_wire_core.x_name, font_size)
                            p600.write(row_p600, 1, printer, font_size)
            for qty in range(line.x_quantity):
                if printer == 'P600':
                    if line.x_start_label:
                        row_p600 += 1
                        p600.write(row_p600, 0, line.x_start_heat_shrink_label, font_size)
                        p600.write(row_p600, 1, printer, font_size)
                    if line.x_end_label:
                        row_p600 += 1
                        p600.write(row_p600, 0, line.x_end_heat_shrink_label, font_size)
                        p600.write(row_p600, 1, printer, font_size)
                    if line.x_wire_label:
                        row_p600 += 1
                        p600.write(row_p600, 0, line.x_name, font_size)
                        p600.write(row_p600, 1, printer, font_size)


class ReportProductLabelXlsx(models.AbstractModel):
    _name = 'report.cable_assembly.cable_assembly_product_label_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Product Label'

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet(objs.x_name + " - Product Label")
        font_size = workbook.add_format({'font_size': 12})

        row = 0
        sheet.write(row, 0, 'Product Name', font_size)

        product_names = []
        for line in objs.x_wiring_lines:
            if line.x_ref_des.x_start_product:
                if line.x_ref_des.x_start_product.x_label_required:
                    if not line.x_ref_des.x_start_product_id.x_name in product_names:
                        product_names.append(line.x_ref_des.x_start_product_id.x_name)
                        for qty in range(line.x_quantity):
                            row += 1
                            sheet.write(row, 0, line.x_ref_des.x_start_product_id.x_name, font_size)
            if line.x_ref_des.x_end_product:
                if line.x_ref_des.x_end_product.x_label_required:
                    if not line.x_ref_des.x_end_product_id.x_name in product_names:
                        product_names.append(line.x_ref_des.x_end_product_id.x_name)
                        for qty in range(line.x_quantity):
                            row += 1
                            sheet.write(row, 0, line.x_ref_des.x_end_product_id.x_name, font_size)


class ReportCutListXlsx(models.AbstractModel):
    _name = 'report.cable_assembly.cable_assembly_cut_list_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Cut List'

    def add_row(self, sheet, row, row_data, format):
        column = 0
        for cell_data in row_data:
            sheet.write(row, column, cell_data, format)
            column += 1

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet(objs.x_name + " - Cut List")
        font_size = workbook.add_format({'font_size': 12})

        row = 0
        row_data = ['Ref Def','Cable Details','Label Details','Quantity','Unit Length','Wire Core','Harness',
                    'Start Label','End Label','Wire Label','Core Label','Harness Label',]
        self.add_row(sheet, row, row_data, font_size)

        for line in objs.x_wiring_lines:
            row += 1

            cable_details = 'Wire: ' + line.x_wire.x_name if line.x_wire else ''
            cable_details += '\nStart Conn.: ' + line.x_start_connector.x_name if line.x_start_connector else ''
            cable_details += '\nEnd Conn.: ' + line.x_end_connector.x_name if line.x_end_connector else ''

            unit_length = str(round(line.x_unit_length,2)) + ' ' + line.x_uom_id.name if line.x_uom_id else '0'

            cable_label = 'Wire Label: ' + line.x_name if line.x_name else ''
            cable_label += '\nStart Label: ' + line.x_start_heat_shrink_label if line.x_start_heat_shrink_label else ''
            cable_label += '\nEnd Label: ' + line.x_end_heat_shrink_label if line.x_end_heat_shrink_label else ''

            wire_core = line.x_wire_core.x_name if line.x_wire_core else ''
            harness = line.x_harness.x_name if line.x_harness else ''

            row_data = [line.x_ref_des.x_ref_des,cable_details,cable_label,line.x_quantity,unit_length,wire_core,harness,
                        line.x_start_label,line.x_end_label,line.x_wire_label,line.x_core_label,line.x_harness_label]
            self.add_row(sheet, row, row_data, font_size)










