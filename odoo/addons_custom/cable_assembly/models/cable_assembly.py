# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class CableAssembly(models.Model):
    _name = "cable.assembly"
    _description = "Cable Manufacturing"
    _rec_name = "x_name"

    state = fields.Selection(string="Status", required=False, default="draft",
                             selection=[('draft','Draft'),('in_progress','In Progress'),('on_hold','On Hold'),('done','Complete')],)
    x_cable_assembly_demand_list_id = fields.Many2one(comodel_name="cable.assembly.demand.list", string="Demand List",
                                                      required=False, compute="update_demand_list", store=True, )
    x_task_id = fields.Many2one(comodel_name="project.task", string="Task", required=False, )
    x_name = fields.Char(string="Name", required=True, readonly=True, copy=False, default='New')
    x_hours = fields.Float(string="Hours",  required=False, )
    x_time = fields.Datetime(string="Time", required=False, )
    x_bom_ids = fields.One2many(comodel_name="cable.assembly.bom.list", inverse_name="x_cable_assembly_id", string="BOM List", required=False, )
    x_wiring_lines = fields.One2many(comodel_name="cable.assembly.line", inverse_name="x_cable_assembly_id", string="Wiring Lines", required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", required=True, domain="[('category_id', '=', 4)]", default=21)
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_cable_assembly_id", string="Images", required=False, )

    @api.depends('x_wiring_lines','x_bom_ids')
    def update_demand_list(self):
        for rec in self:
            if not rec.x_cable_assembly_demand_list_id:
                vals = {
                    'x_name': 'Demand List: ' + rec.x_name,
                    'x_cable_assembly_id': rec.id
                }
                demand_list = self.env['cable.assembly.demand.list'].create(vals)
                rec.x_cable_assembly_demand_list_id = demand_list.id

    def action_view_demand_list(self):
        action = self.env.ref('cable_assembly.action_demand_list').read()[0]
        form_view = [(self.env.ref('cable_assembly.view_demand_list_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_cable_assembly_demand_list_id.id
        return action

    @api.onchange('x_bom_ids','x_uom_id')
    def update_wiring_lines(self):
        for rec in self:
            rec.x_wiring_lines = [(5, 0)]
            for bom in rec.x_bom_ids:
                for bom_line in bom.x_product_bom_id.x_bom_line_ids:
                    ref_des = rec.x_wiring_lines.mapped('x_ref_des')
                    if not bom_line in ref_des:
                        if bom_line.x_uom_id:
                            unit_length = bom_line.x_unit_length / bom_line.x_uom_id.factor
                            unit_length = unit_length * rec.x_uom_id.factor
                        else:
                            unit_length = 0
                        rec.x_wiring_lines = [(0, 0, {
                            'x_cable_assembly_id': rec.id,
                            'x_name': bom_line.x_name,
                            'x_ref_des': bom_line.id,
                            'x_wire': bom_line.x_wire.id,
                            'x_unit_length': unit_length,
                            'x_uom_id': rec.x_uom_id.id,
                            'x_harness': bom_line.x_harness.id,
                            'x_wire_core': bom_line.x_wire_core.id,
                            'x_start_label': bom_line.x_start_label,
                            'x_end_label': bom_line.x_end_label,
                            'x_wire_label': bom_line.x_wire_label,
                            'x_core_label': bom_line.x_core_label,
                            'x_harness_label': bom_line.x_harness_label,
                            'x_notes': bom_line.x_notes,
                            'x_start_connector': bom_line.x_start_connector.id,
                            'x_start_heat_shrink_label': bom_line.x_start_heat_shrink_label,
                            'x_end_connector': bom_line.x_end_connector.id,
                            'x_end_heat_shrink_label': bom_line.x_end_heat_shrink_label,
                            'x_quantity': bom.x_quantity,
                        })]
                    else:
                        for wiring_line in rec.x_wiring_lines:
                            if wiring_line.x_ref_des.id == bom_line.id:
                                rec.x_wiring_lines = [(1, wiring_line.id, {'x_quantity': wiring_line.x_quantity + bom.x_quantity})]
                                break

    @api.model
    def create(self, vals):
        if vals.get('x_name', 'New') == 'New':
            vals['x_name'] = self.env['ir.sequence'].next_by_code('cable.assembly') or 'New'
        result = super(CableAssembly, self).create(vals)
        return result

    @api.constrains('x_name')
    def create_project_task(self):
        for rec in self:
            name = ''
            for line in rec.x_bom_ids:
                name = name + '[' + line.x_product_id.name + ' x' + str(line.x_quantity) + ']'
            name = rec.x_name + ' ' + name
            vals = {
                'name': name,
                'project_id': 6,
                'user_id': 28,
                'x_cable_manufacturing_id': rec.id,
            }
            task = self.env['project.task'].create(vals)
            rec.x_task_id = task.id

    @api.onchange('x_bom_ids')
    def update_task_name(self):
        for rec in self:
            name = ''
            for line in rec.x_bom_ids:
                name = name + '[' + line.x_product_id.name + ' x' + str(line.x_quantity) + ']'
            name = rec.x_name + ' ' + name
            task = self.env['project.task'].search([('id', '=', rec.x_task_id.id)])
            task.name = name

    def action_view_task(self):
        action = self.env.ref('cable_assembly.act_cable_assembly_project_task_all').read()[0]
        form_view = [(self.env.ref('project.view_task_form2').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_task_id.id
        return action

    def export_bom(self):
        return self.env.ref('cable_assembly.cable_assembly_bom_xlsx').report_action(self)

    def export_wire_label_e800tk(self):
        return self.env.ref('cable_assembly.cable_assembly_wire_label_e800tk_xlsx').report_action(self)

    def export_wire_label_p600(self):
        return self.env.ref('cable_assembly.cable_assembly_wire_label_p600_xlsx').report_action(self)

    def export_product_label(self):
        return self.env.ref('cable_assembly.cable_assembly_product_label_xlsx').report_action(self)

    def export_cut_list(self):
        return self.env.ref('cable_assembly.cable_assembly_cut_list_xlsx').report_action(self)

    def start_manufacturing(self):
        for rec in self:
            rec.x_time = datetime.datetime.now()
            rec.state = 'in_progress'
            task = self.env['project.task'].search([('id', '=', rec.x_task_id.id)])
            task.stage_id = 39

    def pause_manufacturing(self):
        for rec in self:
            if rec.x_time:
                time_difference = datetime.datetime.now() - rec.x_time
                total_seconds = time_difference.total_seconds()
                rec.x_hours += total_seconds / 3600
            rec.state = 'on_hold'
            task = self.env['project.task'].search([('id', '=', rec.x_task_id.id)])
            task.stage_id = 40

    def finish_manufacturing(self):
        for rec in self:
            if rec.x_time:
                time_difference = datetime.datetime.now() - rec.x_time
                total_seconds = time_difference.total_seconds()
                rec.x_hours += total_seconds / 3600
            rec.state = 'done'
            task = self.env['project.task'].search([('id', '=', rec.x_task_id.id)])
            task.stage_id = 41


class CableAssemblyDemandList(models.Model):
    _name = "cable.assembly.demand.list"
    _description = "Cable Assembly Demand List"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=False, readonly=True, )
    x_cable_assembly_id = fields.Many2one(comodel_name="cable.assembly", string="Cable Assembly ID", required=False, )
    x_product_demand_list_line_ids = fields.One2many(comodel_name="product.demand.list.line", string="Product Demand List lines", required=False,
                                                     inverse_name="x_cable_assembly_demand_list_id", compute="_update_product_demand_list", store=True, )
    x_connector_demand_list_line_ids = fields.One2many(comodel_name="connector.demand.list.line", string="Connector Demand List lines", required=False,
                                                       inverse_name="x_cable_assembly_demand_list_id", compute="_update_connector_demand_list", store=True, )
    x_wire_demand_list_line_ids = fields.One2many(comodel_name="wire.demand.list.line", string="Wire Demand List lines", required=False,
                                                  inverse_name="x_cable_assembly_demand_list_id", compute="_update_wire_demand_list", store=True, )
    x_harness_demand_list_line_ids = fields.One2many(comodel_name="cable.assembly.demand.list.line", string="Harness Demand List lines", required=False,
                                                     inverse_name="x_cable_assembly_demand_list_id", compute="_update_harness_demand_list", store=True, )

    @api.depends('x_cable_assembly_id.x_bom_ids')
    def _update_product_demand_list(self):
        for rec in self:
            rec.x_product_demand_list_line_ids.unlink()
            demand_list_lines = []
            products = []
            for bom_line in rec.x_cable_assembly_id.x_bom_ids:
                for line in bom_line.x_product_bom_id.x_bom_line_ids:
                    if line.x_start_product and line.x_start_product_id:
                        demand_list_line = [line.x_start_product.id,line.x_start_product_id.id,bom_line.id,bom_line.x_quantity]
                        if not demand_list_line in demand_list_lines:
                            demand_list_lines.append(demand_list_line)
                        if not line.x_start_product.id in products:
                            products.append(line.x_start_product.id)
                    if line.x_end_product and line.x_end_product_id:
                        demand_list_line = [line.x_end_product.id,line.x_end_product_id.id,bom_line.id,bom_line.x_quantity]
                        if not demand_list_line in demand_list_lines:
                            demand_list_lines.append(demand_list_line)
                        if not line.x_end_product.id in products:
                            products.append(line.x_end_product.id)

            for product in products:
                quantity = 0
                for demand_list_line in demand_list_lines:
                    if product == demand_list_line[0]:
                        quantity += demand_list_line[3]
                rec.x_product_demand_list_line_ids = [(0, 0, {
                    'x_name': product,
                    'x_quantity': quantity,
                })]

    @api.depends('x_cable_assembly_id.x_wiring_lines')
    def _update_connector_demand_list(self):
        for rec in self:
            rec.x_connector_demand_list_line_ids.unlink()

            demand_list_lines = []
            connectors = []
            for line in rec.x_cable_assembly_id.x_wiring_lines:
                if line.x_ref_des.x_start_connector.x_product_id:
                    demand_list_line = [line.x_ref_des.x_start_connector.x_product_id.id,line.x_quantity,line.x_ref_des.x_start_connector.x_name]
                    demand_list_lines.append(demand_list_line)
                    if not line.x_ref_des.x_start_connector.x_product_id.id in connectors:
                        connectors.append(line.x_ref_des.x_start_connector.x_product_id.id)
                if line.x_ref_des.x_end_connector.x_product_id:
                    demand_list_line = [line.x_ref_des.x_end_connector.x_product_id.id,line.x_quantity,line.x_ref_des.x_end_connector.x_name]
                    demand_list_lines.append(demand_list_line)
                    if not line.x_ref_des.x_end_connector.x_product_id.id in connectors:
                        connectors.append(line.x_ref_des.x_end_connector.x_product_id.id)

            for connector in connectors:
                label = ''
                quantity = 0
                for demand_list_line in demand_list_lines:
                    if connector == demand_list_line[0]:
                        quantity += demand_list_line[1]
                        label = demand_list_line[2]
                rec.x_connector_demand_list_line_ids = [(0, 0, {
                    'x_product_id': connector,
                    'x_label': label,
                    'x_required_qty': quantity,
                })]

    @api.depends('x_cable_assembly_id.x_wiring_lines')
    def _update_wire_demand_list(self):
        for rec in self:
            rec.x_wire_demand_list_line_ids.unlink()

            demand_list_lines = []
            wires = []
            for line in rec.x_cable_assembly_id.x_wiring_lines:
                if line.x_ref_des.x_wire.x_product_id and line.x_unit_length != 0:
                    demand_list_line = [line.x_ref_des.x_wire.x_product_id.id,line.x_quantity * line.x_unit_length,line.x_ref_des.x_wire.x_name]
                    demand_list_lines.append(demand_list_line)
                    if not line.x_ref_des.x_wire.x_product_id.id in wires:
                        wires.append(line.x_ref_des.x_wire.x_product_id.id)

            for wire in wires:
                label = ''
                quantity = 0
                for demand_list_line in demand_list_lines:
                    if wire == demand_list_line[0]:
                        quantity += demand_list_line[1]
                        label = demand_list_line[2]
                rec.x_wire_demand_list_line_ids = [(0, 0, {
                    'x_product_id': wire,
                    'x_label': label,
                    'x_required_qty': quantity,
                    'x_uom_id': rec.x_cable_assembly_id.x_uom_id.id,
                })]

    @api.depends('x_cable_assembly_id.x_wiring_lines')
    def _update_harness_demand_list(self):
        for rec in self:
            rec.x_harness_demand_list_line_ids.unlink()

            demand_list_lines = []
            for line in rec.x_cable_assembly_id.x_wiring_lines:
                if line.x_harness:
                    demand_list_line = [line.x_harness.id,line.x_quantity]
                    if not demand_list_line in demand_list_lines:
                        demand_list_lines.append(demand_list_line)

            for demand_list_line in demand_list_lines:
                rec.x_harness_demand_list_line_ids = [(0, 0, {
                    'x_harness_id': demand_list_line[0],
                    'x_quantity': demand_list_line[1],
                })]


class ProductDemandListLine(models.Model):
    _name = "product.demand.list.line"
    _description = "Product Demand List Line"
    _rec_name = "x_name"

    x_cable_assembly_demand_list_id = fields.Many2one(comodel_name="cable.assembly.demand.list", string="Demand List", )
    x_name = fields.Many2one(comodel_name="product.label", string="Product", required=False, )
    x_description = fields.Char(string="Description", required=False, related="x_name.x_description")

    x_quantity = fields.Float(string="Quantity",  required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", required=True, default=1, )


class ConnectorDemandListLine(models.Model):
    _name = "connector.demand.list.line"
    _description = "Connector Demand List Line"
    _rec_name = "x_label"

    x_cable_assembly_demand_list_id = fields.Many2one(comodel_name="cable.assembly.demand.list", string="Demand List", )

    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    x_label = fields.Char(string="Label", required=False, )
    x_description = fields.Text(string="Description", required=False, related="x_product_id.description")


    x_required_qty = fields.Float(string="Required Quantity",  required=False, )
    x_available_qty = fields.Float(string="Available Quantity",  required=False, related="x_product_id.qty_available", )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", default=1, )


class WireDemandListLine(models.Model):
    _name = "wire.demand.list.line"
    _description = "Wire Demand List Line"
    _rec_name = "x_label"

    x_cable_assembly_demand_list_id = fields.Many2one(comodel_name="cable.assembly.demand.list", string="Demand List", )

    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    x_label = fields.Char(string="Label", required=False, )
    x_description = fields.Text(string="Description", required=False, related="x_product_id.description", )

    x_required_qty = fields.Float(string="Required Length",  required=False, )
    x_available_qty = fields.Float(string="Available Length",  required=False, compute="_get_available_quantity", store=True, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", default=1, )

    @api.depends('x_product_id','x_uom_id')
    def _get_available_quantity(self):
        for rec in self:
            if rec.x_product_id and rec.x_uom_id:
                rec.x_available_qty = rec.x_product_id.qty_available / rec.x_product_id.uom_id.factor * rec.x_uom_id.factor


class CableAssemblyDemandListLine(models.Model):
    _name = "cable.assembly.demand.list.line"
    _description = "Cable Assembly Demand List Line"
    _rec_name = "x_harness_id"

    x_cable_assembly_demand_list_id = fields.Many2one(comodel_name="cable.assembly.demand.list", string="Demand List", )
    x_harness_id = fields.Many2one(comodel_name="harness", string="Harness", required=False, )
    x_quantity = fields.Float(string="Quantity",  required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", default=1, )


class CableAssemblyBOMList(models.Model):
    _name = "cable.assembly.bom.list"
    _description = "BOM List"
    _rec_name = "x_product_id"

    x_cable_assembly_id = fields.Many2one(comodel_name="cable.assembly", string="Cable Assembly", required=False, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True, )
    x_product_bom_id = fields.Many2one(comodel_name="cable.assembly.bom", string="Product BOM", required=True,
                                       domain="[('x_product_ids', 'ilike', x_product_id)]", )
    x_quantity = fields.Integer(string="Quantity", required=True, )


class CableAssemblyLine(models.Model):
    _name = "cable.assembly.line"
    _description = "Wiring Line"
    _order = "x_harness, x_ref_des"
    _rec_name = "x_ref_des"

    state = fields.Selection(string="Status", selection=[('new', 'New'), ('done', 'Done'), ], required=False, default="new")
    x_quantity = fields.Integer(string="Quantity", required=False, )
    x_cable_assembly_id = fields.Many2one(comodel_name="cable.assembly", string="Cable Assembly", required=False, )

    x_name = fields.Char(string="Name", required=False, )
    x_ref_des = fields.Many2one(comodel_name="cable.assembly.bom.line", string="Ref. Des.", required=False, )
    x_wire = fields.Many2one(comodel_name="wire.label", string="Wire", required=False, )
    x_unit_length = fields.Float(string="Unit Length",  required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", required=False, domain="[('category_id', '=', 4)]")

    x_harness = fields.Many2one(comodel_name="harness", string="Harness", required=False, )
    x_wire_core = fields.Many2one(comodel_name="wire.core", string="Wire Core", required=False, )
    x_start_label = fields.Boolean(string="Start Label",  )
    x_end_label = fields.Boolean(string="End Label",  )
    x_wire_label = fields.Boolean(string="Wire Label",  )
    x_core_label = fields.Boolean(string="Core Label",  )
    x_harness_label = fields.Boolean(string="Harness Label",  )
    x_notes = fields.Text(string="Notes", required=False, )

    x_start_connector = fields.Many2one(comodel_name="connector.label", string="Start Conn.", required=False, )
    x_start_heat_shrink_label = fields.Char(string="Start Label", required=False, )

    x_end_connector = fields.Many2one(comodel_name="connector.label", string="End Conn.", required=False, )
    x_end_heat_shrink_label = fields.Char(string="End Label", required=False, )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_cable_assembly_bom_line_id",
                                  string="Images", required=False, related="x_ref_des.x_image_ids")

    x_wire_color = fields.Selection(string="Wire Color", related='x_ref_des.x_wire_color')
    x_status = fields.Boolean(string="Done", compute="compute_status")

    @api.depends('state')
    def compute_status(self):
        for rec in self:
            if rec.state == 'done':
                rec.x_status = True
            else:
                rec.x_status = False

    def change_state_done(self):
        for record in self:
            if record.state == "new":
                record.state = "done"
                # for line in record.x_cable_assembly_id.x_wiring_lines:
                #     if line.x_harness.id == record.x_harness.id:
                #         line.state = "done"
            else:
                record.state = "new"
                # for line in record.x_cable_assembly_id.x_wiring_lines:
                #     if line.x_harness.id == record.x_harness.id:
                #         line.state = "new"


class CableAssemblyBOM(models.Model):
    _name = "cable.assembly.bom"
    _description = "Wiring BOM"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=False, )
    x_product_ids = fields.Many2many(comodel_name="product.product", relation="product_product_cable_assembly_bom_rel",
                                     column1="product_product_id", column2="cable_assembly_bom_id", string="Products", )
    x_bom_line_ids = fields.Many2many(comodel_name="cable.assembly.bom.line", relation="cable_assembly_bom_cable_assembly_bom_line_rel",
                                      column1="cable_assembly_bom_id", column2="bom_cable_assembly_bom_line_id", string="BOM Lines", )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_cable_assembly_bom_id", string="Images", required=False, )

    x_harness_ids = fields.Many2many(comodel_name="harness", relation="harness_cable_assembly_bom_rel",
                                     column1="harness_id", column2="cable_assembly_bom_id", string="Harnesses",
                                     compute="update_harness_boms", store=True, )

    _sql_constraints = [
        ('wiring_bom_name_unique',
         'unique(x_name)',
         'Wiring BoM name should be unique'),
    ]

    def copy(self, default=None):
        default = dict(default or {})

        # Generate a unique name for the duplicated BOM
        copied_count = self.search_count(
            [('x_name', '=like', u"Copy of {}%".format(self.x_name))]
        )
        if not copied_count:
            new_name = u"Copy of {}".format(self.x_name)
        else:
            new_name = u"Copy of {} ({})".format(self.x_name, copied_count)

        default['x_name'] = new_name

        # Duplicate related BOM lines
        if self.x_bom_line_ids:
            new_bom_lines = []
            for bom_line in self.x_bom_line_ids:
                # Call the copy method for each BOM line
                copied_line = bom_line.copy()
                new_bom_lines.append(copied_line.id)

            # Assign the duplicated lines to the new record
            default['x_bom_line_ids'] = [(6, 0, new_bom_lines)]

        return super(CableAssemblyBOM, self).copy(default)

    @api.model
    def create(self, vals_list):
        res = super(CableAssemblyBOM, self).create(vals_list)
        for rec in self:
            rec.x_bom_line_ids.update({'x_cable_assembly_bom_id': rec.id})
        return res

    def write(self, vals):
        res = super(CableAssemblyBOM, self).write(vals)
        for rec in self:
            rec.x_bom_line_ids.update({'x_cable_assembly_bom_id': rec.id})
        return res

    @api.depends('x_bom_line_ids')
    def update_harness_boms(self):
        for rec in self:
            for harness in rec.x_bom_line_ids.x_harness:
                rec.update_harness_bom_ids(harness)
            for harness in rec.x_harness_ids:
                rec.update_harness_bom_ids(harness)
            rec.x_harness_ids = rec.x_bom_line_ids.x_harness.ids

    def update_harness_bom_ids(self, harness_id):
        harness_id.x_bom_ids = [(5, 0, 0)]
        bom_ids = self.env['cable.assembly.bom'].search([])
        for bom in bom_ids:
            if harness_id.id in bom.x_bom_line_ids.x_harness.ids:
                harness_id.x_bom_ids = [(4, bom.id)]



class CableAssemblyBOMLine(models.Model):
    _name = "cable.assembly.bom.line"
    _description = "Wiring BOM Line"
    _rec_name = "x_ref_des"

    x_name = fields.Char(string="Wire Label", required=False, compute="wire_heat_shrink_label", store=True, )
    x_ref_des = fields.Char(string="Ref. Des.", required=False, readonly=True, )
    x_wire = fields.Many2one(comodel_name="wire.label", string="Wire", required=False, )
    x_wire_color = fields.Selection(selection=[
        ('black', 'Black'), ('blue', 'Blue'), ('green', 'Green'), ('red', 'Red'), ('yellow', 'Yellow'), ('grey', 'Grey')
    ], string='Wire Color', required=False, )

    x_unit_length = fields.Float(string="Unit Length",  required=False, )
    x_finished_length = fields.Float(string="Finished Length",  required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure", required=False,
                               domain="[('category_id', '=', 4)]", default=21)

    x_harness = fields.Many2one(comodel_name="harness", string="Harness", required=False, )
    x_wire_core = fields.Many2one(comodel_name="wire.core", string="Wire Core", required=False, )
    x_start_label = fields.Boolean(string="Start Label", )
    x_end_label = fields.Boolean(string="End Label", )
    x_wire_label = fields.Boolean(string="Wire Label", )
    x_core_label = fields.Boolean(string="Core Label", )
    x_harness_label = fields.Boolean(string="Harness Label", )
    x_notes = fields.Text(string="Notes", required=False, )

    x_start_product = fields.Many2one(comodel_name="product.label", string="Start Product", required=False, )
    x_start_product_code_ids = fields.Many2many(comodel_name="product.code", relation="product_code_product_label_rel_1",
                                                 column1="product_code_id", column2="product_label_id",
                                                 string="Codes", related="x_start_product.x_product_code_ids", )
    x_start_product_point_ids = fields.Many2many(comodel_name="product.point", relation="product_point_product_label_rel_1",
                                                 column1="product_point_id", column2="product_label_id",
                                                 string="Points", related="x_start_product.x_product_point_ids", )
    
    x_start_product_id = fields.Many2one(comodel_name="product.code", string="Start Product Label", required=False, domain="[('id', 'in', x_start_product_code_ids)]", )
    x_start_point_id = fields.Many2one(comodel_name="product.point", string="Start Point", required=False, domain="[('id', 'in', x_start_product_point_ids)]", )
    x_start_point_pin_ids = fields.Many2many(comodel_name="product.pin", relation="product_pin_product_point_rel_1",
                                               column1="product_pin_id", column2="product_point_id",
                                               string="Pins", related="x_start_point_id.x_pin_ids", )

    x_start_pin_id = fields.Many2one(comodel_name="product.pin", string="Start Pin", required=False, domain="[('id', 'in', x_start_point_pin_ids)]", )
    
    x_start_connector = fields.Many2one(comodel_name="connector.label", string="Start Conn.", required=False, )
    x_start_heat_shrink_label = fields.Char(string="Start Label", required=False, compute="start_heat_shrink_label", store=True, )

    x_end_product = fields.Many2one(comodel_name="product.label", string="End Product", required=False, )
    x_end_product_code_ids = fields.Many2many(comodel_name="product.code", relation="product_code_product_label_rel_1",
                                                 column1="product_code_id", column2="product_label_id",
                                                 string="Codes", related="x_end_product.x_product_code_ids", )
    x_end_product_point_ids = fields.Many2many(comodel_name="product.point",
                                                 relation="product_point_product_label_rel_1",
                                                 column1="product_point_id", column2="product_label_id",
                                                 string="Points", related="x_end_product.x_product_point_ids", )

    x_end_product_id = fields.Many2one(comodel_name="product.code", string="End Product Label", required=False, domain="[('id', 'in', x_end_product_code_ids)]", )
    x_end_point_id = fields.Many2one(comodel_name="product.point", string="End Point", required=False, domain="[('id', 'in', x_end_product_point_ids)]", )
    x_end_point_pin_ids = fields.Many2many(comodel_name="product.pin", relation="product_pin_product_point_rel_1",
                                             column1="product_pin_id", column2="product_point_id",
                                             string="Pins", related="x_end_point_id.x_pin_ids", )

    x_end_pin_id = fields.Many2one(comodel_name="product.pin", string="End Pin", required=False, domain="[('id', 'in', x_end_point_pin_ids)]", )

    x_end_connector = fields.Many2one(comodel_name="connector.label", string="End Conn.", required=False, )
    x_end_heat_shrink_label = fields.Char(string="End Label", required=False, compute="end_heat_shrink_label", store=True, )

    x_instruction_doc = fields.Binary(string="Instruction Doc",  )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_cable_assembly_bom_line_id", string="Images", required=False, )

    x_cable_assembly_bom_id = fields.Many2one('cable.assembly.bom', string='Cable Assembly BoM')

    # @api.depends('x_cable_assembly_bom_id.x_bom_line_ids')
    # def compute_cable_assembly_bom_id(self):
    #     for line in self:
    #         # Search for the BOM that contains this BOM line
    #         bom = self.env['cable.assembly.bom'].search([('x_bom_line_ids', 'in', line.id)], limit=1)
    #         # bom = self.env['cable.assembly.bom'].search([(line.id, 'in', 'x_bom_line_ids.ids')], limit=1)
    #         if bom:
    #             line.x_cable_assembly_bom_id = bom.id
    #         else:
    #             line.x_cable_assembly_bom_id = False


    @api.model
    def create(self, vals):
        vals['x_ref_des'] = self.env['ir.sequence'].next_by_code('cable.assembly.bom.line') or 'New'
        result = super(CableAssemblyBOMLine, self).create(vals)
        return result

    @api.depends('x_start_point_id', 'x_start_pin_id')
    def start_heat_shrink_label(self):
        for rec in self:
            if rec.x_start_point_id and rec.x_start_pin_id:
                rec.x_start_heat_shrink_label = rec.x_start_point_id.x_name + '.' + rec.x_start_pin_id.x_name
            elif rec.x_start_point_id and not rec.x_start_pin_id:
                rec.x_start_heat_shrink_label = rec.x_start_point_id.x_name
            elif not rec.x_start_point_id and rec.x_start_pin_id:
                rec.x_start_heat_shrink_label = rec.x_start_pin_id.x_name
            else:
                rec.x_start_heat_shrink_label = ''

    @api.depends('x_end_point_id', 'x_end_pin_id')
    def end_heat_shrink_label(self):
        for rec in self:
            if rec.x_end_point_id and rec.x_end_pin_id:
                rec.x_end_heat_shrink_label = rec.x_end_point_id.x_name + '.' + rec.x_end_pin_id.x_name
            elif rec.x_end_point_id and not rec.x_end_pin_id:
                rec.x_end_heat_shrink_label = rec.x_end_point_id.x_name
            elif not rec.x_end_point_id and rec.x_end_pin_id:
                rec.x_end_heat_shrink_label = rec.x_end_pin_id.x_name
            else:
                rec.x_end_heat_shrink_label = ''

    @api.onchange('x_start_product_id')
    def _update_start_product_label(self):
        for rec in self:
            if rec.x_start_product and rec.x_start_product_id:
                if not rec.x_start_product_id in rec.x_start_product.x_product_code_ids:
                    rec.x_start_product.x_product_code_ids = [(4, rec.x_start_product_id.id)]

    @api.onchange('x_start_point_id')
    def _update_start_point(self):
        for rec in self:
            if rec.x_start_product and rec.x_start_point_id:
                if not rec.x_start_point_id in rec.x_start_product.x_product_point_ids:
                    rec.x_start_product.x_product_point_ids = [(4, rec.x_start_point_id.id)]

    @api.onchange('x_start_pin_id')
    def _update_start_pin(self):
        for rec in self:
            if rec.x_start_point_id and rec.x_start_pin_id:
                if not rec.x_start_pin_id in rec.x_start_point_id.x_pin_ids:
                    rec.x_start_point_id.x_pin_ids = [(4, rec.x_start_pin_id.id)]

    @api.onchange('x_end_product_id')
    def _update_end_product_label(self):
        for rec in self:
            if rec.x_end_product and rec.x_end_product_id:
                if not rec.x_end_product_id in rec.x_end_product.x_product_code_ids:
                    rec.x_end_product.x_product_code_ids = [(4, rec.x_end_product_id.id)]

    @api.onchange('x_end_point_id')
    def _update_end_point(self):
        for rec in self:
            if rec.x_end_product and rec.x_end_point_id:
                if not rec.x_end_point_id in rec.x_end_product.x_product_point_ids:
                    rec.x_end_product.x_product_point_ids = [(4, rec.x_end_point_id.id)]

    @api.onchange('x_end_pin_id')
    def _update_end_pin(self):
        for rec in self:
            if rec.x_end_point_id and rec.x_end_pin_id:
                if not rec.x_end_pin_id in rec.x_end_point_id.x_pin_ids:
                    rec.x_end_point_id.x_pin_ids = [(4, rec.x_end_pin_id.id)]

    @api.depends('x_start_product_id', 'x_start_heat_shrink_label', 'x_end_product_id', 'x_end_heat_shrink_label', )
    def wire_heat_shrink_label(self):
        for rec in self:
            if rec.x_start_product_id and rec.x_end_product_id:
                rec.x_name = rec.x_start_product_id.x_name + '(' + str(rec.x_start_heat_shrink_label) + ')>>' + \
                             rec.x_end_product_id.x_name + '(' + str(rec.x_end_heat_shrink_label) + ')'
            elif rec.x_start_product_id and not rec.x_end_product_id:
                rec.x_name = rec.x_start_product_id.x_name + '(' + str(rec.x_start_heat_shrink_label) + ')'
            elif not rec.x_start_product_id and rec.x_end_product_id:
                rec.x_name = rec.x_end_product_id.x_name + '(' + str(rec.x_end_heat_shrink_label) + ')'

    @api.constrains('x_harness')
    def _update_harness_wiring_lines(self):
        for harness in self.env['harness'].search([]):
            lines = self.env['cable.assembly.bom.line'].search([('x_harness', '=', harness.id)]).mapped('id')
            harness.x_wiring_line_ids = [(6, 0, lines)]


class Harness(models.Model):
    _name = "harness"
    _description = "Harness"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=False, readonly=True, copy=False, default="New")
    x_printer = fields.Selection(string="Printer", selection=[('E800TK', 'E800TK'), ('P600', 'P600'), ], required=False, )
    x_instruction_doc = fields.Binary(string="Instruction Docs", )
    x_notes = fields.Text(string="Notes", required=False, )
    x_start_label = fields.Boolean(string="Start Label", )
    x_end_label = fields.Boolean(string="End Label", )
    x_wire_label = fields.Boolean(string="Wire Label", )
    x_harness_label = fields.Boolean(string="Harness Label", )
    x_onenote_link = fields.Char(string="Onenote Link", required=False, )
    x_wiring_line_ids = fields.Many2many(comodel_name="cable.assembly.bom.line",
                                         relation="harness_cable_assembly_bom_line_rel",
                                         column1="harness_id", column2="cable_assembly_bom_line_id",
                                         string="Wiring Lines", )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_harness_id", string="Images", required=False, )
    x_bom_ids = fields.Many2many(comodel_name="cable.assembly.bom", relation="harness_cable_assembly_bom_rel",
                                 column1="cable_assembly_bom_id", column2="harness_id", string="BOMs", )

    @api.model
    def create(self, vals):
        if vals.get('x_name', 'New') == 'New':
            vals['x_name'] = self.env['ir.sequence'].next_by_code('cable.assembly.harness') or 'New'
        result = super(Harness, self).create(vals)
        return result

    @api.onchange('x_start_label', 'x_end_label', 'x_wire_label', 'x_harness_label')
    def update_bom_line_status(self):
        for rec in self:
            for line in rec.x_wiring_line_ids:
                line.x_start_label = rec.x_start_label
                line.x_end_label = rec.x_end_label
                line.x_wire_label = rec.x_wire_label
                line.x_harness_label = rec.x_harness_label

    @api.onchange('x_wiring_line_ids')
    def update_bom_line_harness(self):
        for rec in self:
            lines = self.env['cable.assembly.bom.line'].search([('x_harness', '=', rec._origin.id)])
            for line in lines:
                if not line.id in rec.x_wiring_line_ids.ids:
                    line.x_harness = False
            for line in rec.x_wiring_line_ids:
                line.x_harness = rec._origin.id

    @api.constrains('x_name')
    def _check_name(self):
        for rec in self:
            names = self.env['harness'].search([('id', '!=', rec.id)]).mapped('x_name')
            if rec.x_name in names:
                raise UserError(_("Harness name already exist."))


class WireCore(models.Model):
    _name = "wire.core"
    _description = "Wire Core"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=False, )
    x_notes = fields.Text(string="Notes", required=False, )
    x_start_label = fields.Boolean(string="Start Label",  )
    x_end_label = fields.Boolean(string="End Label",  )
    x_wire_label = fields.Boolean(string="Wire Label",  )
    x_core_label = fields.Boolean(string="Core Label",  )
    x_onenote_link = fields.Char(string="Onenote Link", required=False, )
    x_wiring_line_ids = fields.Many2many(comodel_name="cable.assembly.bom.line", relation="wire_core_cable_assembly_bom_line_rel",
                                         column1="wire_core_id", column2="cable_assembly_bom_line_id", string="Wiring Lines", )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_wire_core_id", string="Images", required=False, )

    @api.onchange('x_start_label', 'x_end_label', 'x_wire_label', 'x_core_label')
    def update_bom_line_status(self):
        for rec in self:
            for line in rec.x_wiring_line_ids:
                line.x_start_label = rec.x_start_label
                line.x_end_label = rec.x_end_label
                line.x_wire_label = rec.x_wire_label
                line.x_core_label = rec.x_core_label

    @api.onchange('x_wiring_line_ids')
    def update_bom_line_core(self):
        for rec in self:
            lines = self.env['cable.assembly.bom.line'].search([('x_wire_core', '=', rec._origin.id)])
            for line in lines:
                if not line.id in rec.x_wiring_line_ids.ids:
                    line.x_wire_core = False
            for line in rec.x_wiring_line_ids:
                line.x_wire_core = rec._origin.id

    @api.constrains('x_name')
    def _check_name(self):
        for rec in self:
            names = self.env['wire.core'].search([('id', '!=', rec.id)]).mapped('x_name')
            if rec.x_name in names:
                raise UserError(_("Core name already exist."))


class ProductLabel(models.Model):
    _name = "product.label"
    _description = "Product Label"
    _rec_name = "x_name"
    _order = "x_sequence"

    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_name = fields.Char(string="Product Name", required=True, )
    x_description = fields.Char(string="Product Description", required=False, )
    x_label_required = fields.Boolean(string="Label Required?",  )
    x_product_code_ids = fields.Many2many(comodel_name="product.code", relation="product_code_product_label_rel",
                                          column1="product_code_id", column2="product_label_id", string="Product Codes", )
    x_product_point_ids = fields.Many2many(comodel_name="product.point", relation="product_point_product_label_rel",
                                           column1="product_point_id", column2="product_label_id", string="Points", )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_product_label_id", string="Images", required=False, )


class ProductCode(models.Model):
    _name = "product.code"
    _description = "Product Code"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Product Code", required=True, )


class ProductPoint(models.Model):
    _name = "product.point"
    _description = "Product Points"
    _rec_name = "x_point_name"
    _order = "x_name"

    x_name = fields.Char(string="Point", required=True, )
    x_point_desc = fields.Char(string="Point Desc", required=False, )
    x_pin_ids = fields.Many2many(comodel_name="product.pin", relation="product_pin_product_point_rel",
                                 column1="product_pin_id", column2="product_point_id", string="Pins", )
    x_point_name = fields.Char(string="Name", required=False, compute="_compute_point_name", store=True, )

    @api.depends('x_name','x_point_desc','x_pin_ids')
    def _compute_point_name(self):
        for rec in self:
            if rec.x_name:
                rec.x_point_name = rec.x_name
            if rec.x_point_desc:
                rec.x_point_name += ' (' + rec.x_point_desc + ')'
            if rec.x_pin_ids:
                rec.x_point_name += ' ['
                for pin in rec.x_pin_ids:
                    rec.x_point_name += pin.x_name + ','
                rec.x_point_name += ']'


class ProductPin(models.Model):
    _name = "product.pin"
    _description = "Product Pin"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Pin Name", required=True, )


class ConnectorLabel(models.Model):
    _name = "connector.label"
    _description = "Connector Label"
    _rec_name = "x_name"

    x_name = fields.Char(string="Connector Short Code", required=True, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Connector Model#", required=False, )
    x_printer = fields.Selection(string="Printer", selection=[('E800TK', 'E800TK'), ('P600', 'P600'), ], required=False, )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_connector_label_id", string="Images", required=False, )


class WireLabel(models.Model):
    _name = "wire.label"
    _description = "Wire Label"
    _rec_name = "x_name"

    x_name = fields.Char(string="Wire Short Code", required=True, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Wire Model#", required=False, )
    x_printer = fields.Selection(string="Printer", selection=[('E800TK', 'E800TK'), ('P600', 'P600'), ], required=False, )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_wire_label_id", string="Images", required=False, )


class Images(models.Model):
    _inherit = "odoo.image"

    x_cable_assembly_id = fields.Many2one(comodel_name="cable.assembly", string="Cable Assembly ID", required=False, )
    x_cable_assembly_bom_id = fields.Many2one(comodel_name="cable.assembly.bom", string="Cable Assembly BOM ID", required=False, )
    x_cable_assembly_bom_line_id = fields.Many2one(comodel_name="cable.assembly.bom.line", string="Cable Assembly BOM Line ID", required=False, )
    x_wire_core_id = fields.Many2one(comodel_name="wire.core", string="Wire Core ID", required=False, )
    x_harness_id = fields.Many2one(comodel_name="harness", string="Harness ID", required=False, )
    x_product_label_id = fields.Many2one(comodel_name="product.label", string="Product Label ID", required=False, )
    x_connector_label_id = fields.Many2one(comodel_name="connector.label", string="Connector Label ID", required=False, )
    x_wire_label_id = fields.Many2one(comodel_name="wire.label", string="Wire Label ID", required=False, )


