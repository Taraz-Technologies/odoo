from odoo import api, fields, models
from odoo.exceptions import UserError

import base64
import io
import csv
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    x_bom_tool_id = fields.Many2one(related="product_id.x_bom_tool_id")

    x_pnp_file = fields.Binary(string="PnP File (.csv)")
    x_machine = fields.Selection(selection=[('ND4', 'ND4'), ('ND2', 'ND2')], string='Assembly Machine', required=False)

    # ND4 Data
    x_pnp_line_ids = fields.One2many(comodel_name='assembly.processing', inverse_name='x_work_order_id', string='PnP Lines')
    x_nozzle_config_ids = fields.Many2many(comodel_name='nozzle.config', string='Nozzle Config')

    x_nd4_settings = fields.Binary(string="ND4 Settings")
    x_nd4_settings_name = fields.Char(string="ND4 Settings Name")

    x_pcb_thickness = fields.Float(string='PCB Thickness', digits=(4, 4), default=1.6)
    x_pcb_mounting = fields.Selection(selection=[('rail', 'Rail'), ('fix', 'Fixed')], string='PCB Mounting')
    x_pcb_side = fields.Selection(selection=[('Top', 'Top'), ('Bottom', 'Bottom')], string='PCB Side', default="Top")

    x_first_component = fields.Char(string='First Component (RefDes)', required=False)

    x_x_translation = fields.Float(string="First Component's X", digits=(4, 4))
    x_y_translation = fields.Float(string="First Component's Y", digits=(4, 4))

    x_x_shift = fields.Float(string="X Shift", digits=(4, 4))
    x_y_shift = fields.Float(string="Y Shift", digits=(4, 4))

    x_pcb_length = fields.Float(string="PCB Width", digits=(4, 4))
    x_pcb_width = fields.Float(string="PCB Height", digits=(4, 4))

    x_rotation = fields.Selection(selection=[('90', '90'), ('180', '180'), ('-90', '-90')], string='Rotation')
    x_mirror = fields.Selection(selection=[('mirror_x', 'Mirror X'), ('mirror_y', 'Mirror Y')], string='Mirror')

    x_nd4_feeder_ids = fields.Many2many(comodel_name='nd4.feeders', string='ND4 Feeders')

    # ND2 Data
    x_ordinates_x_shift = fields.Float(string='Co-ordinates X Shift', digits=(4, 4))
    x_ordinates_y_shift = fields.Float(string='Co-ordinates Y Shift', digits=(4, 4))
    x_feeders_x_shift = fields.Float(string='Feeders X Shift', digits=(4, 4))
    x_feeders_y_shift = fields.Float(string='Feeders Y Shift', digits=(4, 4))
    x_nd2_speed = fields.Float(string='Speed', digits=(4, 0))
    x_nd2_feeder_ids = fields.Many2many(comodel_name='nd2.feeders', string='ND2 Feeders')

    @api.model
    def default_get(self, fields_list):
        res = super(MrpWorkorder, self).default_get(fields_list)
        res.update({
            'x_nd2_feeder_ids': [
                self.env.ref('cus_production_planner.ND2_FEEDER01').id,
                self.env.ref('cus_production_planner.ND2_FEEDER02').id,
                self.env.ref('cus_production_planner.ND2_FEEDER03').id,
                self.env.ref('cus_production_planner.ND2_FEEDER04').id,
                self.env.ref('cus_production_planner.ND2_FEEDER05').id,
                self.env.ref('cus_production_planner.ND2_FEEDER06').id,
                self.env.ref('cus_production_planner.ND2_FEEDER07').id,
                self.env.ref('cus_production_planner.ND2_FEEDER08').id,
                self.env.ref('cus_production_planner.ND2_FEEDER09').id,
                self.env.ref('cus_production_planner.ND2_FEEDER10').id,
                self.env.ref('cus_production_planner.ND2_FEEDER11').id,
                self.env.ref('cus_production_planner.ND2_FEEDER12').id,
                self.env.ref('cus_production_planner.ND2_FEEDER13').id,
                self.env.ref('cus_production_planner.ND2_FEEDER14').id,
                self.env.ref('cus_production_planner.ND2_FEEDER15').id,
                self.env.ref('cus_production_planner.ND2_FEEDER16').id,
                self.env.ref('cus_production_planner.ND2_FEEDER17').id,
                self.env.ref('cus_production_planner.ND2_FEEDER18').id,
                self.env.ref('cus_production_planner.ND2_FEEDER19').id,
                self.env.ref('cus_production_planner.ND2_FEEDER20').id,
                self.env.ref('cus_production_planner.ND2_FEEDER21').id,
                self.env.ref('cus_production_planner.ND2_FEEDER22').id,
                self.env.ref('cus_production_planner.ND2_FEEDER23').id,
                self.env.ref('cus_production_planner.ND2_FEEDER24').id,
                self.env.ref('cus_production_planner.ND2_FEEDER25').id,
                self.env.ref('cus_production_planner.ND2_FEEDER26').id,
                self.env.ref('cus_production_planner.ND2_FEEDER27').id,
                self.env.ref('cus_production_planner.ND2_FEEDER28').id,
            ],
            'x_nd4_feeder_ids': [
                self.env.ref('cus_production_planner.ND4_FEEDER01').id,
                self.env.ref('cus_production_planner.ND4_FEEDER02').id,
                self.env.ref('cus_production_planner.ND4_FEEDER03').id,
                self.env.ref('cus_production_planner.ND4_FEEDER04').id,
                self.env.ref('cus_production_planner.ND4_FEEDER05').id,
                self.env.ref('cus_production_planner.ND4_FEEDER06').id,
                self.env.ref('cus_production_planner.ND4_FEEDER07').id,
                self.env.ref('cus_production_planner.ND4_FEEDER08').id,
                self.env.ref('cus_production_planner.ND4_FEEDER09').id,
                self.env.ref('cus_production_planner.ND4_FEEDER10').id,
                self.env.ref('cus_production_planner.ND4_FEEDER11').id,
                self.env.ref('cus_production_planner.ND4_FEEDER12').id,
                self.env.ref('cus_production_planner.ND4_FEEDER13').id,
                self.env.ref('cus_production_planner.ND4_FEEDER14').id,
                self.env.ref('cus_production_planner.ND4_FEEDER15').id,
                self.env.ref('cus_production_planner.ND4_FEEDER16').id,
                self.env.ref('cus_production_planner.ND4_FEEDER17').id,
                self.env.ref('cus_production_planner.ND4_FEEDER18').id,
                self.env.ref('cus_production_planner.ND4_FEEDER19').id,
                self.env.ref('cus_production_planner.ND4_FEEDER20').id,
                self.env.ref('cus_production_planner.ND4_FEEDER21').id,
                self.env.ref('cus_production_planner.ND4_FEEDER22').id,
                self.env.ref('cus_production_planner.ND4_FEEDER23').id,
                self.env.ref('cus_production_planner.ND4_FEEDER24').id,
                self.env.ref('cus_production_planner.ND4_FEEDER25').id,
                self.env.ref('cus_production_planner.ND4_FEEDER26').id,
                self.env.ref('cus_production_planner.ND4_FEEDER27').id,
                self.env.ref('cus_production_planner.ND4_FEEDER28').id,
                self.env.ref('cus_production_planner.ND4_FEEDER29').id,
                self.env.ref('cus_production_planner.ND4_FEEDER30').id,
                self.env.ref('cus_production_planner.ND4_FEEDER31').id,
                self.env.ref('cus_production_planner.ND4_FEEDER32').id,
                self.env.ref('cus_production_planner.ND4_FEEDER33').id,
                self.env.ref('cus_production_planner.ND4_FEEDER34').id,
                self.env.ref('cus_production_planner.ND4_FEEDER35').id,
                self.env.ref('cus_production_planner.ND4_FEEDER36').id,
                self.env.ref('cus_production_planner.ND4_FEEDER37').id,
                self.env.ref('cus_production_planner.ND4_FEEDER38').id,
                self.env.ref('cus_production_planner.ND4_FEEDER39').id,
                self.env.ref('cus_production_planner.ND4_FEEDER40').id,
                self.env.ref('cus_production_planner.ND4_FEEDER41').id,
                self.env.ref('cus_production_planner.ND4_FEEDER42').id,
                self.env.ref('cus_production_planner.ND4_FEEDER43').id,
                self.env.ref('cus_production_planner.ND4_FEEDER44').id,
            ],
        })
        return res

    def record_production(self):
        for rec in self:
            rec.raw_workorder_line_ids.update_line_quantities()
            if any(line.qty_reserved < line.qty_to_consume for line in rec.raw_workorder_line_ids):
                raise UserError("Cannot record production!"
                                "\n"
                                "Some workorder lines are not completely reserved in Manufacturing order")
        return super(MrpWorkorder, self).record_production()


    def button_start(self):
        for rec in self:
            rec.raw_workorder_line_ids.update_line_quantities()
        return super(MrpWorkorder, self).button_start()


    def button_pending(self):
        for rec in self:
            rec.raw_workorder_line_ids.update_line_quantities()
        return super(MrpWorkorder, self).button_pending()

    def arrange_ref_des(self):
        for rec in self:
            for line in rec.raw_workorder_line_ids:
                ref_des = line.x_ref_des.split(', ')

    def compute_pnp_lines(self):
        for rec in self:
            rec.x_pnp_line_ids = [(2, line.id) for line in rec.x_pnp_line_ids]

            if not rec.x_pnp_file:
                raise UserError("PnP file not attached!")

            csv_data = base64.b64decode(rec.x_pnp_file)
            try:
                data_file = io.StringIO(csv_data.decode("utf-8"))
            except:
                data_file = io.StringIO(csv_data.decode("latin-1"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)

            pnp_data = []
            for row in file_reader:
                for line in rec.raw_workorder_line_ids:
                    if row[0] in line.x_ref_des.split(', '):
                        pnp_data.append((0, 0, {
                            'x_ref_des': row[0],
                            'x_x_axis': row[1],
                            'x_y_axis': row[2],
                            'x_side': row[3],
                            'x_angle': row[4],
                            'x_product_id': line.product_id.id,
                        }))

            rec.x_pnp_line_ids = [(2, line.id) for line in rec.x_pnp_line_ids]
            rec.x_pnp_line_ids = pnp_data

            nozzles = rec.x_pnp_line_ids.mapped('x_package_id').mapped('x_nozzle_ids')
            if len(nozzles) > 4:
                raise UserError("Nozzles configuration is getting more than 4 nozzles due to different packages!")

            total_lines = len(rec.x_pnp_line_ids)
            nozzle_config_ids = self.env['nozzle.config'].search([])
            rec.x_nd4_feeder_ids.compute_nozzles()

    @api.onchange('x_nd4_settings')
    def get_translation(self):
        for rec in self:
            if not rec.x_nd4_settings:
                rec.x_x_translation = 0
                rec.x_y_translation = 0
                continue

            csv_data = base64.b64decode(rec.x_nd4_settings)
            try:
                data_file = io.StringIO(csv_data.decode("utf-8"))
            except:
                data_file = io.StringIO(csv_data.decode("latin-1"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)

            for file_row in file_reader:
                if file_row[0] == 'mirror_create':
                    rec.x_x_translation = float(file_row[3])
                    rec.x_y_translation = float(file_row[4])

    def export_machine_file(self):
        for rec in self:
            if not rec.x_nd4_settings:
                raise UserError("Settings file not attached!")
            if rec.x_rotation and (rec.x_pcb_length == 0 or rec.x_pcb_width == 0):
                raise UserError("You must define PCB dimension if you want to rotate the PCB")
            if rec.x_mirror and (rec.x_pcb_length == 0 or rec.x_pcb_width == 0):
                raise UserError("You must define PCB dimension if you want to mirror the PCB")
            if rec.x_nd4_feeder_ids.filtered(lambda l: l.x_product_id and not l.x_nozzle):
                raise UserError("Some feeder nozzles are not defined!")
        return self.env.ref('cus_production_planner.assembly_process_excel_report').report_action(self)


class MrpWorkorderLine(models.Model):
    _inherit = "mrp.workorder.line"

    x_ref_des = fields.Char(related="move_id.x_ref_des", readonly=False, store=True)
    x_goods_type = fields.Selection(related="product_id.x_goods_type")
    x_package_id = fields.Many2one(related="product_id.x_package_id")
    x_nozzle_ids = fields.Many2many(related="x_package_id.x_nozzle_ids")

    def update_line_quantities(self):
        for rec in self:
            product_uom_qty = rec.move_id.product_uom_qty
            reserved_availability = rec.move_id.reserved_availability
            qty_producing = rec.raw_workorder_id.qty_producing
            qty_produced = rec.raw_workorder_id.qty_produced
            qty_production = rec.raw_workorder_id.qty_production
            rec.qty_to_consume = (
                    product_uom_qty * qty_producing / (qty_production - qty_produced)
            )
            rec.qty_reserved = rec.qty_to_consume if reserved_availability >= rec.qty_to_consume else reserved_availability
            rec.qty_done = rec.qty_to_consume if reserved_availability >= rec.qty_to_consume else reserved_availability
