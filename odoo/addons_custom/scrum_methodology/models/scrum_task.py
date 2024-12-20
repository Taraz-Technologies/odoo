from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError


class ScrumTaskType(models.Model):
    _name = 'scrum.task.type'
    _description = 'Task Stage'
    _rec_name = 'x_name'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_name = fields.Char(string='Stage Name', required=True, translate=True)
    x_description = fields.Text(string="Description", translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    x_ready_stage = fields.Boolean(
        string='Ready Stage',
        help='When task is complete and ready to review.')
    x_last_stage = fields.Boolean(
        string='Last Stage',
        help='When all tasks of project are in this stage then project will be in its last stage.')

    @api.constrains('x_last_stage')
    def _check_last_stage(self):
        if self.env['scrum.task.type'].search_count([('x_last_stage', '=', True)]) > 1:
            raise UserError('You cannot set more than one last stage!')


class ScrumTask(models.Model):
    _name = "scrum.task"
    _description = "Task"
    _rec_name = "x_name"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    x_stage_id = fields.Many2one(comodel_name='scrum.task.type', string='Stage', tracking=True, copy=False,
                                 group_expand='_read_group_stage_ids')
    x_name = fields.Char(string='Title', tracking=True, required=True, index=True)
    x_priority = fields.Selection(selection=[
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0', index=True, string="Priority", tracking=True)
    x_task_weightage = fields.Selection(selection=[
        ('00', '00'),
        ('01', '01'),
        ('02', '02'),
        ('03', '03'),
        ('04', '04'),
        ('05', '05'),
        ('06', '06'),
        ('07', '07'),
        ('08', '08'),
        ('09', '09'),
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
    ], string='Weightage', required=False, help="TW: Task Weightage", default="00")
    x_weightage = fields.Integer(string='Task Weightage', compute="_compute_weightage", store=True)
    x_user_id = fields.Many2one(comodel_name='res.users', string='Assigned to', tracking=True)
    x_user_ids = fields.Many2many(comodel_name='res.users', string='Participants')
    x_sequence = fields.Integer(string='Sequence', index=True, default=10, tracking=True)
    x_project_id = fields.Many2one(comodel_name='scrum.project', string='Project', tracking=True)
    x_department_id = fields.Many2one(related="x_project_id.x_department_id", store=True)
    x_description = fields.Text(string="Description", tracking=True)

    def write(self, vals):
        backlog_stage_id = self.env.ref('scrum_methodology.scrum_task_stage_1')
        sprint_backlog_stage_id = self.env.ref('scrum_methodology.scrum_task_stage_2')

        for record in self:
            if (
                    record.x_stage_id == backlog_stage_id and
                    vals.get('x_stage_id') == sprint_backlog_stage_id.id
            ):
                vals['x_user_id'] = self.env.uid  # Set to the current user ID
        return super(ScrumTask, self).write(vals)

    @api.depends('x_task_weightage')
    def _compute_weightage(self):
        for rec in self:
            rec.x_weightage = int(rec.x_task_weightage)
            selection_field = self._fields['x_task_weightage']
            print(selection_field.selection)

    def increase_weightage(self):
        selection_field = self._fields['x_task_weightage']
        index = next((i for i, t in enumerate(selection_field.selection) if t[0] == self.x_task_weightage), -1)
        if index + 1 == len(selection_field.selection):
            return
        self.x_task_weightage = selection_field.selection[index + 1][0]

    def decrease_weightage(self):
        selection_field = self._fields['x_task_weightage']
        index = next((i for i, t in enumerate(selection_field.selection) if t[0] == self.x_task_weightage), -1)
        if index == 0:
            return
        self.x_task_weightage = selection_field.selection[index - 1][0]

