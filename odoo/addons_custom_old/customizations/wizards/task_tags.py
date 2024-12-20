# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class TaskTags(models.TransientModel):
    _name = "task.tags"
    _description = "Task Tags"

    x_task_id = fields.Many2one(comodel_name="project.task", string="Task", required=False, )
    x_tag_ids = fields.Many2many('project.tags', string='Tags', related="x_task_id.tag_ids", readonly=False, )

    # @api.model
    # def default_get(self, fields):
    #     res = super(TaskTags, self).default_get(fields)
    #     task_id = self.env.context.get('active_ids')
    #     res.update({
    #         'x_task_id': task_id,
    #     })
    #     return res

    def update_task_tags(self):
        for rec in self:
            rec.x_task_id = rec.x_task_id.id

