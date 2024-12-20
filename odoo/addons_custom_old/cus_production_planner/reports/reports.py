from odoo import models

import base64
import io
import csv


class MachineFileExcelReport(models.AbstractModel):
    _name = 'report.cus_production_planner.assembly_process_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Machine File Excel Report"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size = workbook.add_format({'font_size': 12})
        for obj in objs:
            sheet = workbook.add_worksheet("ND4 Machine File")

            headers = [
                '#Feeder', 'Feeder ID', 'Type', 'Nozzle', 'X', 'Y', 'Angle', 'Footprint', 'Value', 'Pick height',
                'Pick delay', 'Placement height', 'Placement delay', 'Vacuum detection', 'Vacuum value',
                'Vision alignment', 'Speed',
            ]

            row = 0
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size)

            obj.x_nd4_feeder_ids.compute_nozzles()
            for feeder in obj.x_nd4_feeder_ids.filtered(lambda l: l.x_product_id):
                row += 1
                vals = [
                    'stack', int(feeder.x_name[-2:]), 0, feeder.x_nozzle, feeder.x_x_mm, feeder.x_y_mm,
                    feeder.x_pick_angle, feeder.x_package_id.x_name, feeder.x_product_id.name, feeder.x_pick_height, 100,
                    feeder.x_place_height, 100, 'No', -40, 1, 60, feeder.x_feed_rate, 50, 80, 'No', 'No', -40, -40, -40, -40
                ]
                for column in range(len(vals)):
                    sheet.write(row, column, vals[column], font_size)

            csv_data = base64.b64decode(obj.x_nd4_settings)
            try:
                data_file = io.StringIO(csv_data.decode("utf-8"))
            except:
                data_file = io.StringIO(csv_data.decode("latin-1"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)

            x_first = 0
            y_first = 0
            for file_row in file_reader:
                if file_row[0] in ['pcb', 'mark', 'markext', 'test', 'mirror_create', 'mirror']:
                    row += 1
                    for column in range(len(file_row)):
                        sheet.write(row, column, file_row[column], font_size)
                if file_row[0] == 'mirror_create':
                    x_first = float(file_row[3])
                    y_first = float(file_row[4])

            x_difference = 0
            y_difference = 0
            first_component_id = obj.x_pnp_line_ids.filtered(lambda l: l.x_ref_des == obj.x_first_component)
            if first_component_id:
                x_axis = first_component_id.x_x_axis
                y_axis = first_component_id.x_y_axis

                if obj.x_mirror == 'mirror_x':
                    x_axis = obj.x_pcb_length - x_axis
                elif obj.x_mirror == 'mirror_y':
                    y_axis = obj.x_pcb_width - y_axis

                if obj.x_rotation == '90':
                    y = y_axis
                    y_axis = x_axis
                    x_axis = obj.x_pcb_width - y
                elif obj.x_rotation == '180':
                    x_axis = obj.x_pcb_length - x_axis
                    y_axis = obj.x_pcb_width - y_axis
                elif obj.x_rotation == '-90':
                    x = x_axis
                    x_axis = obj.x_pcb_width - y_axis
                    y_axis = obj.x_pcb_length - x

                x_difference = x_first - x_axis
                y_difference = y_first - y_axis

            headers = ['#Chip', 'Feeder ID', 'Nozzle', 'Name', 'Value', 'Footprint', 'X', 'Y', 'Rotation', 'Skip']

            row += 1
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size)

            nozzle = 0
            for feeder in obj.x_nd4_feeder_ids.filtered(lambda l: l.x_product_id):
                pnp_line_ids = obj.x_pnp_line_ids.filtered(
                    lambda l: l.x_product_id.id == feeder.x_product_id.id and l.x_side == obj.x_pcb_side
                )
                for line in pnp_line_ids:
                    x_axis = line.x_x_axis
                    y_axis = line.x_y_axis
                    rotate = line.x_angle

                    if obj.x_mirror == 'mirror_x':
                        x_axis = obj.x_pcb_length - x_axis
                    elif obj.x_mirror == 'mirror_y':
                        y_axis = obj.x_pcb_width - y_axis

                    if obj.x_rotation == '90':
                        y = y_axis
                        y_axis = x_axis
                        x_axis = obj.x_pcb_width - y
                        rotate += 90
                        rotate = 0 if rotate == 360 else rotate
                        rotate = -90 if rotate == 270 else rotate
                        rotate = 180 if rotate == -180 else rotate
                    elif obj.x_rotation == '180':
                        x_axis = obj.x_pcb_length - x_axis
                        y_axis = obj.x_pcb_width - y_axis
                        rotate += 180
                        rotate = 0 if rotate == 360 else rotate
                        rotate = -90 if rotate == 270 else rotate
                        rotate = 180 if rotate == -180 else rotate
                    elif obj.x_rotation == '-90':
                        x = x_axis
                        x_axis = obj.x_pcb_width - y_axis
                        y_axis = obj.x_pcb_length - x
                        rotate -= 90
                        rotate = 0 if rotate == 360 else rotate
                        rotate = -90 if rotate == 270 else rotate
                        rotate = 180 if rotate == -180 else rotate

                    x_axis += x_difference + obj.x_x_shift
                    y_axis += y_difference + obj.x_y_shift

                    if nozzle >= len(feeder.x_nozzle):
                        nozzle = 0

                    vals = [
                        'comp',
                        int(feeder.x_name[-2:]),
                        feeder.x_nozzle[nozzle],
                        line.x_ref_des,
                        feeder.x_product_id.name,
                        feeder.x_package_id.x_name,
                        x_axis,
                        y_axis,
                        rotate,
                        'No',
                    ]
                    nozzle += 1
                    row += 1
                    for column in range(len(vals)):
                        sheet.write(row, column, vals[column], font_size)










