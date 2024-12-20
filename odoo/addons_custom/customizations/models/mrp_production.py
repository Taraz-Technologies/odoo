from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from datetime import date

import datetime
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    x_investor_product = fields.Boolean(string='Investor Product?')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    x_serial_numbers = fields.One2many("serial.number", inverse_name="x_manufacturing_id", string="Serial #")

    x_unit_cost = fields.Float(string="Unit Cost", required=False, compute="_calculate_unit_cost", store=True)

    x_product_journal_entry = fields.Many2many(comodel_name="account.move", relation="account_move_mrp_production_rel_1",
                                               column1="mrp_production_id", column2="account_move_id",
                                               compute="_get_journal_entries", string="Product Journal Entries", )
    x_raw_journal_entries = fields.Many2many(comodel_name="account.move", relation="account_move_mrp_production_rel_2",
                                             column1="mrp_production_id", column2="account_move_id",
                                             compute="_get_journal_entries", string="Raw Material Journal Entries",)

    x_stencil = fields.Char(string="Stencil", compute="get_stencil", store=True)

    x_pcb_sides = fields.Selection(string="PCB Sides", selection=[('1', '1'), ('2', '2'), ], required=False, )
    x_assembly_type = fields.Selection(selection=[
        ('TH', 'TH'), ('SMD', 'SMD'), ('Other', 'Other'),
    ], string="Assembly Type", required=False, )
    x_placement_type = fields.Selection(selection=[
        ('Manual', 'Manual'), ('Machine', 'Machine'),
    ], string="Placement Type", required=False, )

    x_acrylic_exist = fields.Boolean(string="Acrylic Exist?", )
    x_local_procurement = fields.Boolean(string="Local Procurement?", )
    x_outdoor_fabrication = fields.Boolean(string="Outdoor Fabrication?", )

    x_product_group = fields.Char(string="Product Group", required=False, related="product_id.x_product_group.name", )
    x_product_series = fields.Char(string="Product Series", related="product_id.x_product_series.display_name", )
    x_product_division = fields.Char(string="Product Division", related="product_id.x_product_division.display_name", )
    x_product_category = fields.Char(string="Product Category", related="product_id.categ_id.display_name", )
    x_project = fields.Selection(string="Project", selection=[('MO Tracking', 'MO Tracking'), ], default='MO Tracking')
    x_description = fields.Text(string="Description", required=False, )
    x_checklist = fields.Text(string="Checklist", required=False, )

    x_checklist_items = fields.Many2many(comodel_name="checklist.items", relation="mrp_production_checklist_items_rel",
                                         column1="mrp_production_id", column2="checklist_items_id", string="Checklist")

    x_responsible_person = fields.Many2one(comodel_name="hr.employee", string="Responsible person", default=57, )
    x_participants = fields.Many2many(comodel_name="hr.employee", relation="hr_employee_mrp_production_rel_1",
                                      column1="mrp_production_id", column2="hr_employee_id", string="Participants", )
    x_observers = fields.Many2many(comodel_name="hr.employee", relation="hr_employee_mrp_production_rel_2",
                                   column1="mrp_production_id", column2="hr_employee_id", string="Observers",
                                   default=[37, 38, 53, 56])

    # -------------------------------------- Project Task --------------------------------------
    x_task_id = fields.Many2one(comodel_name="project.task", string="Task", required=False, )
    x_task_stage_id = fields.Many2one(related="x_task_id.stage_id")
    x_task_name = fields.Char(string="Name", required=False, )
    x_user_responsible = fields.Many2one(comodel_name="res.users", string="Responsible User", default=28, )
    x_user_participants = fields.Many2many(comodel_name="res.users", relation="res_users_mrp_production_rel_1",
                                           column1="mrp_production_id", column2="res_users_id", string="Participants", )
    x_user_observers = fields.Many2many(comodel_name="res.users", relation="res_users_mrp_production_rel_2",
                                        column1="mrp_production_id", column2="res_users_id", string="Observers")
    x_start_task_on = fields.Datetime(string="Start task on", required=False, )
    x_deadline = fields.Datetime(string="Deadline", required=False, )
    x_processes = fields.Many2many(comodel_name="processes", relation="mrp_production_processes_rel",
                                   column1="mrp_production_id", column2="processes_id", string="Processes", )
    x_notes = fields.Text(string="Notes", required=False, )
    x_tasks = fields.Many2many(comodel_name="tasks", relation="mrp_production_tasks_rel", column1="mrp_production_id",
                               column2="tasks_id", string="Task", )

    def write(self, vals):
        old_values = self.x_tag_ids.ids
        res = super(MrpProduction, self).write(vals)
        new_values = self.x_tag_ids.ids
        if 'x_tag_ids' in vals:
            self.x_tag_ids._track_many2many_changes(
                self, 'x_tag_ids', old_values=old_values, new_values=new_values
            )
        return res

    @api.depends('move_finished_ids', 'move_finished_ids.stock_valuation_layer_ids.unit_cost')
    def _calculate_unit_cost(self):
        for rec in self:
            move_finished_ids = rec.move_finished_ids.filtered(lambda f: f.state == 'done')
            if move_finished_ids:
                if move_finished_ids[0].stock_valuation_layer_ids:
                    rec.x_unit_cost = move_finished_ids[0].stock_valuation_layer_ids[0].unit_cost
            else:
                rec.x_unit_cost = 0

    @api.depends('state')
    def _get_journal_entries(self):
        for rec in self:
            if rec.state in ('progress', 'done'):
                rec.x_product_journal_entry = [(6, 0, rec.move_finished_ids.mapped('account_move_ids').ids)]
                rec.x_raw_journal_entries = [(6, 0, rec.move_raw_ids.mapped('account_move_ids').ids)]
            else:
                rec.x_product_journal_entry = False
                rec.x_raw_journal_entries = False

    @api.depends('bom_id')
    def get_stencil(self):
        for rec in self:
            stencil = False
            if rec.bom_id:
                bom_line_id = rec.bom_id.bom_line_ids.filtered(lambda l: 'PCB-' == l.product_id.name[0:3])
                if bom_line_id:
                    stencil_name = 'Stencil-' + str(bom_line_id.product_id.name)
                    domain = ['|', ('name', '=', stencil_name), ('description', 'ilike', bom_line_id.product_id.name)]
                    stencil = self.env['product.template'].search(domain, limit=1, order="create_date desc").name
            rec.x_stencil = stencil

    @api.onchange('name', 'product_id', 'product_qty', 'x_product_category', 'x_description')
    def update_task_name(self):
        for rec in self:
            if rec.name and rec.product_id and rec.product_qty:
                rec.x_task_name = '[' + rec.name + '] [' + rec.product_id.name + '] [Qty: ' + str(rec.product_qty) + ']'

            if rec.x_product_category:
                if '[SFG]' in rec.x_product_category:
                    rec.x_task_name = str(rec.x_task_name) + ' [SFG]'
                if '[FG]' in rec.x_product_category:
                    rec.x_task_name = str(rec.x_task_name) + ' [FG]'

            if rec.x_description:
                if 'Stock Build' in rec.x_description:
                    rec.x_task_name = str(rec.x_task_name) + ' [StockBuild]'

    @api.onchange('product_qty', 'x_tasks')
    def update_task_description(self):
        for record in self:
            quantity = record.product_qty
            if quantity > 0:
                if not record.x_description:
                    record.x_description = 'Stock Build [x' + str(quantity) + ']'
                elif record.x_description != '':
                    record.x_description = record.x_description + '\nStock Build [x' + str(quantity) + ']'

            for task in record.x_tasks:
                if not record.x_description:
                    record.x_description = '[Task: ' + task.x_name + ']'
                elif record.x_description != '':
                    record.x_description = record.x_description + '\n[Task: ' + str(task.x_name) + ']'

    @api.onchange('date_planned_start', 'date_planned_finished')
    def update_task_dates(self):
        for record in self:
            if record.date_planned_start:
                record.x_start_task_on = record.date_planned_start
                record.x_deadline = record.date_planned_finished

    @api.onchange('x_checklist_items')
    def update_task_checklist(self):
        for record in self:
            record.x_checklist = ''
            for checklist in record.x_checklist_items:
                if not record.x_checklist:
                    record.x_checklist = '[*]' + checklist.x_name
                else:
                    record.x_checklist = record.x_checklist + '\n[*]' + checklist.x_name

    @api.onchange('x_processes')
    def update_task_list(self):
        for record in self:
            record.x_tasks = [(5, 0, 0)]
            for process in record.x_processes:
                for task in process.x_tasks:
                    add00 = True

                    add01 = False
                    add02 = False
                    add03 = False
                    add04 = False
                    add05 = False
                    add06 = False
                    add07 = False
                    add08 = False
                    add09 = False
                    add10 = False

                    for condition in task.x_conditions:
                        if condition.x_model.model == record._name:
                            condition_field = condition.x_field_id.name

                            for model in self.env['ir.model'].search([('model', '=', record._name)]):
                                for field in model.field_id:
                                    if field.name == condition_field:
                                        condition_value = ''
                                        condition_value = condition.x_value
                                        field_value = ''
                                        field_value = record[condition_field]

                                        if field.ttype == 'many2one':
                                            if record[condition_field].name:
                                                field_value = record[condition_field].name

                                        if task.x_check == 'All':
                                            if condition.x_relation == 'equals':
                                                if record[condition_field]:
                                                    if field_value != condition_value:
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'not equals':
                                                if record[condition_field]:
                                                    if field_value == condition_value:
                                                        add00 = False
                                                elif not record[condition_field] and condition_value == '':
                                                    add00 = False
                                            elif condition.x_relation == 'is set':
                                                if not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is not set':
                                                if record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'contains':
                                                if record[condition_field] and condition_value:
                                                    if not condition_value in field_value:
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'does not contain':
                                                if record[condition_field] and condition_value:
                                                    if condition_value in field_value:
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is greater than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) >= int(field_value):
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is less than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) <= int(field_value):
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is greater than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) > int(field_value):
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is less than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) < int(field_value):
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                        elif task.x_check == 'Any':
                                            if condition.x_relation == 'equals':
                                                if record[condition_field] and condition_value:
                                                    if field_value == condition_value:
                                                        add01 = True
                                                        break
                                                elif not record[condition_field] and not condition_value:
                                                    add01 = True
                                                    break
                                            elif condition.x_relation == 'not equals':
                                                if record[condition_field] and condition_value:
                                                    if field_value != condition_value:
                                                        add02 = True
                                                        break
                                                elif not record[condition_field] and condition_value:
                                                    add02 = True
                                                    break
                                                elif record[condition_field] and not condition_value:
                                                    add02 = True
                                                    break
                                            elif condition.x_relation == 'is set':
                                                if record[condition_field]:
                                                    add03 = True
                                                    break
                                            elif condition.x_relation == 'is not set':
                                                if not record[condition_field]:
                                                    add04 = True
                                                    break
                                            elif condition.x_relation == 'contains':
                                                if record[condition_field] and condition_value:
                                                    if condition_value in field_value:
                                                        add06 = True
                                                        break
                                                elif not record[condition_field] and not condition_value:
                                                    add06 = True
                                                    break
                                                elif record[condition_field] and not condition_value:
                                                    add06 = True
                                                    break
                                            elif condition.x_relation == 'does not contain':
                                                if record[condition_field] and condition_value:
                                                    if not condition_value in field_value:
                                                        add06 = True
                                                        break
                                                elif not record[condition_field] and condition_value:
                                                    add06 = True
                                                    break
                                            elif condition.x_relation == 'is greater than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) < int(field_value):
                                                        add07 = True
                                                        break
                                                elif record[condition_field]:
                                                    add07 = True
                                                    break
                                            elif condition.x_relation == 'is less than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) > int(field_value):
                                                        add08 = True
                                                        break
                                                elif not record[condition_field]:
                                                    add08 = True
                                                    break
                                            elif condition.x_relation == 'is greater than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) <= int(field_value):
                                                        add09 = True
                                                        break
                                                elif record[condition_field]:
                                                    add09 = True
                                                    break
                                            elif condition.x_relation == 'is less than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) >= int(field_value):
                                                        add10 = True
                                                        break
                                                elif not record[condition_field]:
                                                    add10 = True
                                                    break
                                if (
                                        add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                                    break
                        if (
                                add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                            break

                    if add00 and task.x_check == 'All':
                        task.x_task_name = '[' + str(process.x_name) + '] [' + str(task.x_name) + '] ' + str(
                            record.x_task_name)
                        if record.date_planned_start:
                            task.x_start_task_on = record.date_planned_start
                        if task.x_has_deadline:
                            task.x_deadline = record.date_planned_start + datetime.timedelta(task.x_per_unit_time / 24)
                        else:
                            task.x_deadline = ''

                        record.x_tasks = [(4, task.id)]

                    elif (
                            add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                        task.x_task_name = '[' + str(process.x_name) + '] [' + str(task.x_name) + '] ' + str(
                            record.x_task_name)
                        if record.date_planned_start:
                            task.x_start_task_on = record.date_planned_start
                        if task.x_has_deadline:
                            task.x_deadline = record.date_planned_start + datetime.timedelta(task.x_per_unit_time / 24)
                        else:
                            task.x_deadline = ''

                        record.x_tasks = [(4, task.id)]

    def update_task_data(self):
        for record in self:
            record.update_task_name()
            record.update_task_description()
            record.update_task_dates()
            record.update_task_checklist()
            record.update_task_list()


class SaleOrderList(models.Model):
    _name = 'sale.order.list'
    _description = 'Sale Order List'
    _rec_name = "x_sale_order_number"
    _order = 'x_sequence'

    x_sequence = fields.Integer(string='Sequence', required=False)
    x_manufacturing_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing", required=False, )
    x_sale_order_number = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False)
    x_folder_name = fields.Char(related="x_sale_order_number.x_folder_name")
    x_deadline = fields.Datetime(ralated="x_sale_order_number.x_deadline")
    x_quantity = fields.Float(string="Quantity", digits='Product Unit of Measure')


class MegaMOsList(models.Model):
    _name = 'mega.mos.list'
    _description = 'Mega MOs List'

    x_manufacturing_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing", required=False)
    x_mega_mo_number = fields.Many2one(comodel_name="mrp.production", string="Master Order", required=False)
    x_product_id = fields.Many2one(related='x_mega_mo_number.product_id')
    x_product_category = fields.Many2one(related='x_mega_mo_number.product_id.categ_id')
    x_quantity = fields.Float(string="Quantity", digits='Product Unit of Measure')


class SerialNumber(models.Model):
    _name = 'serial.number'
    _description = "Serial Number"
    _rec_name = "x_sale_order_number"

    x_manufacturing_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing", required=False, )
    x_product_id = fields.Many2one(related='x_manufacturing_id.product_id')
    x_mega_mo_number = fields.Many2one(comodel_name="mrp.production", string="Master Order", required=False)
    x_sale_order_number = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False)
    x_serial_number = fields.Char(string="Serial #", required=False)


