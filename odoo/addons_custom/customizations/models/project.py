from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

from datetime import date
from lxml import etree

import datetime


class Project(models.Model):
    _inherit = "project.project"

    def _get_default_user(self):
        return [self.env.uid]

    def _get_default_admins(self):
        return [2, 17, 19, 20, self.env.uid]

    x_description = fields.Char(string="Description", required=False, )
    x_project_type = fields.Many2one(comodel_name="project.group", string="Project Group", required=True, )
    x_project_user_ids = fields.Many2many(comodel_name="res.users", relation="res_users_project_project_rel_1",
                                          column1="project_project_id", column2="res_users_id", string="Users",
                                          default=_get_default_user, tracking=True, required=True, )
    x_project_admin_ids = fields.Many2many(comodel_name="res.users", relation="res_users_project_project_rel_2",
                                           column1="project_project_id", column2="res_users_id", string="Project Admins",
                                           default=_get_default_admins, tracking=True, required=True, )

    x_attachment = fields.Binary(string="Attachment", )
    x_loom_link = fields.Char(string="Loom Link", required=False, )
    x_tag_ids = fields.Many2many(comodel_name='project.tags', string=' Project Tags')

    # ------------------------------- Task Settings -------------------------------
    x_trackbot_filter = fields.Boolean(string="Apply TrackBot Filter", )
    x_hide_done_task = fields.Boolean(string="Hide Done Tasks", )
    x_default_participant_ids = fields.Many2many(comodel_name="res.users", relation="res_users_project_project_rel_3",
                                                 column1="project_project_id", column2="res_users_id",
                                                 string="Default Participants", )
    x_default_observer_ids = fields.Many2many(comodel_name="res.users", relation="res_users_project_project_rel_4",
                                              column1="project_project_id", column2="res_users_id",
                                              string="Default Observers", )
    x_show_arithmetic_value = fields.Boolean(string="Show Arithmetic Value", )
    x_arithmetic_label = fields.Char(string="Arithmetic Value Label", defualt="Arithmetic Value")
    x_task_field_ids = fields.One2many(comodel_name="task.quick.create.form.fields", inverse_name="x_project_id",
                                       string="Tasks Quick Create Form Fields", required=False, )


class Task(models.Model):
    _inherit = "project.task"

    x_cable_manufacturing_id = fields.Many2one(comodel_name="cable.assembly", string="Cable Manufacturing ID")
    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order ID")
    x_purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order ID")
    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')
    x_picking_type_code = fields.Selection(related='x_picking_id.picking_type_code')

    def action_view_cable_manufacturing(self):
        action = self.env.ref('cable_assembly.action_cable_assembly').read()[0]
        form_view = [(self.env.ref('cable_assembly.view_cable_assembly_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_cable_manufacturing_id.id
        return action

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready').read()[0]
        form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_picking_id.id
        return action

    def action_view_sale_order(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_sale_order_id.id
        return action

    def action_view_purchase_order(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_purchase_order_id.id
        return action

    # =====================================================================================================================
    def _get_default_user_stage_id(self):
        """ Gives default stage_id """
        stage_id = self.env['project.task.type'].search(
            [('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)], limit=1)
        return stage_id.id if stage_id else False

    @api.model
    def _read_group_user_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        search_domain = ['|', '&', ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)] + search_domain
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    x_so_product_ids = fields.One2many(comodel_name='sale.order.products.task', inverse_name='x_task_id',
                                       string='SO Products', compute="_compute_so_products", store=True)

    x_user_stage_id = fields.Many2one('project.task.type', string='User Stage', ondelete='restrict', index=True,
                                      group_expand='_read_group_user_stage_ids', domain="[('project_ids', '=', False)]",
                                      default=_get_default_user_stage_id, copy=False)

    x_user_participants = fields.Many2many(comodel_name="res.users", relation="res_users_project_task_rel_1",
                                           column1="project_task_id", column2="res_users_id", string="Participants",
                                           domain="[('id','!=',user_id),('id','not in',x_user_observers)]", )
    x_user_observers = fields.Many2many(comodel_name="res.users", relation="res_users_project_task_rel_2",
                                        column1="project_task_id", column2="res_users_id", string="Observers",
                                        domain="[('id','!=',user_id),('id','not in',x_user_participants)]", )

    x_start_task_on = fields.Date(string="Start task on", required=False, tracking=True, )
    x_notes = fields.Text(string="Notes", required=False, tracking=True, )
    x_subtask_list = fields.One2many(comodel_name="subtask.list", inverse_name="x_task_id", string="Subtasks")
    x_subtask_list_hide = fields.Boolean(string="Subtasks Hide", default=True, )
    x_poked = fields.Boolean(string="Poked", default=False, tracking=True, compute="_compute_poke", store=True, )
    x_poke_counter = fields.Integer(string="Poke Counter", required=False, default=0, tracking=True, )
    x_deadline_days = fields.Integer(string="Deadline Days", required=False, )
    x_deadline_stage = fields.Selection(selection=[
        ('overdue', '1. Overdue'),
        ('due_today', '2. Due today'),
        ('due_this_week', '3. Due this week'),
        ('due_next_week', '4. Due next week'),
        ('no_deadline', '6. No deadline'),
        ('due_over_two_weeks', '7. Due over two weeks'),
    ], string="Deadline Stage", required=False, tracking=True, )
    stage_usage = fields.Selection(selection=[
        ('responsible', 'Responsible'), ('assisting', 'Assisting'), ('following', 'Following'),
    ], string="Stage Usage", default=lambda self: self.env.context.get('default_stage_usage'), required=False, )
    x_user_department = fields.Many2one(related="user_id.employee_id.department_id")
    x_completion_date = fields.Date(string="Completion Date", required=False,
                                    compute="_compute_completion_date", store=True, )
    duration = fields.Float('Real Duration', compute='_compute_duration', store=True, )
    is_user_working = fields.Boolean('Is Current User Working', compute='_compute_is_user_working',
                                     help="Technical field indicating whether the current user is working.", )
    x_partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", required=False, )
    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_project_task_id", string="Images",
                                  required=False, )
    x_attachment = fields.Binary(string="Attachment", )
    x_show_arithmetic_value = fields.Boolean(string="Show Arithmetic Value",
                                             related="project_id.x_show_arithmetic_value", )
    x_arithmetic_label = fields.Char(string="Arithmetic Value Label", required=False,
                                     related="project_id.x_arithmetic_label", )
    x_arithmetic_field = fields.Float(string="Arithmetic Value", required=False, )

    # ============================================= DEPENDS =============================================
    @api.depends('x_sale_order_id.order_line')
    def _compute_so_products(self):
        for rec in self:
            if rec.x_sale_order_id:
                so_product_ids = rec.x_sale_order_id.order_line.search([
                    ('id', 'not in', rec.x_so_product_ids.mapped('x_line_id').ids),
                    ('product_id.type', '!=', 'service'),
                    ('product_id.name', 'not ilike', 'BOS'),
                ])
                rec.x_so_product_ids = [(0, 0, {'x_task_id': rec.id, 'x_line_id': line.id}) for line in so_product_ids]

    @api.depends('kanban_state')
    def _compute_completion_date(self):
        for rec in self:
            if rec.kanban_state == 'done':
                rec.x_completion_date = datetime.date.today()
                author_id = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.id
                followers = self.message_follower_ids.mapped('partner_id').ids
                self.message_post(author_id=author_id, body='Task is done!', message_type='comment',
                                  subtype='mt_comment', followers=followers)

    @api.depends('stage_id', 'x_user_stage_id')
    def _compute_poke(self):
        for rec in self:
            rec.x_poked = False

    # ============================================= ON CHANGE =============================================
    @api.onchange('user_id')
    def onchange_user_id(self):
        for rec in self:
            rec.x_user_participants = [(3, rec.user_id.id)]
            rec.x_user_observers = [(3, rec.user_id.id)]
            if rec.user_id.id != self.env.uid and self.env.uid not in rec.x_user_observers.ids:
                rec.x_user_observers = [(4, self.env.uid)]

    @api.onchange('kanban_state')
    def onchange_kanban_state(self):
        for rec in self:
            for subtask in rec.x_subtask_list:
                if not subtask.x_created_task_id and rec.kanban_state == 'done':
                    raise UserError(_('Error: You cannot mark task as done. Some subtasks are not created!'))
                elif subtask.x_created_task_id.kanban_state != 'done' and rec.kanban_state == 'done':
                    raise UserError(_('Error: You cannot mark task as done. Some subtasks are not done!'))

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        for rec in self:
            if self.env.uid in rec.x_user_observers.ids and self.env.uid not in rec.x_user_participants.ids and rec.user_id.id != 28 and self.env.uid != rec.user_id:
                raise UserError(_('Error: Observer cannot change the task stage!'))
            elif rec.stage_id:
                # Update Task State
                if rec.stage_id.x_mark_status_as:
                    rec.kanban_state = rec.stage_id.x_mark_status_as
                else:
                    rec.kanban_state = 'pending'
                # Update Task Tags
                if rec.stage_id.x_stage_as_tag != "none":
                    if rec.stage_id.x_stage_as_tag == "add":
                        for tags in rec.stage_id.x_tag_ids:
                            rec.tag_ids = [(4, tags.id)]
                    elif rec.stage_id.x_stage_as_tag == "replace":
                        rec.tag_ids = rec.stage_id.x_tag_ids
                # Update Task Subtasks
                task_subtasks = rec.x_subtask_list.mapped('x_name')
                subtask_list = []
                for subtask in rec.stage_id.x_subtask_list:
                    if subtask.x_name not in task_subtasks or not task_subtasks:
                        subtask_list.append((0, 0, {
                            'x_name': subtask.x_name,
                            'x_user_id': subtask.x_user_id.id,
                            'x_user_participants': subtask.x_user_participants.ids,
                            'x_user_observers': subtask.x_user_observers.ids,
                            'x_project_id': subtask.x_project_id.id,
                            'x_project_stage_id': subtask.x_project_stage_id.id,
                            'x_planned_hours': subtask.x_planned_hours,
                            'x_notes': subtask.x_notes,
                            'x_checklist_items': subtask.x_checklist_items.ids,
                        }))
                rec.x_subtask_list = subtask_list
                if rec.x_subtask_list:
                    rec.x_subtask_list_hide = False
                else:
                    rec.x_subtask_list_hide = True

    @api.onchange('x_user_stage_id')
    def onchange_user_stage_id(self):
        for rec in self:
            if self.env.uid in rec.x_user_observers.ids and self.env.uid not in rec.x_user_participants.ids and rec.user_id.id != 28 and self.env.uid != rec.user_id:
                raise UserError(_('Error: Observer cannot change the task stage!'))
            elif rec.x_user_stage_id:
                # Update Task State
                if rec.x_user_stage_id.x_mark_status_as:
                    rec.kanban_state = rec.x_user_stage_id.x_mark_status_as
                else:
                    rec.kanban_state = 'pending'
                # Update Task Tags
                if rec.x_user_stage_id.x_stage_as_tag != "none":
                    if rec.x_user_stage_id.x_stage_as_tag == "add":
                        for tags in rec.x_user_stage_id.x_tag_ids:
                            rec.tag_ids = [(4, tags.id)]
                    elif rec.x_user_stage_id.x_stage_as_tag == "replace":
                        rec.tag_ids = rec.x_user_stage_id.x_tag_ids
                # Update Task Subtasks
                task_subtasks = rec.x_subtask_list.mapped('x_name')
                subtask_list = []
                for subtask in rec.x_user_stage_id.x_subtask_list:
                    if subtask.x_name not in task_subtasks or not task_subtasks:
                        subtask_list.append((0, 0, {
                            'x_name': subtask.x_name,
                            'x_user_id': subtask.x_user_id.id,
                            'x_user_participants': subtask.x_user_participants.ids,
                            'x_user_observers': subtask.x_user_observers.ids,
                            'x_project_id': subtask.x_project_id.id,
                            'x_project_stage_id': subtask.x_project_stage_id.id,
                            'x_planned_hours': subtask.x_planned_hours,
                            'x_notes': subtask.x_notes,
                            'x_checklist_items': subtask.x_checklist_items.ids,
                        }))
                rec.x_subtask_list = subtask_list
                if rec.x_subtask_list:
                    rec.x_subtask_list_hide = False
                else:
                    rec.x_subtask_list_hide = True

    @api.onchange('project_id')
    def onchange_project_id(self):
        for rec in self:
            if rec.project_id:
                rec.x_user_participants = rec.project_id.x_default_participant_ids
                rec.x_user_observers = rec.project_id.x_default_observer_ids

    @api.onchange('date_deadline')
    def onchange_date_deadline(self):
        for rec in self:
            if not rec.date_deadline:
                rec.x_deadline_stage = 'no_deadline'
            elif rec.date_deadline < datetime.date.today():
                rec.x_deadline_stage = 'overdue'
            elif rec.date_deadline == datetime.date.today():
                rec.x_deadline_stage = 'due_today'
            elif rec.date_deadline.strftime('%W') == datetime.date.today().strftime('%W'):
                rec.x_deadline_stage = 'due_this_week'
            elif int(rec.date_deadline.strftime('%W')) == int(datetime.date.today().strftime('%W')) + 1:
                rec.x_deadline_stage = 'due_next_week'
            elif int(rec.date_deadline.strftime('%W')) > int(datetime.date.today().strftime('%W')) + 1:
                rec.x_deadline_stage = 'due_over_two_weeks'
            rec.x_deadline_days = (rec.date_deadline - datetime.date.today()).days if rec.date_deadline else 0

    # ============================================= CONSTRAINS =============================================
    @api.model
    @api.constrains('x_user_stage_id')
    def toggle_start(self):
        if self.x_user_stage_id.x_start_timer:
            self.write({'is_user_working': True})
            time_line = self.env['account.analytic.line']
            for time_sheet in self:
                time_line.create({
                    'name': self.env.user.name + ': ' + time_sheet.name,
                    'task_id': time_sheet.id,
                    'user_id': self.env.user.id,
                    'project_id': time_sheet.project_id.id,
                    'date_start': datetime.datetime.now(),
                })
        elif self.x_user_stage_id.x_pause_timer:
            self.write({'is_user_working': False})
            time_line_obj = self.env['account.analytic.line']
            domain = [('task_id', 'in', self.ids), ('date_end', '=', False)]
            for time_line in time_line_obj.search(domain):
                time_line.write({'date_end': fields.Datetime.now()})
                if time_line.date_end:
                    diff = fields.Datetime.from_string(time_line.date_end) - fields.Datetime.from_string(
                        time_line.date_start)
                    time_line.timer_duration = round(diff.total_seconds() / 60.0, 2)
                    time_line.unit_amount = round(diff.total_seconds() / (60.0 * 60.0), 2)
                else:
                    time_line.unit_amount = 0.0
                    time_line.timer_duration = 0.0

    @api.constrains('user_id')
    def update_user_stage(self):
        for rec in self:
            stage_id = self.env['project.task.type'].search(
                [('name', '=', 'New'), ('stage_usage', '=', 'responsible'), ('project_ids', '=', False)], limit=1)
            rec.x_user_stage_id = stage_id.id if stage_id else False

    @api.constrains('parent_id')
    def update_parent_task(self):
        for rec in self:
            update_parent_task = True
            tasks = self.env['project.task'].search([])
            for task in tasks:
                if task.x_subtask_list:
                    for subtask in task.x_subtask_list:
                        if rec.id == subtask.x_created_task_id.id and not rec.parent_id:
                            subtask.sudo().unlink()
                        elif rec.id == subtask.x_created_task_id.id and rec.parent_id.id != subtask.x_task_id.id:
                            subtask.sudo().unlink()
                        elif rec.id == subtask.x_created_task_id.id and rec.parent_id.id == subtask.x_task_id.id:
                            update_parent_task = False

            if rec.parent_id and update_parent_task:
                rec.parent_id.x_subtask_list = [(0, 0, {
                    'x_task_id': rec.parent_id.id,
                    'x_name': rec.name,
                    'state': 'created',
                    'x_user_id': rec.user_id.id,
                    'x_user_participants': rec.x_user_participants,
                    'x_user_observers': rec.x_user_observers,
                    'x_deadline': rec.date_deadline,
                    'x_project_id': rec.project_id.id,
                    'x_project_stage_id': rec.stage_id.id,
                    'x_created_task_id': rec.id,
                    'x_planned_hours': rec.planned_hours,
                })]
                rec.parent_id.x_subtask_list_hide = False

    @api.constrains('x_subtask_list')
    def constrains_subtask_list(self):
        for rec in self:
            if not rec.x_subtask_list:
                rec.x_subtask_list_hide = True
            # Create Subtask
            if rec.stage_id:
                for subtask in rec.x_subtask_list:
                    if not subtask.x_created_task_id and subtask.x_project_stage_id:
                        if rec.stage_id.id == subtask.x_project_stage_id.id:
                            vals = {
                                'name': str(rec.name) + ': ' + str(subtask.x_name),
                                'project_id': subtask.x_project_id.id,
                                'stage_id': subtask.x_project_stage_id.id,
                                'user_id': subtask.x_user_id.id,
                                'x_user_participants': subtask.x_user_participants.ids,
                                'x_user_observers': subtask.x_user_observers.ids,
                                'x_start_task_on': date.today(),
                                'date_deadline': subtask.x_deadline,
                                'x_notes': subtask.x_notes,
                            }
                            task = self.env['project.task'].create(vals)
                            for checklist in subtask.x_checklist_items:
                                task.subtask_ids = [(0, 0, {
                                    'task_id': task.id,
                                    'name': checklist.x_name,
                                    'user_id': task.user_id.id,
                                    'deadline': subtask.x_deadline,
                                })]
                            subtask.x_created_task_id = task.id
                            subtask.state = 'created'
                            task.parent_id = rec.id

    @api.constrains('stage_id')
    def update_subtask_list(self):
        for rec in self:
            if rec.stage_id:
                for subtask in rec.x_subtask_list:
                    if not subtask.x_created_task_id and subtask.x_project_stage_id:
                        if rec.stage_id.id == subtask.x_project_stage_id.id:
                            vals = {
                                'name': subtask.x_name,
                                'project_id': subtask.x_project_id.id,
                                'stage_id': subtask.x_project_stage_id.id,
                                'user_id': subtask.x_user_id.id,
                                'x_user_participants': subtask.x_user_participants.ids,
                                'x_user_observers': subtask.x_user_observers.ids,
                                'x_start_task_on': date.today(),
                                'date_deadline': subtask.x_deadline,
                                'x_notes': subtask.x_notes,
                            }
                            task = self.env['project.task'].create(vals)
                            for checklist in subtask.x_checklist_items:
                                task.subtask_ids = [(0, 0, {
                                    'task_id': task.id,
                                    'name': checklist.x_name,
                                    'user_id': task.user_id.id,
                                    'deadline': subtask.x_deadline,
                                })]
                            subtask.x_created_task_id = task.id
                            subtask.state = 'created'
                            task.parent_id = rec.id

    # ============================================= FUNCTIONS =============================================
    @api.model
    def update_deadline_stage_and_days(self):
        self.env['project.task'].search([('date_deadline', '=', False)]).write({'x_deadline_stage': 'no_deadline'})
        task_ids = self.env['project.task'].search([('date_deadline', '!=', False)])
        task_ids.filtered(lambda l: l.date_deadline < datetime.date.today()).write({'x_deadline_stage': 'overdue'})
        task_ids.filtered(lambda l: l.date_deadline == datetime.date.today()).write({'x_deadline_stage': 'due_today'})
        task_ids.filtered(lambda l: l.date_deadline.strftime('%W') == datetime.date.today().strftime('%W'))\
            .write({'x_deadline_stage': 'due_this_week'})
        task_ids.filtered(lambda l: int(l.date_deadline.strftime('%W')) == int(datetime.date.today().strftime('%W')) + 1)\
            .write({'x_deadline_stage': 'due_next_week'})
        task_ids.filtered(lambda l: int(l.date_deadline.strftime('%W')) > int(datetime.date.today().strftime('%W')) + 1)\
            .write({'x_deadline_stage': 'due_over_two_weeks'})

        for rec in task_ids:
            rec.x_deadline_days = (rec.date_deadline - datetime.date.today()).days if rec.date_deadline else 0

    def update_tag_ids(self):
        action = self.env.ref('customizations.action_update_task_tags').read()[0]
        return action

    def copy_record(self):
        for rec in self:
            rec.copy()

    def _compute_duration(self):
        self

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    def follow_task(self):
        for rec in self:
            if rec.user_id.id != self.env.uid and self.env.uid not in rec.x_user_observers.ids:
                rec.x_user_observers = [(4, self.env.uid)]

    def assist_task(self):
        for rec in self:
            if rec.user_id.id != self.env.uid and self.env.uid not in rec.x_user_participants.ids:
                rec.x_user_participants = [(4, self.env.uid)]

    def poke_button(self):
        for rec in self:
            rec.x_poked = True
            rec.x_poke_counter += 1
            rec.sequence = 0

    def action_project(self):
        action = self.env.ref('customizations.act_project_task_2_project_task_all').read()[0]

        # only display tasks of current project
        action['domain'] = [('project_id', '=', self.project_id.id)]
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_project_id': [self.project_id.id],
            'search_default_trackbot_task': 1,
            'search_default_pending_task': 1,
            'search_default_normal_task': 1,
            'search_default_blocked_task': 1,
            'default_company_id': self.project_id.company_id.id,
            'default_project_id': self.project_id.id,
            'default_user_id': self.env.uid,
        })
        action['context'] = ctx

        return action

    def add_checklist(self):
        for rec in self:
            rec.subtask_ids = [(0, 0, {
                'task_id': rec.id,
                'name': 'Checklist',
                'user_id': rec.user_id.id,
                'deadline': rec.date_deadline,
            })]

    def add_subtask(self):
        for rec in self:
            rec.x_subtask_list_hide = False

    def unlink(self):
        for subtasks in self.x_subtask_list:
            if subtasks.x_created_task_id:
                subtasks.x_created_task_id.sudo().unlink()
        result = super(Task, self).unlink()
        return result

    def write(self, vals):
        old_list = []
        for rec in self:
            for line in rec.x_so_product_ids:
                old_list.append([line.x_line_id.id, line.x_product_id.name, line.x_status.x_name])

        res = super(Task, self).write(vals)

        for rec in self:
            new_list = []
            for line in rec.x_so_product_ids:
                new_list.append([line.x_line_id.id, line.x_product_id.name, line.x_status.x_name])

            body = ''
            for n_line in new_list:
                for o_line in old_list:
                    if o_line[0] == n_line[0] and o_line[2] != n_line[2]:
                        body += '<span><strong>%s</strong> status is changed from ' \
                                '<strong>%s</strong> to <strong>%s</strong></span><br/>' \
                                % (o_line[1], o_line[2], n_line[2])
                        break

            if body != '':
                rec.message_post(message_type="comment", body=body)

        return res


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    def _get_default_stage_usage(self):
        default_stage_usage = self.env.context.get('default_stage_usage')
        return default_stage_usage if default_stage_usage else None

    stage_usage = fields.Selection(selection=[
        ('responsible', 'Responsible'),
        ('assisting', 'Assisting'),
        ('following', 'Following'),
    ], required=False, string="Stage Usage", default=_get_default_stage_usage, )
    x_start_timer = fields.Boolean(string="Start Timer", default=False)
    x_pause_timer = fields.Boolean(string="Pause Timer", default=True)
    x_mark_status_as = fields.Selection(selection=[
        ('pending', 'Pending'),
        ('normal', 'In Progress'),
        ('blocked', 'On Hold'),
        ('done', 'Done'),
    ], string="Mark Status as", required=True, default="pending")
    x_stage_as_tag = fields.Selection(string="Stage as Tag",
                                      selection=[('none', 'None'), ('add', 'Add'), ('replace', 'Replace'), ],
                                      required=True, default="none")
    x_tag_ids = fields.Many2many('project.tags', string=' Stage Tag', compute="_compute_tags", store=True, )
    x_subtask_list = fields.One2many(comodel_name="subtask.list", inverse_name="x_stage_id", string="Subtask List",
                                     required=False, )

    @api.depends('x_stage_as_tag')
    def _compute_tags(self):
        for rec in self:
            if rec.x_stage_as_tag == 'none':
                rec.x_tag_ids = False
            else:
                stage_tag_id = self.env['project.tags'].search([('name', '=', rec.name)]).id
                if not stage_tag_id:
                    stage_tag_id = self.env['project.tags'].create({'name': rec.name, 'color': 1, }).id
                rec.x_tag_ids = [stage_tag_id]


# --------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- Custom Models -------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------


class SaleOrderProductsTask(models.Model):
    _name = "sale.order.products.task"
    _description = "Task Sale Order Products"
    _rec_name = "display_name"

    x_task_id = fields.Many2one(comodel_name='project.task', string='Task', required=False)
    x_line_id = fields.Many2one(comodel_name='sale.order.line', string='Sale Order Lines', required=False)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', related="x_line_id.product_id")
    x_product_qty = fields.Float(string='Quantity', related="x_line_id.product_uom_qty")
    x_status = fields.Many2one(comodel_name='sale.order.products.status', string='Status', required=False)

    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends('x_product_id', 'x_product_qty', 'x_status')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s (Qty: %s) [%s]" % (rec.x_product_id.name,
                                                      round(rec.x_product_qty, 0), rec.x_status.x_name)


class SaleOrderProductsStatus(models.Model):
    _name = "sale.order.products.status"
    _description = "Sale Order Products Status"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)


class SubtaskList(models.Model):
    _name = "subtask.list"
    _description = "Subtask List"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True, )
    x_task_id = fields.Many2one(comodel_name="project.task", string="Task ID", required=False, )
    x_stage_id = fields.Many2one(comodel_name="project.task.type", string="Stage ID", required=False, )
    x_project_id = fields.Many2one(comodel_name="project.project", string="Project", required=True, )
    x_project_stage_id = fields.Many2one(comodel_name="project.task.type", string="Project Stage", required=True,
                                         domain="[('project_ids','ilike',x_project_id)]", )
    x_user_id = fields.Many2one(comodel_name="res.users", string="Assigned to", required=True,
                                default=lambda self: self.env.uid, )
    x_user_participants = fields.Many2many(comodel_name="res.users", relation="res_users_subtask_list_rel_1",
                                           column1="subtask_list_id", column2="res_users_id", string="Participants", )
    x_user_observers = fields.Many2many(comodel_name="res.users", relation="res_users_subtask_list_rel_2",
                                        column1="subtask_list_id", column2="res_users_id", string="Observers", )
    x_notes = fields.Text(string="Notes", required=False, )
    x_checklist_items = fields.Many2many(comodel_name="checklist.items", relation="subtask_list_checklist_items_rel",
                                         column1="subtask_list_id", column2="checklist_items_id",
                                         string="Checklist Items", )
    x_deadline = fields.Date(string="Deadline", required=False, )
    state = fields.Selection(selection=[
        ('started', 'Started'),
        ('finished', 'Finished'),
        ('overdue', 'Overdue'),
        ('created', 'Created'),
        ('not_created', 'Not Created'),
    ], required=False, store=True, default="not_created", string="Status", compute="_update_task_status", )
    x_created_task_id = fields.Many2one(comodel_name="project.task", string="Created Task", required=False, )
    x_planned_hours = fields.Float(string="Planned Hours", required=False, )

    @api.model
    def create(self, vals):
        res = super(SubtaskList, self).create(vals)
        for rec in self:
            if rec.x_project_stage_id.id == rec.x_task_id.stage_id.id:
                rec.poke_button()
        return res

    @api.depends('x_created_task_id.x_poke', )
    def _update_poke_status(self):
        for rec in self:
            if rec.x_created_task_id:
                rec.x_poke = "not_poked" if rec.x_created_task_id.x_poke == "not_poked" else "poked"
            else:
                rec.x_poke = "not_poked"

    @api.depends('x_created_task_id', 'x_created_task_id.kanban_state', 'x_created_task_id.date_deadline',
                 'x_created_task_id.stage_id', )
    def _update_task_status(self):
        for rec in self:
            if rec.x_created_task_id:
                if rec.x_created_task_id.kanban_state == 'done':
                    rec.state = 'finished'
                elif rec.x_created_task_id.date_deadline:
                    if rec.x_created_task_id.date_deadline < date.today():
                        rec.state = 'overdue'
                elif rec.x_created_task_id.kanban_state == 'pending':
                    rec.state = 'created'
                elif rec.x_created_task_id.kanban_state != 'normal':
                    rec.state = 'started'
            elif not rec.x_created_task_id:
                rec.state = 'not_created'

    def poke_button(self):
        for rec in self:
            if not rec.x_created_task_id:
                vals = {
                    'name': rec.x_name,
                    'project_id': rec.x_project_id.id,
                    'stage_id': rec.x_project_stage_id.id,
                    'user_id': rec.x_user_id.id,
                    'x_user_participants': rec.x_user_participants.ids,
                    'x_user_observers': rec.x_user_observers.ids,
                    'x_start_task_on': datetime.datetime.now(),
                    'date_deadline': rec.x_deadline,
                    'x_notes': rec.x_notes,
                    'planned_hours': rec.x_planned_hours,
                    'x_poked': True,
                    'x_poke_counter': 1,
                    'sequence': 0,
                }
                task = self.env['project.task'].create(vals)
                for checklist in rec.x_checklist_items:
                    task.subtask_ids = [(0, 0, {
                        'task_id': task.id,
                        'name': checklist.x_name,
                        'user_id': task.user_id.id,
                        'deadline': task.date_deadline,
                    })]
                rec.x_created_task_id = task.id
                rec.state = 'created'
                task.parent_id = rec.x_task_id.id
            elif rec.x_created_task_id:
                rec.x_created_task_id.x_poked = True
                rec.x_created_task_id.x_poke_counter += 1
                rec.x_created_task_id.sequence = 0


class TaskQuickCreateFormFields(models.Model):
    _name = "task.quick.create.form.fields"
    _description = "Task Quick Create Form Fields"
    _rec_name = "x_sequence"

    x_project_id = fields.Many2one(comodel_name="project.project", string="Project", required=False, )
    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_field_id = fields.Many2one(comodel_name="ir.model.fields", string="Field", required=True,
                                 domain=[('model_id', '=', 410)], )
    x_name = fields.Char(string="Label", required=True, )
    x_required = fields.Boolean(string="Required", )

    @api.onchange('x_field_id')
    def _onchange_field_id(self):
        for rec in self:
            rec.x_name = rec.x_field_id.field_description


class TaskConditions(models.Model):
    _name = "task.conditions"
    _description = "Conditions"







