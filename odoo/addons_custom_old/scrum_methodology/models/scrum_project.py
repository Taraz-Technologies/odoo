from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError


class ScrumProjectType(models.Model):
    _name = 'scrum.project.type'
    _description = 'Project Stage'
    _rec_name = 'x_name'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_name = fields.Char(string='Stage Name', required=True, translate=True)
    x_description = fields.Text(string="Description", translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    x_stage_id = fields.Many2one(
        comodel_name='scrum.task.type',
        string='Task Stage',
        help='When project is move to this stage tasks of that project will move to the stage defined here.')
    x_default_stage = fields.Boolean(
        string='Default Stage',
        help='Default stage for new projects.')
    x_last_stage = fields.Boolean(
        string='Last Stage',
        help='When all tasks of project are in their last stage then project will be in this stage.')

    @api.constrains('x_default_stage')
    def _check_last_stage(self):
        if self.env['scrum.project.type'].search_count([('x_default_stage', '=', True)]) > 1:
            raise UserError('You cannot set more than one default stage!')

    @api.constrains('x_last_stage')
    def _check_last_stage(self):
        if self.env['scrum.project.type'].search_count([('x_last_stage', '=', True)]) > 1:
            raise UserError('You cannot set more than one last stage!')


class ScrumProject(models.Model):
    _name = "scrum.project"
    _description = "Project"
    _rec_name = "x_name"
    _order = "x_priority desc, x_sequence, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _get_default_stage_id(self):
        return self.env['scrum.project.type'].search([('x_default_stage', '=', True)], limit=1).id

    x_name = fields.Char(string='Title', tracking=True, required=True, index=True)
    x_description = fields.Text(string="Description", tracking=True)
    x_stage_id = fields.Many2one(comodel_name='scrum.project.type', string='Stage', tracking=True, copy=False,
                                 default=_get_default_stage_id, group_expand='_read_group_stage_ids')
    x_task_stage_id = fields.Many2one(related='x_stage_id.x_stage_id')
    x_department_id = fields.Many2one(comodel_name='hr.department', string='Department', tracking=True)
    x_user_id = fields.Many2one(comodel_name='res.users', string='Manager', tracking=True)
    x_user_ids = fields.Many2many(comodel_name='res.users', string='Participants')
    x_sequence = fields.Integer(string='Sequence', index=True, default=10, tracking=True)
    x_priority = fields.Selection(selection=[
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0', index=True, string="Priority", tracking=True)

    x_task_ids = fields.One2many(
        comodel_name='scrum.task', inverse_name='x_project_id', string='All Tasks', required=False,
    )
    x_task1_ids = fields.One2many(
        comodel_name='scrum.task', inverse_name='x_project_id', string='Development Tasks',
        domain=[('x_stage_id.x_ready_stage', '=', False), ('x_stage_id.x_last_stage', '=', False), ('x_stage_id.x_name', '!=', 'IceBox')]
    )
    x_task2_ids = fields.One2many(
        comodel_name='scrum.task', inverse_name='x_project_id', string='Ready Tasks',
        domain=[('x_stage_id.x_ready_stage', '=', True)]
    )
    x_task3_ids = fields.One2many(
        comodel_name='scrum.task', inverse_name='x_project_id', string='Completed Tasks',
        domain=[('x_stage_id.x_last_stage', '=', True)]
    )
    x_task4_ids = fields.One2many(
        comodel_name='scrum.task', inverse_name='x_project_id', string='Delayed Tasks',
        domain=[('x_stage_id.x_name', '=', 'IceBox')]
    )

    @api.depends('x_task_ids')
    def _compute_x_task1_ids(self):
        for rec in self:
            rec.x_task1_ids = rec.x_task_ids.filtered(
                lambda t: not t.x_stage_id.x_last_stage and not t.x_stage_id.x_ready_stage
            )

    @api.depends('x_task_ids')
    def _compute_x_task2_ids(self):
        for rec in self:
            rec.x_task2_ids = rec.x_task_ids.filtered(lambda t: t.x_stage_id.x_ready_stage)

    @api.depends('x_task_ids')
    def _compute_x_task3_ids(self):
        for rec in self:
            rec.x_task3_ids = rec.x_task_ids.filtered(lambda t: t.x_stage_id.x_last_stage)

    x_compute_project_stage_id = fields.Boolean(compute='compute_project_stage_id', store=True)
    x_compute_tasks_stage_id = fields.Boolean(compute='compute_tasks_stage_id', store=True)

    @api.depends('x_task_ids', 'x_task_ids.x_stage_id')
    def compute_project_stage_id(self):
        for rec in self:
            if (all(last_stage for last_stage in rec.x_task_ids.mapped('x_stage_id').mapped('x_last_stage'))
                    and rec.x_task_ids.mapped('x_stage_id')):
                rec.x_stage_id = self.env['scrum.project.type'].search(
                    [('x_last_stage', '=', True)], order='x_sequence desc', limit=1).id

    @api.depends('x_stage_id')
    def compute_tasks_stage_id(self):
        for rec in self:
            if len(rec.x_task_ids.mapped('x_stage_id')) > 1 and rec.x_task_stage_id:
                raise UserError('You cannot change project stage as there are tasks in this project that are in'
                                ' different stages!')
            elif rec.x_task_stage_id:
                rec.x_task_ids.write({'x_stage_id': rec.x_stage_id.x_stage_id.id})

    def unlink(self):
        for rec in self:
            if len(rec.x_task_ids.mapped('x_stage_id')) > 1 and rec.x_task_stage_id:
                raise UserError(
                    'You cannot delete this project as there are tasks in this project that are in different stages!'
                )
            rec.x_task_ids.unlink()
        return super(ScrumProject, self).unlink()
