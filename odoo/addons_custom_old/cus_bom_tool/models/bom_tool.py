from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import html_escape as escape

import re
import datetime
import logging

_logger = logging.getLogger("*__addons_custom__*")

SUBTASK_STATES = {
    "done": "Done",
    "todo": "TODO",
}


class BomTool(models.Model):
    _name = "bom.tool"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "BoM Tool"
    _rec_name = "x_name"

    @api.model
    def _read_group_user_state(self, stages, domain, order):
        return ['draft', 'to_be_review', 'active', 'inactive']

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('to_be_review', 'To be Reviewed'), ('active', 'Active'), ('inactive', 'Inactive'),
    ], string='Status', default='draft', tracking=True, group_expand='_read_group_user_state')

    x_task_id = fields.Many2one(comodel_name='project.task', string='Task', compute='create_task', store=True)
    x_name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                         default=lambda self: _('New'))
    x_finished_good = fields.Selection(selection=[
        ('finished', 'Finished Good'), ('semi_finished', 'Semi-Finished Good'),
    ], string='Product Type', default='finished', required=True, tracking=True)
    x_product_type_fg = fields.Selection(selection=[
        ('system', 'System'), ('pcb', 'PCB Module'),
    ], string='FG Type', default='pcb', required=True, tracking=True)
    x_product_type_sfg = fields.Selection(selection=[
        ('pcb', 'PCB Module'), ('cable', 'CBL Assembly'), ('mechanical', 'MECH Assembly'), ('other', 'Other Assembly'),
        ('inductor', 'Inductor'), ('transformer', 'Transformer'),
    ], string='SFG Type', default='cable', required=True, tracking=True)

    x_base_product_prefix = fields.Char(string='Base Product Prefix', compute='_compute_name_prefix', store=True)
    x_base_product_name = fields.Char(string='Product Name', required=True, tracking=True)
    x_base_product_id = fields.Many2one(comodel_name='product.template', string='Product',
                                        compute='_compute_base_product', store=True, tracking=True)

    image_1920 = fields.Image(related='x_base_product_id.image_1920', string="Image", readonly=False, store=True)

    x_product_variants = fields.Boolean(
        string='Variants?',
        required=False,
        tracking=True)
    x_enable_safety_stock = fields.Boolean(
        string='Enable Safety Stock',
        required=False,
        tracking=True)

    @api.onchange('x_enable_safety_stock')
    def onchange_enable_safety_stock(self):
        for rec in self:
            if rec.x_enable_safety_stock:
                rec.x_base_bom_id.x_bom_line_ids.mapped('x_taraz_part_id').update({
                    'x_enable_safety_stock': True, 'x_consider_compromised': True,
                })
            else:
                bom_line_ids = self.env['bom.tool'].search([
                    ('x_enable_safety_stock', '!=', False), ('id', '!=', rec._origin.id)
                ]).mapped('x_base_bom_id').mapped('x_bom_line_ids')
                taraz_part_ids = rec.x_base_bom_id.x_bom_line_ids.mapped('x_taraz_part_id')
                for taraz_part_id in taraz_part_ids:
                    if not bom_line_ids.filtered(lambda l: l.x_taraz_part_id.id == taraz_part_id.id):
                        taraz_part_id.x_enable_safety_stock = False
                        taraz_part_id.x_consider_compromised = False

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    # BoM Tool
    x_team_lead_id = fields.Many2one(comodel_name='res.users', string='Team Lead', tracking=True, default=19)
    x_team_member_ids = fields.Many2many(comodel_name='res.users', string='Team Members')
    x_bom_tool_description = fields.Text(string="Description", required=False, tracking=True)

    x_bom_tool_checklist = fields.One2many(comodel_name='bom.tool.check.list', inverse_name='x_bom_tool_id',
                                           string='BoM TOOL CHECKLIST', required=False)
    x_bom_tool_bom_ids = fields.Many2many(comodel_name='base.bom', relation='base_bom_bom_tool_rel_2',
                                          column1='base_bom_id', column2='bom_tool_id', string='BoM Tool BoMs', )
    x_compute_bom_tool_boms = fields.Boolean(string='Compute Product Name', store=True,
                                             compute='_compute_bom_tool_boms')

    # Base BoM
    x_base_bom_id = fields.Many2one(comodel_name='base.bom', string='BoM Version',
                                    domain="[('x_product_id', '=', x_base_product_id)]")
    x_routing_id = fields.Many2one(
        comodel_name='mrp.routing', string='BoM Routing',
        related='x_base_bom_id.x_routing_id', store=True, readonly=False,
        check_company = True, tracking = True, company_dependent = True,
        help="The list of operations to produce the finished product. The routing is mainly used to "
             "compute work center costs during operations and to plan future loads on work centers "
             "based on production planning.")

    @api.onchange('x_routing_id')
    def onchange_routing_id(self):
        for rec in self:
            for line in rec.x_base_bom_id.x_bom_line_ids:
                operation_id = rec.x_routing_id.operation_ids.filtered(
                    lambda o: o.workcenter_id.x_mounting_type == line.x_type
                )
                line.x_operation_id = operation_id[0].id if operation_id else False

    x_base_bom_line_count = fields.Integer(string='BoM Lines Count', required=False)
    x_attached_block_ids = fields.One2many(comodel_name='bom.tool.blocks', inverse_name='x_bom_tool_id',
                                           string='BoM Blocks', required=False)

    x_search_base_bom_lines = fields.Char(string='Search Lines', required=False)

    x_select_base_bom_lines = fields.Boolean(string='Select All', required=False)
    x_compute_base_selection = fields.Boolean(string='Select', compute='_compute_base_selection', store=True)

    x_filter_base_bom_lines = fields.Selection(selection=[
        ('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER'), ('undefined', 'Undefined'), ('all', 'ALL')
    ], string='Filter Line Type', default='all')

    x_undefined_base_bom_lines = fields.Boolean(string='Undefined', required=False)
    x_dnp_base_bom_lines = fields.Boolean(string='DNP', required=False)
    x_non_dnp_base_bom_lines = fields.Boolean(string='NON DNP', required=False)
    x_critical_base_bom_lines = fields.Boolean(string='CRITICAL', required=False)
    x_variant_base_bom_lines = fields.Boolean(string='VAR', required=False)
    x_investor_base_bom_lines = fields.Boolean(string='IP', required=False)

    x_new_design_base_bom_lines = fields.Boolean(string='New Lines', required=False)
    x_modified_design_base_bom_lines = fields.Boolean(string='Modified', required=False)
    x_deleted_design_base_bom_lines = fields.Boolean(string='Deleted', required=False)

    x_new_base_bom_lines = fields.Boolean(string='New Lines', required=False)
    x_modified_base_bom_lines = fields.Boolean(string='Modified', required=False)
    x_deleted_base_bom_lines = fields.Boolean(string='Deleted', required=False)
    x_moved_base_bom_lines = fields.Boolean(string='Moved', required=False)

    x_bom_line_product_id = fields.Many2one(comodel_name='product.template', string='Update Lines Part #')
    x_operation_id = fields.Many2one(
        comodel_name='mrp.routing.workcenter', string='Update Line Operation',
        check_company=True, company_dependent=True, domain="[('routing_id', '=', x_routing_id)]",
        help="The operation where the components are consumed, or the finished products created.")
    x_bom_line_notes = fields.Char(string='Update Lines Notes')
    x_move_to_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='Move Lines to', domain="[('id', '!=', id)]")

    x_bom_line_ids = fields.Many2many('base.bom.lines', 'base_bom_lines_bom_tool_rel_1',
                                      'base_bom_lines_id', 'bom_tool_id', 'BoM lines')

    # Product Variants
    x_product_tag_id = fields.Many2one(comodel_name='bom.tool.tags', string='Variant Main Tag', required=False)
    x_variant_attribute_line_ids = fields.One2many(comodel_name='product.variant.attribute.lines',
                                                   inverse_name='x_bom_tool_id', string='Variant Attributes')
    x_product_categ_id = fields.Many2one(comodel_name='product.category', string='Default Var. Category')

    x_product_group = fields.Many2one(related="x_base_product_id.x_product_group", readonly=False, store=True)
    x_product_series = fields.Many2one(related="x_base_product_id.x_product_series", readonly=False, store=True)
    x_product_division = fields.Many2one(related="x_base_product_id.x_product_division", readonly=False, store=True)
            
    dk_hs_code = fields.Many2one(related="x_base_product_id.dk_hs_code", readonly=False, store=True)
    x_hs_code_tr_id = fields.Many2one(related="x_base_product_id.x_hs_code_tr_id", readonly=False, store=True)
    x_country_id = fields.Many2one(related="x_base_product_id.x_country_id", readonly=False, store=True)

    x_base_short_description = fields.Char(related="x_base_product_id.x_short_description", readonly=False, store=True)
    x_base_description = fields.Text(related="x_base_product_id.description", store=True, readonly=False)
    x_base_description_pickingout = fields.Text(related="x_base_product_id.description_pickingout", readonly=False, store=True)
    x_base_description_sale = fields.Text(related="x_base_product_id.description_sale", readonly=False, store=True)

    x_search_product_variant = fields.Char(string='Variant Contains', required=False)
    x_currency_id = fields.Many2one(related="x_base_product_id.currency_id", readonly=False, store=True)
    x_list_price = fields.Float(related="x_base_product_id.list_price", readonly=False, store=True)
    x_weight = fields.Float(related="x_base_product_id.weight", readonly=False, store=True)
    x_variant_categ_id = fields.Many2one(comodel_name='product.category', string='Update Var. Category')

    x_product_variant_ids = fields.One2many(comodel_name='product.variant.lines', inverse_name='x_bom_tool_id',
                                            string='Product Variant', required=False)

    # Variant BoM
    x_ref_des = fields.Char(string='RefDes', required=False)
    x_component_id = fields.Many2one(comodel_name='product.product', string='Component', required=False)
    x_variant_ids = fields.One2many(comodel_name='product.variant', inverse_name='x_bom_tool_id',
                                    string='Product Variant', required=False)

    x_variant_id = fields.Many2one(comodel_name='product.template', string='Selected Product')
    x_variant_bom_id = fields.Many2one(comodel_name='base.bom', string='Variant BoM (Input)', required=False)
    x_bom_ids = fields.Many2many(comodel_name='base.bom', relation='base_bom_bom_tool_rel_3',
                                 column1='base_bom_id', column2='bom_tool_id', string='BoM TOOL BoMs', )
    x_auto_complete_bom_id = fields.Many2one(comodel_name='base.bom', string='Auto-Complete',
                                             domain="[('id', 'in', x_bom_ids)]")

    x_search_variant_bom_lines = fields.Char(string='Search Lines', required=False)

    x_select_variant_bom_lines = fields.Boolean(string='Select All', required=False)
    x_compute_variant_selection = fields.Boolean(string='Select', compute='_compute_variant_selection', store=True)

    x_filter_variant_bom_lines = fields.Selection(selection=[
        ('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER'), ('all', 'ALL')
    ], string='Filter Line Type', default='all')

    x_undefined_variant_bom_lines = fields.Boolean(string='Undefined', required=False)
    x_dnp_variant_bom_lines = fields.Boolean(string='DNP', required=False)
    x_non_dnp_variant_bom_lines = fields.Boolean(string='NON DNP', required=False)
    x_critical_variant_bom_lines = fields.Boolean(string='CRITICAL', required=False)
    x_investor_variant_bom_lines = fields.Boolean(string='IP', required=False)

    x_new_design_variant_bom_lines = fields.Boolean(string='New Lines', required=False)
    x_modified_design_variant_bom_lines = fields.Boolean(string='Modified', required=False)
    x_deleted_design_variant_bom_lines = fields.Boolean(string='Deleted', required=False)

    x_new_variant_bom_lines = fields.Boolean(string='New Lines', required=False)
    x_modified_variant_bom_lines = fields.Boolean(string='Modified', required=False)
    x_deleted_variant_bom_lines = fields.Boolean(string='Deleted', required=False)

    x_variant_bom_line_product_id = fields.Many2one(comodel_name='product.template', string='Update Lines Part #')
    x_variant_bom_line_notes = fields.Char(string='Update Lines Notes')

    x_variant_bom_line_ids = fields.Many2many('base.bom.lines', 'base_bom_lines_bom_tool_rel_2',
                                              'base_bom_lines_id', 'bom_tool_id', 'BoM lines')

    # Alternate Part Selection
    x_search_aps_bom_lines = fields.Char(string='Search Lines', required=False)
    x_aps_selected_message = fields.Char('Selected BoM Lines', readonly=True, store=True)

    x_parts_selection = fields.Selection(selection=[
        ('all', 'All Parts'), ('base', 'Base Parts'), ('variant', 'Variant Parts'),
    ], string='Parts Selection', default='all', )

    x_dnp_aps_bom_lines = fields.Boolean(string='DNP', required=False)
    x_non_dnp_aps_bom_lines = fields.Boolean(string='NON DNP', required=False)
    x_critical_aps_bom_lines = fields.Boolean(string='CRITICAL', required=False)
    x_variant_aps_bom_lines = fields.Boolean(string='VARIANT', required=False)
    x_to_be_reviewed_aps_bom_lines = fields.Boolean(string='TO BE REVIEWED', required=False)

    x_aps_bom_line_ids = fields.Many2many('base.bom.lines', 'base_bom_lines_bom_tool_rel_3',
                                          'base_bom_lines_id', 'bom_tool_id', 'BoM lines')

    x_aps_selected_ref_des = fields.Char('Selected BoM Lines', readonly=True, store=True)
    x_aps_taraz_part_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part', readonly=True)
    x_aps_description = fields.Text(string="Description", required=False)

    x_alternate_usage_ids = fields.One2many(comodel_name='alternates.usage', inverse_name='x_bom_tool_id',
                                            string='Alternate Usage', required=False)

    x_compromised_usage_ids = fields.One2many(comodel_name='compromised.usage', inverse_name='x_bom_tool_id',
                                              string='Compromised Usage', required=False)

    # BoM Line Rules
    x_bom_line_rule_ids = fields.One2many(comodel_name='bom.line.rules', inverse_name='x_bom_tool_id',
                                          string='BoM Line Rules', required=False)

    # QC Checklist
    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_qc_checklist_ids = fields.One2many(comodel_name='bom.tool.qc.checklist', inverse_name='x_bom_tool_id',
                                         string='QC Checklist', required=False)

    def update_variants_components(self):
        for rec in self:
            if rec.x_ref_des:
                line_ids = rec.x_variant_ids.mapped('x_bom_id').mapped('x_bom_line_ids').filtered(
                    lambda l: l.x_ref_des == rec.x_ref_des
                )
                line_ids.update({'x_product_id': rec.x_component_id.product_tmpl_id.id})
                line_ids.update_uom_id()

    def get_qc_check_list(self):
        for rec in self:
            rec.x_qc_checklist_ids = [(2, line.id) for line in rec.x_qc_checklist_ids]
            for line in rec.x_bom_tool_id.x_qc_checklist_ids:
                line.copy({'x_bom_tool_id': rec.id})

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = ['|', ('x_name', operator, name), ('x_base_product_id.name', operator, name)]
            product_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))

    @api.model
    def create(self, vals):
        if vals.get('x_name', _('New')) == _('New'):
            vals['x_name'] = self.env['ir.sequence'].next_by_code('bom.tool') or 'New'
        return super(BomTool, self).create(vals)

    def write(self, vals):
        res = super(BomTool, self).write(vals)

        if self.x_base_product_name and not self.x_base_product_id:

            name = '%s%s' % (
                self.x_base_product_prefix, self.x_base_product_name
            ) if self.x_product_variants else self.x_base_product_name

            product_id = self.env['product.template'].search([('name', '=', name)])
            if not product_id:
                product_id = self.env['product.template'].create({
                    'name': name,
                    'type': 'product',
                    'categ_id': 275,
                    'route_ids': [5],
                })
            self.x_base_product_id = product_id.id

        # Create Product BoM if No BoM exist
        bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.x_base_product_id.id)])
        if not bom_id:
            self.env['mrp.bom'].create({'product_tmpl_id': self.x_base_product_id.id,
                                        'product_qty': 1, 'code': self.x_name})

        self.x_base_product_id.x_bom_tool_id = self.id

        return res

    def compute_bom_line(self):
        for rec in self:
            line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

            product_0_line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
            for line_0 in product_0_line_ids:
                line_0_ids = line_0.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                line_ids += line_0_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                product_1_line_ids = line_0_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                for line_1 in product_1_line_ids:
                    line_1_ids = line_1.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                    line_ids += line_1_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                    product_2_line_ids = line_1_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                    for line_2 in product_2_line_ids:
                        line_2_ids = line_2.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                        line_ids += line_2_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                        product_3_line_ids = line_2_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                        for line_3 in product_3_line_ids:
                            line_3_ids = line_3.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                            line_ids += line_3_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                            product_4_line_ids = line_3_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                            for line_4 in product_4_line_ids:
                                line_4_ids = line_4.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                                line_ids += line_4_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                                product_5_line_ids = line_4_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                                for line_5 in product_5_line_ids:
                                    line_5_ids = line_5.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                                    line_ids += line_5_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                                    product_6_line_ids = line_5_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                                    for line_6 in product_6_line_ids:
                                        line_6_ids = line_6.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                                        line_ids += line_6_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

                                        product_7_line_ids = line_6_ids.filtered(lambda l: l.x_product_id.x_bom_tool_id)
                                        for line_7 in product_7_line_ids:
                                            line_7_ids = line_7.x_product_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                                            line_ids += line_7_ids.filtered(lambda l: not l.x_product_id.x_bom_tool_id)

            return line_ids

    def action_view_note(self):
        action = self.env.ref('cus_letters.action_res_help').read()[0]
        form_view = [(self.env.ref('cus_letters.res_help_view_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        model_id = self.env['ir.model']._get(self._name).id
        note_id = self.env['res.help'].search([('x_model_id', '=', model_id)], limit=1)
        action['res_id'] = note_id.id
        return action

    def action_view_base_bom_lines(self):
        for rec in self:
            line_ids = rec.compute_bom_line()

            domain = [('id', 'in', line_ids.ids)]
            action = self.env.ref('cus_bom_tool.action_view_base_bom_lines').read()[0]
            action['domain'] = domain
            return action

    def action_view_task(self):
        for rec in self:
            action = self.env.ref('cus_bom_tool.action_view_bom_tool_task').read()[0]
            action['res_id'] = rec.x_task_id.id
            return action

    def change_state_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def change_state_to_review(self):
        for rec in self:
            rec.state = 'to_be_review'
            stage_id = self.env['project.task.type'].search([
                ('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
            ], limit=1)
            if rec.x_task_id:
                rec.x_task_id.kanban_state = 'pending'
                rec.x_task_id.x_user_stage_id = stage_id.id
                rec.x_task_id.stage_id = 272

    def change_state_to_active(self):
        for rec in self:
            rec.state = 'active'
            if rec.x_task_id:
                stage_id = self.env['project.task.type'].search([
                    ('name', '=', 'Done'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
                ], limit=1)
                rec.x_task_id.kanban_state = 'done'
                rec.x_task_id.x_user_stage_id = stage_id.id
                rec.x_task_id.stage_id = 273

    def change_state_to_inactive(self):
        for rec in self:
            rec.state = 'inactive'
            if rec.x_task_id:
                stage_id = self.env['project.task.type'].search([
                    ('name', '=', 'Done'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
                ], limit=1)
                rec.x_task_id.kanban_state = 'done'
                rec.x_task_id.x_user_stage_id = stage_id.id
                rec.x_task_id.stage_id = 274

    def send_line_update_email(self, body):
        for rec in self:
            rec.message_post(
                message_type="comment",
                subtype="bom_tool.bom_tool_subtype",
                body=body,
            )

    def send_subtask_email(self, subtask_name, subtask_state, subtask_user_id, old_name=None):
        for r in self:
            body = ""
            reviewer = self.env["res.users"].browse(subtask_user_id)
            user = self.env["res.users"].browse(subtask_user_id)
            state = SUBTASK_STATES[subtask_state]
            if subtask_state == "done":
                state = '<span style="color:#080">' + state + "</span>"
            if subtask_state == "todo":
                state = '<span style="color:#A00">' + state + "</span>"
            partner_ids = []
            subtype = "project_task_subtask.subtasks_subtype"
            if user == self.env.user and reviewer == self.env.user:
                body = "<p>" + "<strong>" + state + "</strong>: " + escape(subtask_name)
                subtype = False
            elif self.env.user == reviewer:
                body = (
                        "<p>"
                        + escape(user.name)
                        + ", <br><strong>"
                        + state
                        + "</strong>: "
                        + escape(subtask_name)
                )
                partner_ids = [user.partner_id.id]
            elif self.env.user == user:
                body = (
                        "<p>"
                        + escape(reviewer.name)
                        + ', <em style="color:#999">I updated checklist item assigned to me:</em> <br><strong>'
                        + state
                        + "</strong>: "
                        + escape(subtask_name)
                )
                partner_ids = [reviewer.partner_id.id]
            else:
                body = (
                        "<p>"
                        + escape(user.name)
                        + ", "
                        + escape(reviewer.name)
                        + ', <em style="color:#999">I updated checklist item, now its assigned to '
                        + escape(user.name)
                        + ": </em> <br><strong>"
                        + state
                        + "</strong>: "
                        + escape(subtask_name)
                )
                partner_ids = [user.partner_id.id, reviewer.partner_id.id]
            if old_name:
                body = (
                        body
                        + '<br><em style="color:#999">Updated from</em><br><strong>'
                        + state
                        + "</strong>: "
                        + escape(old_name)
                        + "</p>"
                )
            else:
                body = body + "</p>"
            r.message_post(
                message_type="comment",
                subtype=subtype,
                body=body,
                partner_ids=partner_ids,
            )

    # ---------------------- DEPENDS ----------------------
    @api.depends('x_name')
    def create_task(self):
        for rec in self:
            stage_id = self.env['project.task.type'].search([
                ('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
            ], limit=1)
            if not rec.x_task_id:
                task_id = self.env['project.task'].create({
                    'name': 'BoM Tool: %s' % rec.x_name,
                    'x_user_stage_id': stage_id.id,
                    'x_bom_tool_id': rec._origin.id,
                    'project_id': 63,
                    'stage_id': 267,
                    'kanban_state': 'pending',
                    'user_id': 28,
                    'x_user_participants': rec.x_team_member_ids.ids + [rec.x_team_lead_id.id],
                })
                rec.x_task_id = task_id.id
            else:
                rec.x_task_id.name = 'BoM Tool: %s' % rec.x_name
                rec.x_task_id.x_bom_tool_id = rec._origin.id,

    @api.depends('x_finished_good', 'x_product_type_fg', 'x_product_type_sfg')
    def _compute_name_prefix(self):
        for rec in self:
            base_product_prefix = 'TZB-'
            if rec.x_finished_good == 'finished':
                rec.x_product_type_sfg = 'cable'
                base_product_prefix += 'SYS-' if rec.x_product_type_fg == 'system' else 'PCB-'
            else:
                rec.x_product_type_fg = 'system'
                if rec.x_product_type_sfg == 'pcb':
                    base_product_prefix += 'PCB-'
                elif rec.x_product_type_sfg == 'cable':
                    base_product_prefix += 'CBLA-'
                elif rec.x_product_type_sfg == 'mechanical':
                    base_product_prefix += 'MECH-'
                elif rec.x_product_type_sfg == 'other':
                    base_product_prefix += 'ASM-'
                elif rec.x_product_type_sfg == 'inductor':
                    base_product_prefix += 'IND-'
                elif rec.x_product_type_sfg == 'transformer':
                    base_product_prefix += 'TRANS-'

            rec.x_base_product_prefix = base_product_prefix

    @api.depends('x_base_product_prefix', 'x_base_product_name')
    def _compute_base_product(self):
        for rec in self:
            name = '%s%s' % (
                rec.x_base_product_prefix, rec.x_base_product_name
            ) if rec.x_product_variants else rec.x_base_product_name

            product_id = self.env['product.template'].search([('name', '=', name)])
            if product_id:
                rec.x_base_product_id.x_bom_tool_id = False
                rec.x_base_product_id = product_id.id
            elif rec.x_base_product_id and rec.x_base_product_name:
                rec.x_base_product_id.name = name

            rec.x_base_bom_id.x_product_id = rec.x_base_product_id.id

            base_bom_ids = rec.x_variant_ids.mapped('x_bom_id').ids
            domain = [('x_base_bom_id', 'in', base_bom_ids), ('x_ref_des', '=', 'TZB01')]
            base_line_ids = self.env['base.bom.lines'].search(domain)
            base_line_ids.write({'x_product_id': rec.x_base_product_id.id})

    @api.depends('x_base_bom_id')
    def _compute_bom_tool_boms(self):
        for rec in self:
            bom_ids = self.env['base.bom'].search([('x_product_id', '=', rec.x_base_product_id.id)]).ids
            rec.x_bom_tool_bom_ids = [(6, 0, bom_ids)]

    @api.depends('x_select_base_bom_lines')
    def _compute_base_selection(self):
        for rec in self:
            rec.x_bom_line_ids.write({'x_line_select': rec.x_select_base_bom_lines})

    @api.depends('x_select_variant_bom_lines')
    def _compute_variant_selection(self):
        for rec in self:
            rec.x_variant_bom_line_ids.write({'x_line_select': rec.x_select_variant_bom_lines})

    # ---------------------- ONCHANGE ----------------------
    @api.onchange('x_product_variants')
    def reset_base_product_name(self):
        for rec in self:
            rec.x_base_product_name = False

    @api.onchange('x_team_lead_id')
    def get_team_members(self):
        for rec in self:
            team_member_ids = self.env['res.users'].search(
                [('employee_parent_id', '=', rec.x_team_lead_id.employee_id.id)])
            rec.x_team_member_ids = team_member_ids.ids

    @api.onchange('x_search_base_bom_lines', 'x_filter_base_bom_lines', 'x_undefined_base_bom_lines',
                  'x_dnp_base_bom_lines', 'x_non_dnp_base_bom_lines', 'x_critical_base_bom_lines',
                  'x_variant_base_bom_lines',
                  'x_investor_base_bom_lines', 'x_moved_base_bom_lines', 'x_new_design_base_bom_lines',
                  'x_modified_design_base_bom_lines', 'x_deleted_design_base_bom_lines',
                  'x_new_base_bom_lines', 'x_modified_base_bom_lines', 'x_deleted_base_bom_lines')
    def filter_base_bom_lines(self):
        for rec in self:
            rec.x_select_base_bom_lines = False
            rec.x_base_bom_line_count = len(rec.compute_bom_line())
            bom_line_ids = rec.x_base_bom_id.x_bom_line_ids

            search_text = str(rec.x_search_base_bom_lines).replace('(', '').replace(')', '')
            if search_text:
                bom_line_ids = bom_line_ids.filtered(lambda l: re.search(search_text, '%s %s %s %s %s %s %s %s' % (
                    str(l.x_name).replace('(', '').replace(')', ''),
                    str(l.x_part_description).replace('(', '').replace(')', ''),
                    str(l.x_ref_des).replace('(', '').replace(')', ''),
                    str(l.x_taraz_part_id.x_name).replace('(', '').replace(')', ''),
                    str(l.x_product_id.name).replace('(', '').replace(')', ''),
                    str(l.x_description).replace('(', '').replace(')', ''),
                    str(l.x_line_block_id.display_name).replace('(', '').replace(')', ''),
                    str(l.x_notes).replace('(', '').replace(')', ''),
                ), re.IGNORECASE))

            line_filter = rec.x_filter_base_bom_lines
            if line_filter == 'smd':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'smd')
            elif line_filter == 'th':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'th')
            elif line_filter == 'other':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'other')
            elif line_filter == 'undefined':
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_type)

            if rec.x_undefined_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_product_id)
            if rec.x_dnp_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_dnp)
            if rec.x_non_dnp_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_dnp)
            if rec.x_critical_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_critical)
            if rec.x_variant_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_variant)
            if rec.x_investor_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_investor_product)

            if rec.x_new_design_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_new)
            if rec.x_modified_design_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_modified)

            if rec.x_deleted_design_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_deleted)
            else:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_design_deleted)

            if rec.x_new_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_new)
            if rec.x_modified_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_modified)

            if rec.x_deleted_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_deleted)
            else:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_deleted)

            if rec.x_moved_base_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_move_to_tool_id or l.x_move_from_tool_id)
            else:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_move_to_tool_id)

            rec.x_bom_line_ids = [(6, 0, bom_line_ids.ids)]
            rec.x_select_base_bom_lines = True

    @api.onchange('x_product_group')
    def update_product_series(self):
        for rec in self:
            rec.x_product_series = rec.x_product_group.series.id
            rec.x_product_division = rec.x_product_series.division.id

    @api.onchange('x_product_series')
    def update_product_division(self):
        for rec in self:
            rec.x_product_division = rec.x_product_series.division.id

    @api.onchange('x_search_variant_bom_lines', 'x_filter_variant_bom_lines', 'x_undefined_variant_bom_lines',
                  'x_dnp_variant_bom_lines', 'x_non_dnp_variant_bom_lines', 'x_critical_variant_bom_lines',
                  'x_investor_variant_bom_lines',
                  'x_new_design_variant_bom_lines', 'x_modified_design_variant_bom_lines',
                  'x_deleted_design_variant_bom_lines', 'x_new_variant_bom_lines', 'x_modified_variant_bom_lines',
                  'x_deleted_variant_bom_lines')
    def filter_variant_bom_lines(self):
        for rec in self:
            rec.x_select_variant_bom_lines = False
            bom_line_ids = rec.x_variant_bom_id.x_bom_line_ids

            search_text = str(rec.x_search_variant_bom_lines).replace('(', '').replace(')', '')
            if search_text:
                bom_line_ids = bom_line_ids.filtered(lambda l: re.search(search_text, '%s %s %s %s %s %s %s %s' % (
                    str(l.x_name).replace('(', '').replace(')', ''),
                    str(l.x_part_description).replace('(', '').replace(')', ''),
                    str(l.x_ref_des).replace('(', '').replace(')', ''),
                    str(l.x_taraz_part_id.x_name).replace('(', '').replace(')', ''),
                    str(l.x_product_id.name).replace('(', '').replace(')', ''),
                    str(l.x_description).replace('(', '').replace(')', ''),
                    str(l.x_line_block_id.display_name).replace('(', '').replace(')', ''),
                    str(l.x_notes).replace('(', '').replace(')', ''),
                ), re.IGNORECASE))

            line_filter = rec.x_filter_variant_bom_lines
            if line_filter == 'smd':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'smd')
            elif line_filter == 'th':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'th')
            elif line_filter == 'other':
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_type == 'other')

            if rec.x_undefined_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_product_id)
            if rec.x_dnp_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_dnp)
            if rec.x_non_dnp_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_dnp)
            if rec.x_critical_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_critical)
            if rec.x_investor_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_investor_product)

            if rec.x_new_design_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_new)
            if rec.x_modified_design_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_modified)

            if rec.x_deleted_design_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_design_deleted)
            else:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_design_deleted)

            if rec.x_new_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_new)
            if rec.x_modified_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_modified)

            if rec.x_deleted_variant_bom_lines:
                bom_line_ids = bom_line_ids.filtered(lambda l: l.x_deleted)
            else:
                bom_line_ids = bom_line_ids.filtered(lambda l: not l.x_deleted)

            rec.x_variant_bom_line_ids = [(6, 0, bom_line_ids.ids)]
            rec.x_select_variant_bom_lines = True

    @api.onchange('x_parts_selection', 'x_search_aps_bom_lines', 'x_dnp_aps_bom_lines', 'x_non_dnp_aps_bom_lines',
                  'x_critical_aps_bom_lines', 'x_variant_aps_bom_lines', 'x_to_be_reviewed_aps_bom_lines')
    def filter_aps_bom_lines(self):
        for rec in self:
            rec.x_aps_selected_message = '.'
            rec.x_aps_taraz_part_id = False
            line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(
                lambda l: not l.x_deleted and not l.x_design_deleted and not l.x_variant)
            if rec.x_parts_selection == 'all':
                for bom in rec.x_variant_ids.mapped('x_bom_id'):
                    line_ids += bom.x_bom_line_ids.filtered(lambda l: not l.x_deleted and not l.x_design_deleted)
            elif rec.x_parts_selection == 'variant':
                line_ids -= line_ids
                for bom in rec.x_variant_ids.mapped('x_bom_id'):
                    line_ids += bom.x_bom_line_ids.filtered(lambda l: not l.x_deleted and not l.x_design_deleted)

            search_text = str(rec.x_search_aps_bom_lines).replace('(', '').replace(')', '')
            if search_text:
                line_ids = line_ids.filtered(lambda l: re.search(search_text, '%s %s %s %s %s %s' % (
                    str(l.x_ref_des).replace('(', '').replace(')', ''),
                    str(l.x_taraz_part_id.x_name).replace('(', '').replace(')', ''),
                    str(l.x_product_id.name).replace('(', '').replace(')', ''),
                    str(l.x_description).replace('(', '').replace(')', ''),
                    str(l.x_line_block_id.display_name).replace('(', '').replace(')', ''),
                    str(l.x_notes).replace('(', '').replace(')', ''),
                ), re.IGNORECASE))

            if rec.x_dnp_aps_bom_lines:
                line_ids = line_ids.filtered(lambda l: l.x_dnp)
            if rec.x_non_dnp_aps_bom_lines:
                line_ids = line_ids.filtered(lambda l: not l.x_dnp)
            if rec.x_critical_aps_bom_lines:
                line_ids = line_ids.filtered(lambda l: l.x_critical)
            if rec.x_variant_aps_bom_lines:
                line_ids = line_ids.filtered(lambda l: l.x_variant)
            if rec.x_to_be_reviewed_aps_bom_lines:
                line_ids = line_ids.filtered(lambda l: l.x_to_be_reviewed)

            rec.x_aps_bom_line_ids = [(6, 0, line_ids.ids)]

    # ---------------------- Base BoM ----------------------
    def open_import_file_wizard(self):
        action = self.env.ref('cus_bom_tool.action_import_bom_files').read()[0]
        return action

    def create_base_bom(self):
        for rec in self:
            bom_version = self.env['base.bom'].search_count([('x_product_id', '=', rec.x_base_product_id.id)])
            bom_version = '%s%s' % (0, bom_version + 1)
            bom_version = 'BOM.%s' % bom_version[-2:]
            base_bom_id = self.env['base.bom'].create({
                'x_name': bom_version,
                'x_product_id': rec.x_base_product_id.id,
                'x_bom_tool_id': rec._origin.id,
            })
            base_bom_id.x_name += ': %s' % str(base_bom_id.write_date)[0:10]
            rec.x_base_bom_id = base_bom_id.id
            rec.filter_base_bom_lines()

    def duplicate_bom(self):
        for rec in self:
            if rec.x_base_bom_id:
                bom_version = self.env['base.bom'].search_count([('x_product_id', '=', rec.x_base_product_id.id)])
                bom_version = '%s%s' % (0, bom_version + 1)
                bom_version = 'BOM.%s' % bom_version[-2:]
                base_bom_id = rec.x_base_bom_id.copy({'x_name': bom_version})
                base_bom_id.x_name += ': %s' % str(base_bom_id.write_date)[0:10]

                for line in rec.x_base_bom_id.x_bom_line_ids:
                    line_id = line.copy({
                        'x_base_bom_id': base_bom_id.id,
                    })

                    line.x_move_to_tool_id = False
                    line_id.move_line_to_bom()

                rec.x_base_bom_id = base_bom_id.id
                rec.filter_base_bom_lines()

    def download_bom(self):
        return self.env.ref('cus_bom_tool.base_bom_lines_excel_report').report_action(self)

    def clear_base_all_filters(self):
        for rec in self:
            rec.x_search_base_bom_lines = False
            rec.x_filter_base_bom_lines = 'all'

            rec.x_undefined_base_bom_lines = False
            rec.x_dnp_base_bom_lines = False
            rec.x_non_dnp_base_bom_lines = False
            rec.x_critical_base_bom_lines = False
            rec.x_variant_base_bom_lines = False
            rec.x_investor_base_bom_lines = False

            rec.x_new_design_base_bom_lines = False
            rec.x_modified_design_base_bom_lines = False
            rec.x_deleted_design_base_bom_lines = False

            rec.x_new_base_bom_lines = False
            rec.x_modified_base_bom_lines = False
            rec.x_deleted_base_bom_lines = False
            rec.x_moved_base_bom_lines = False

            rec.filter_base_bom_lines()

    def base_bom_lines_dnp(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_dnp': 'dnp'})

    def base_bom_lines_non_dnp(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_dnp': False})

    def base_bom_lines_critical(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_critical': 'critical'})

    def base_bom_lines_non_critical(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_critical': False})

    def base_bom_lines_variant(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_variant': 'variant'})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_variant': 'variant'})

    def base_bom_lines_non_variant(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_variant': False})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_variant': False})

    def base_bom_lines_investment_part(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_investor_product': True})

    def base_bom_lines_non_investment_part(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_investor_product': False})

    def base_bom_lines_smd(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'smd'})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'smd'})

    def base_bom_lines_th(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'th'})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'th'})

    def base_bom_lines_other(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'other'})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'other'})

    def add_base_bom_lines(self):
        if not self.x_base_bom_id:
            raise UserError('Base BoM is not selected.')
        action = self.env.ref('cus_bom_tool.action_bom_line_addition').read()[0]
        return action

    def delete_base_bom_lines(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_deleted': True})

    def restore_base_bom_lines(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_deleted': False})

    def open_block_update_wizard(self):
        if not self.x_base_bom_id:
            raise UserError('Base BoM is not selected.')
        action = self.env.ref('cus_bom_tool.action_block_addition').read()[0]
        return action

    def add_blocks_data(self):
        for rec in self:
            bom_block_ids = rec.x_base_bom_id.x_bom_line_ids.mapped('x_line_block_id')

            # Delete Removed Block Lines
            for block in bom_block_ids:
                if block.id not in rec.x_attached_block_ids.mapped('x_block_id').ids:
                    block.x_bom_tool_ids = [(3, rec.id)]
                    line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_line_block_id.id == block.id)
                    for line in line_ids:
                        line.x_deleted = True

            # Add New Block Lines
            all_ref_des = rec.x_base_bom_id.x_bom_line_ids.mapped('x_ref_des')
            block_ref_des = [ref_des for ref_des in all_ref_des if 'MANBLK' in ref_des]
            block_ref_des_count = len(block_ref_des)

            for block in rec.x_attached_block_ids:
                block_id = block.x_block_id
                line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_line_block_id.id == block_id.id)
                for line in line_ids:
                    line.x_deleted = False

                block_id.x_bom_tool_ids = [(4, rec.id)]
                if block_id.x_bom_line_ids[0].x_name:
                    line_ids = line_ids.filtered(lambda l: l.x_name == block_id.x_bom_line_ids[0].x_name)
                else:
                    line_ids = line_ids.filtered(
                        lambda l: l.x_product_id.id == block_id.x_bom_line_ids[0].x_product_id.id)
                block_part_quantity = block_id.x_bom_line_ids[0].x_quantity * block.x_quantity
                if len(line_ids) < block_part_quantity:
                    block_quantity = block.x_quantity - len(line_ids) / block_id.x_bom_line_ids[0].x_quantity
                    for block_qty in range(int(block_quantity)):
                        for line in block_id.x_bom_line_ids:
                            for qty in range(int(line.x_quantity)):
                                block_ref_des_count += 1
                                ref_des = 'MANBLK%s' % block_ref_des_count
                                rec.x_base_bom_id.x_bom_line_ids = [(0, 0, {
                                    'x_name': line.x_name,
                                    'x_part_description': line.x_part_description,
                                    'x_ref_des': ref_des,
                                    'x_product_id': line.x_product_id.id,
                                    'x_quantity': 1,
                                    'x_uom_id': line.x_uom_id.id or line.x_product_id.uom_id.id,
                                    'x_line_block_id': block_id.id,
                                    'x_station_id': line.x_station_id.id,
                                })]
                elif len(line_ids) > block_part_quantity:
                    line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_line_block_id.id == block_id.id)
                    for block_line in block_id.x_bom_line_ids:
                        if block_line.x_name:
                            bom_line_ids = line_ids.filtered(lambda l: l.x_name == block_line.x_name)
                        else:
                            bom_line_ids = line_ids.filtered(lambda l: l.x_product_id.id == block_line.x_product_id.id)
                        for index in range(int(block_line.x_quantity) * int(block.x_quantity), len(bom_line_ids)):
                            bom_line_ids[index].x_deleted = True

            rec.filter_base_bom_lines()

    def update_bom_line_products(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_product_id': rec.x_bom_line_product_id.id})
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).update_uom_id()

    def update_bom_line_operation(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_operation_id': rec.x_operation_id.id})

    def update_bom_line_notes(self):
        for rec in self:
            rec.x_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_notes': rec.x_bom_line_notes})

    def update_bom_line_move_to(self):
        for rec in self:
            for line in rec.x_bom_line_ids:
                if line.x_line_select:
                    line.x_move_to_tool_id = rec.x_move_to_bom_tool_id.id
                    line.move_line_to_bom()

    # ---------------------- Product Variant ----------------------
    def compute_product_variants(self):
        for rec in self:
            if not rec.x_variant_attribute_line_ids:
                break
            prefixes = []
            variant_tags = []
            for attribute in rec.x_variant_attribute_line_ids:
                if not attribute.x_attribute_id.x_name[:1].isalpha():
                    prefixes.append(attribute.x_attribute_id.x_name[:1])
                else:
                    prefixes.append('')

                variant_tags.append({
                    'attribute': attribute.x_attribute_id.x_name,
                    'tag': attribute.x_attribute_tag_ids.mapped('x_name'),
                    'tag_description': attribute.x_attribute_tag_ids.mapped('x_description'),
                })

            description = rec.x_base_description
            short_description = rec.x_base_short_description
            description_pickingout = rec.x_base_description_pickingout
            description_sale = rec.x_base_description_sale

            variant_tags[0]['description'] = description
            variant_tags[0]['short_description'] = short_description
            variant_tags[0]['description_pickingout'] = description_pickingout
            variant_tags[0]['description_sale'] = description_sale

            variants_data = []
            for x in range(len(variant_tags[0]['tag'])):
                variants_data.append({
                    'tag': '%s%s' % (prefixes[0], variant_tags[0]['tag'][x]) if variant_tags[0]['tag'][x] != 'No Tag' else '',
                    'tag_description': [{
                        'attribute': '{%s}' % variant_tags[0]['attribute'],
                        'tag_description': variant_tags[0]['tag_description'][x],
                    }],
                    'description': description,
                    'short_description': short_description,
                    'description_pickingout': description_pickingout,
                    'description_sale': description_sale,
                })

            for x in range(len(variant_tags)):
                if len(variant_tags) == x + 1:
                    break
                if variant_tags[x + 1]:
                    variants = variants_data
                    variants_data = []

                    for y in range(len(variant_tags[x + 1]['tag'])):
                        for z in range(len(variants)):
                            tag_description = variants[z]['tag_description'] + [{
                                'attribute': '{%s}' % variant_tags[x + 1]['attribute'],
                                'tag_description': variant_tags[x + 1]['tag_description'][y],
                            }]

                            if variant_tags[x + 1]['tag'][y] != 'No Tag':
                                tag = '%s%s%s' % (variants[z]['tag'], prefixes[x + 1], variant_tags[x + 1]['tag'][y])
                            else:
                                tag = variants[z]['tag']

                            variants_data.append({
                                'tag': tag,
                                'tag_description': tag_description,
                                'description': description,
                                'short_description': short_description,
                                'description_pickingout': description_pickingout,
                                'description_sale': description_sale,
                            })

            for variant in variants_data:
                desc = variant['tag_description']
                for x in range(len(variant['tag_description'])):
                    if not desc[x]['tag_description']:
                        variant['description'] = variant['description'].replace(
                            desc[x]['attribute'], ''
                        ) if variant['description'] else variant['description']
                        variant['short_description'] = variant['short_description'].replace(
                            desc[x]['attribute'], ''
                        ) if variant['short_description'] else variant['short_description']
                        variant['description_pickingout'] = variant['description_pickingout'].replace(
                            desc[x]['attribute'], ''
                        ) if variant['description_pickingout'] else variant['description_pickingout']
                        variant['description_sale'] = variant['description_sale'].replace(
                            desc[x]['attribute'], ''
                        ) if variant['description_sale'] else variant['description_sale']
                    else:
                        variant['description'] = variant['description'].replace(
                            desc[x]['attribute'], desc[x]['tag_description']
                        ) if variant['description'] else variant['description']
                        variant['short_description'] = variant['short_description'].replace(
                            desc[x]['attribute'], desc[x]['tag_description']
                        ) if variant['short_description'] else variant['short_description']
                        variant['description_pickingout'] = variant['description_pickingout'].replace(
                            desc[x]['attribute'], desc[x]['tag_description']
                        ) if variant['description_pickingout'] else variant['description_pickingout']
                        variant['description_sale'] = variant['description_sale'].replace(
                            desc[x]['attribute'], desc[x]['tag_description']
                        ) if variant['description_sale'] else variant['description_sale']

            variants = []
            for variant in variants_data:
                variants.append({
                    'x_name': '%s%s' % (rec.x_product_tag_id.x_name, variant['tag']),
                    'x_description': variant['description'],
                    'x_short_description': variant['short_description'],
                    'x_description_pickingout': variant['description_pickingout'],
                    'x_description_sale': variant['description_sale'],
                    'x_var_description': variant['description'],
                    'x_var_short_description': variant['short_description'],
                    'x_var_description_pickingout': variant['description_pickingout'],
                    'x_var_description_sale': variant['description_sale'],
                })

            rec.x_product_variant_ids = [
                (2, line.id) for line in rec.x_product_variant_ids.filtered(lambda l: not l.x_product_id)
            ]

            product_variant_ids = []
            for variant in variants:
                variant_id = rec.x_product_variant_ids.filtered(lambda l: l.x_name == variant['x_name'])
                if not variant_id:
                    product_variant_ids.append((0, 0, variant))
                else:
                    variant_id.update(variant)
            if product_variant_ids:
                rec.x_product_variant_ids = product_variant_ids

    def update_short_description(self):
        for rec in self:
            rec.compute_product_variants()

    def update_description(self):
        for rec in self:
            rec.compute_product_variants()

    def update_description_pickingout(self):
        for rec in self:
            rec.compute_product_variants()

    def update_description_sale(self):
        for rec in self:
            rec.compute_product_variants()

    def update_variant_data(self):
        for rec in self:
            if rec.x_search_product_variant:
                search = rec.x_search_product_variant.replace('(', '').replace(')', '')
                variant_ids = rec.x_product_variant_ids.filtered(lambda l: re.search(
                    search, l.x_product_id.name, re.IGNORECASE
                ))
            else:
                variant_ids = rec.x_product_variant_ids
            for variant in variant_ids:
                variant.x_list_price = rec.x_list_price
                variant.x_weight = rec.x_weight

    def update_variant_categ_id(self):
        for rec in self:
            if rec.x_variant_categ_id:
                if rec.x_search_product_variant:
                    search = rec.x_search_product_variant.replace('(', '').replace(')', '')
                    variant_ids = rec.x_product_variant_ids.filtered(lambda l: re.search(
                        search, l.x_product_id.name, re.IGNORECASE
                    ))
                else:
                    variant_ids = rec.x_product_variant_ids
                for variant in variant_ids:
                    variant.x_categ_id = rec.x_variant_categ_id.id

    # ---------------------- Variant BoM ----------------------
    def auto_complete_bom(self):
        for rec in self:
            if rec.x_auto_complete_bom_id and rec.x_variant_bom_id:
                rec.x_variant_bom_id.x_bom_line_ids.unlink()
                for line in rec.x_auto_complete_bom_id.x_bom_line_ids:
                    line.copy({'x_base_bom_id': rec.x_variant_bom_id.id})
                rec.clear_variant_all_filters()

    def clear_variant_all_filters(self):
        for rec in self:
            rec.x_search_variant_bom_lines = False
            rec.x_filter_variant_bom_lines = 'all'

            rec.x_undefined_variant_bom_lines = False
            rec.x_dnp_variant_bom_lines = False
            rec.x_non_dnp_variant_bom_lines = False
            rec.x_critical_variant_bom_lines = False
            rec.x_variant_variant_bom_lines = False
            rec.x_investor_variant_bom_lines = False

            rec.x_new_design_variant_bom_lines = False
            rec.x_modified_design_variant_bom_lines = False
            rec.x_deleted_design_variant_bom_lines = False

            rec.x_new_variant_bom_lines = False
            rec.x_modified_variant_bom_lines = False
            rec.x_deleted_variant_bom_lines = False

            rec.filter_variant_bom_lines()

    def variant_bom_lines_dnp(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_dnp': 'dnp'})

    def variant_bom_lines_non_dnp(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_dnp': False})

    def variant_bom_lines_critical(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_critical': 'critical'})

    def variant_bom_lines_non_critical(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_critical': False})

    def variant_bom_lines_smd(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'smd'})
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'smd'})

    def variant_bom_lines_th(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'th'})
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'th'})

    def variant_bom_lines_other(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_type': 'other'})
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).mapped('x_slave_bom_line_id').write({'x_type': 'other'})

    def update_variant_bom_line_products(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_product_id': rec.x_variant_bom_line_product_id.id})

    def update_variant_bom_line_notes(self):
        for rec in self:
            rec.x_variant_bom_line_ids.filtered(lambda l: l.x_line_select).write({'x_notes': rec.x_variant_bom_line_notes})

    # ---------------------- Alternate Part Selection ----------------------
    def define_aps_bom_lines(self):
        for rec in self:
            rec.unselect_all_aps_line()
            rec.filter_aps_bom_lines()
            rec.select_all_aps_line()

    def select_all_aps_line(self):
        for rec in self:
            aps_line_id = False
            for line in rec.x_aps_bom_line_ids:
                line.x_aps_line_select = True
                aps_line_id = line
            if aps_line_id:
                aps_line_id.get_lines_taraz_part_data(True)

    def unselect_all_aps_line(self):
        for rec in self:
            aps_line_id = False
            for line in rec.x_aps_bom_line_ids:
                line.x_aps_line_select = False
                aps_line_id = line
            if aps_line_id:
                aps_line_id.get_lines_taraz_part_data(False)

    def clear_aps_all_filters(self):
        for rec in self:
            rec.x_aps_selected_message = '.'
            rec.x_search_aps_bom_lines = False

            rec.x_dnp_aps_bom_lines = False
            rec.x_non_dnp_aps_bom_lines = False
            rec.x_critical_aps_bom_lines = False
            rec.x_variant_aps_bom_lines = False
            rec.x_to_be_reviewed_aps_bom_lines = False

            rec.x_aps_taraz_part_id = False

            rec.filter_aps_bom_lines()

    def action_open_in_editor(self):
        action = self.env.ref('cus_bom_tool.action_open_taraz_part_number_from_bom_tool').read()[0]
        action['res_id'] = self.x_aps_taraz_part_id.id
        return action

    def mark_as_reviewed(self):
        for rec in self:
            for line in rec.x_aps_bom_line_ids:
                line.x_to_be_reviewed = False if line.x_aps_line_select else line.x_to_be_reviewed

            rec.define_aps_bom_lines()
            if not rec.x_aps_bom_line_ids:
                rec.x_search_aps_bom_lines = False
                rec.x_aps_taraz_part_id = False
                rec.filter_aps_bom_lines()

    def unlink(self):
        for rec in self:
            rec.x_task_id.unlink()
            self.env['base.bom'].search([('x_bom_tool_id', '=', rec.id)]).unlink()
            rec.x_bom_tool_checklist.unlink()
            rec.x_attached_block_ids.unlink()
            rec.x_variant_attribute_line_ids.unlink()
            rec.x_product_variant_ids.unlink()
            rec.x_variant_ids.unlink()
            rec.x_bom_line_rule_ids.unlink()
        return super(BomTool, self).unlink()


class BomToolTags(models.Model):
    _name = "bom.tool.tags"
    _description = "BoM Tool Tags"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)


class BomToolCheckList(models.Model):
    _name = 'bom.tool.check.list'
    _description = "BoM Tool Checklist"
    _rec_name = 'x_description'

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_description = fields.Char(string='Description', required=True)
    x_user_id = fields.Many2one(comodel_name='res.users', string='Assigned to', required=True, tracking=True)
    x_deadline = fields.Date(string='Deadline', required=False)
    x_state = fields.Selection(selection=[
        ('done', 'Done'), ('todo', 'TODO')
    ], string='Status', required=True, default='todo')
    x_task_id = fields.Many2one(comodel_name='project.task', string='Task', required=False)
    x_user_stage_id = fields.Many2one(related="x_task_id.x_user_stage_id")

    @api.onchange('x_deadline')
    def update_task_deadline(self):
        for rec in self:
            if rec.x_task_id:
                rec.x_task_id.date_deadline = rec.x_deadline

    def create_task(self):
        for rec in self:
            if not rec.x_task_id:
                stage_id = self.env['project.task.type'].search([
                    ('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
                ], limit=1)
                finished_good = 'Finished Good' if rec.x_bom_tool_id.x_finished_good == 'finished' else 'Semi-Finished Good'
                postfix = '[%s, %s, %s]' % (
                    rec.x_bom_tool_id.x_name, finished_good, rec.x_bom_tool_id.x_base_bom_id.x_name
                )
                task_id = self.env['project.task'].create({
                    'name': '%s %s' % (rec.x_description, postfix),
                    'x_user_stage_id': stage_id.id,
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'project_id': 63,
                    'stage_id': 267,
                    'kanban_state': 'pending',
                    'user_id': rec.x_user_id.id,
                    'date_deadline': rec.x_deadline,
                })
                rec.x_task_id = task_id.id

    def change_state_to_done(self):
        for rec in self:
            rec.x_state = 'done'
            if rec.x_task_id:
                stage_id = self.env['project.task.type'].search([
                    ('name', '=', 'Done'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
                ], limit=1)
                rec.x_task_id.kanban_state = 'done'
                rec.x_task_id.x_user_stage_id = stage_id.id
                rec.x_task_id.stage_id = 273

    def change_state_to_todo(self):
        for rec in self:
            rec.x_state = 'todo'
            if rec.x_task_id:
                stage_id = self.env['project.task.type'].search([
                    ('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)
                ], limit=1)
                rec.x_task_id.kanban_state = 'pending'
                rec.x_task_id.x_user_stage_id = stage_id.id
                rec.x_task_id.stage_id = 267

    @api.model
    def create(self, vals):
        result = super(BomToolCheckList, self).create(vals)
        vals = self._add_missing_default_values(vals)
        bom_tool = self.env["bom.tool"].browse(vals.get("x_bom_tool_id"))
        bom_tool.send_subtask_email(
            vals["x_description"], vals["x_state"], vals["x_user_id"]
        )
        return result

    def write(self, vals):
        old_names = dict(list(zip(self.mapped("id"), self.mapped("x_description"))))
        result = super(BomToolCheckList, self).write(vals)
        for r in self:
            if vals.get("x_state"):
                r.x_bom_tool_id.send_subtask_email(
                    r.x_description, r.x_state, r.x_user_id.id
                )
                if self.env.user != r.create_uid and self.env.user != r.x_user_id:
                    raise UserError(_("Only users related to that subtask can change state."))
            if vals.get("x_description"):
                r.x_bom_tool_id.send_subtask_email(
                    r.x_description, r.x_state, r.x_user_id.id, old_name=old_names[r.id],
                )
                if self.env.user != r.create_uid and self.env.user != r.x_user_id:
                    raise UserError(_("Only users related to that subtask can change state."))
            if vals.get("x_user_id"):
                r.x_bom_tool_id.send_subtask_email(
                    r.x_description, r.x_state, r.x_user_id.id
                )
        return result

    def unlink(self):
        for rec in self:
            if rec.x_task_id:
                rec.x_task_id.unlink()
        return super(BomToolCheckList, self).unlink()


class BomLineStation(models.Model):
    _name = "bom.line.station"
    _description = "BoM Line Station"
    _rec_name = 'display_name'

    x_name = fields.Char(string='Name', required=True)
    x_type = fields.Selection(selection=[
        ('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER'),
    ], string='Mounting Type', required=True)
    x_description = fields.Char(string='Description', required=False)

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)

    @api.depends('x_name', 'x_description')
    def _compute_display_name(self):
        for rec in self:
            if rec.x_description:
                rec.display_name = '%s (%s)' % (rec.x_name, rec.x_description)
            else:
                rec.display_name = rec.x_name


class BomToolBlocks(models.Model):
    _name = "bom.tool.blocks"
    _description = "BoM Tool Blocks"
    _rec_name = 'display_name'

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_block_id = fields.Many2one(comodel_name='bom.blocks', string='Block', required=False)
    x_quantity = fields.Integer(string='Quantity', default=1)

    @api.depends('x_block_id', 'x_quantity')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s (Qty: %s)' % (rec.x_block_id.x_name, rec.x_quantity)


class AlternatesUsage(models.Model):
    _name = "alternates.usage"
    _description = "Alternates Usage"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_alternate_id = fields.Many2one(comodel_name='taraz.part.alternates', string='Alternate', required=False)
    x_description = fields.Text(related="x_alternate_id.x_description")
    x_qty_available = fields.Float(related="x_alternate_id.x_qty_available")
    x_usage = fields.Selection(selection=[
        ('auto_use', 'Auto Use'), ('use', 'Use'), ('not_use', "Don't Use")
    ], default="auto_use", string='Usage', stotr=True)

    def auto_use_line(self):
        for rec in self:
            rec.x_usage = 'auto_use'
            rec.update_bom_line_usage()

    def use_line(self):
        for rec in self:
            rec.x_usage = 'use'
            rec.update_bom_line_usage()

    def not_use_line(self):
        for rec in self:
            rec.x_usage = 'not_use'
            rec.update_bom_line_usage()

    def update_bom_line_usage(self):
        for rec in self:
            for line in rec.x_bom_tool_id.x_aps_bom_line_ids:
                if line.x_aps_line_select:
                    usage_ids = line.x_usage_ids.filtered(lambda l: l.x_alternate_id.id == rec.x_alternate_id.id)
                    for usage_id in usage_ids:
                        usage_id.x_usage = rec.x_usage
                    line.x_to_be_reviewed = False


class CompromisedUsage(models.Model):
    _name = "compromised.usage"
    _description = "Compromised Usage"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_compromised_id = fields.Many2one(comodel_name='taraz.part.compromised', string='Compromised', required=False)
    x_description = fields.Text(related="x_compromised_id.x_description")
    x_qty_available = fields.Float(related="x_compromised_id.x_qty_available")
    x_usage = fields.Selection(selection=[
        ('auto_use', 'Auto Use'), ('use', 'Use'), ('not_use', "Don't Use")
    ], default="use", string='Usage', store=True)

    def auto_use_line(self):
        for rec in self:
            rec.x_usage = 'auto_use'
            rec.update_bom_line_usage()

    def use_line(self):
        for rec in self:
            rec.x_usage = 'use'
            rec.update_bom_line_usage()

    def not_use_line(self):
        for rec in self:
            rec.x_usage = 'not_use'
            rec.update_bom_line_usage()

    def update_bom_line_usage(self):
        for rec in self:
            for line in rec.x_bom_tool_id.x_aps_bom_line_ids:
                if line.x_aps_line_select:
                    line.x_usage_ids.filtered(lambda l: l.x_compromised_id.id == rec.x_compromised_id.id).write({
                        'x_usage': rec.x_usage
                    })
                    line.x_to_be_reviewed = False


class BomToolQcChecklist(models.Model):
    _name = "bom.tool.qc.checklist"
    _description = "QC Checklist"
    _order = "x_sequence"
    _rec_name = "x_checklist"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)

    x_sequence = fields.Integer(string='Sequence', required=False)
    x_checklist = fields.Char(string='Checklist', required=False)
    x_description = fields.Text(string='Description', required=False)
    x_notes = fields.Text(string='Notes', required=False)
    x_typical_value = fields.Char(string='Typical Value', required=False)











