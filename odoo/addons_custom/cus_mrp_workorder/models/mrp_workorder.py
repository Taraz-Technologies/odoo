from odoo import models, fields, api, SUPERUSER_ID
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger("*__addons_custom__*")


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', tracking=True,
                              readonly=False, states={'done': [('readonly', True)]})
    x_user_ids = fields.Many2many(comodel_name='res.users', string='Participants',
                                  readonly=False, states={'done': [('readonly', True)]})
    x_mrp_demand_ids = fields.One2many(related="production_id.x_mrp_demand_ids")

    x_need_material = fields.Text(string='Need Material?', tracking=True, states={'done': [('readonly', True)]})
    x_is_need_material = fields.Boolean(string='Need Material Check')
    x_need_attention = fields.Text(string="Needs Attention?", tracking=True, states={'done': [('readonly', True)]})
    x_is_need_attention = fields.Boolean(string='Need Attention Check')

    x_workorder_id = fields.Many2one(comodel_name='mrp.workorder', string='Interrupted by WO', tracking=True)
    x_production_id = fields.Many2one(related="x_workorder_id.production_id", string="Interrupted by MO")
    x_name = fields.Char(related="x_workorder_id.name", string="Interrupted by WO name")

    x_production_type = fields.Selection(selection=[
        ('full', 'Full'),
        ('partial', 'Partial'),
    ], string="Production", default='full')

    # QC Fields
    x_qc_status = fields.Selection(selection=[
        ('pass', 'Pass'),
        ('rework', 'Re-work'),
        ('fail', 'Fail'),
    ], string='QC Status', tracking=True, compute="_compute_qc_status", store=True)

    x_qc_comment = fields.Text(string="QC Comment", tracing=True, states={'done': [('readonly', True)]})
    x_is_qc_comment = fields.Boolean(string='QC Comment Check')

    x_serial_product_ids = fields.One2many(comodel_name='serial.number', inverse_name='x_workorder_id',
                                           string='Serial Products', states={'done': [('readonly', True)]})

    x_custom_tag_ids = fields.Many2many('custom.tags', string="Tags")

    @api.depends('x_serial_product_ids.x_status')
    def _compute_qc_status(self):
        for rec in self:
            serial_product_ids = self.env['serial.number'].search([('x_workorder_id', '=', rec.id)]).mapped('x_status')
            if any(status == 'fail' for status in serial_product_ids):
                qc_status = 'fail'
            elif any(status == 'rework' for status in serial_product_ids):
                qc_status = 'rework'
            elif all(status == 'pass' for status in serial_product_ids):
                qc_status = 'pass'
            else:
                qc_status = False
            rec.x_qc_status = qc_status

    @api.onchange('x_need_material')
    def onchange_need_material(self):
        for rec in self:
            rec.x_is_need_material = True if rec.x_need_material != '' else False

    @api.onchange('x_need_attention')
    def onchange_need_attention(self):
        for rec in self:
            rec.x_is_need_attention = True if rec.x_need_attention != '' else False

    @api.onchange('x_qc_comment')
    def onchange_qc_comment(self):
        for rec in self:
            rec.x_is_qc_comment = True if rec.x_qc_comment else False

    @api.onchange('production_id', 'workcenter_id')
    def get_serial_products(self):
        for rec in self:
            if rec.workcenter_id.id == 17:
                rec.production_id.x_serial_numbers.update({'x_workorder_id': rec._origin.id})

    @api.onchange('x_workorder_id')
    def _onchange_x_workorder_id(self):
        if self.x_workorder_id and self.is_user_working:
            self.button_pending()

    @api.model
    def _read_group_state(self, stages, domain, order):
        return ['pending', 'ready', 'progress', 'done', 'cancel']

    state = fields.Selection(selection_add=[], tracking=True, group_expand='_read_group_state')

    # @api.model
    # def _read_group_stage_ids(self, stages, domain, order):
    #     stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
    #     return stages.browse(stage_ids)
    #
    # stage_id = fields.Many2one(
    #     comodel_name='mrp.workorder.stage', string='Stage', tracking=True, copy=False,
    #     group_expand='_read_group_stage_ids', index=True, store=True, compute='_compute_stage_id'
    # )
    #
    # @api.depends('state')
    # def _compute_stage_id(self):
    #     for workorder in self:
    #         if workorder.state in ('progress', 'done'):
    #             workorder.stage_id = self.env['mrp.workorder.stage'].search([(
    #                 'workcenter_id', '=', workorder.workcenter_id.id
    #             )], order='sequence', limit=1)
    #         else:
    #             workorder.stage_id = False

    def write(self, vals):
        old_values = self.x_custom_tag_ids.ids
        res = super(MrpWorkorder, self).write(vals)
        new_values = self.x_custom_tag_ids.ids
        if 'x_custom_tag_ids' in vals:
            self.x_custom_tag_ids._track_many2many_changes(
                self, 'x_custom_tag_ids', old_values=old_values, new_values=new_values
            )
        return res

    @api.model
    def create(self, vals_list):
        res = super(MrpWorkorder, self).create(vals_list)
        workcenter_id = self.env['mrp.workcenter'].browse(vals_list.get('workcenter_id'))
        res.update({
            'user_id': workcenter_id.user_id.id
        })
        # if 'x_custom_tag_ids' in vals_list:
        #     self.x_custom_tag_ids._track_many2many_changes(
        #         res, 'x_custom_tag_ids', new_values=vals_list['x_custom_tag_ids']
        #     )
        return res


    def action_view_production_order(self):
        for rec in self:
            action = self.env.ref('mrp.mrp_production_action').read()[0]
            return dict(action, view_mode='form', res_id=rec.production_id.id, views=[(False, 'form')])


    def record_production(self):
        for rec in self:
            if rec.x_is_need_material:
                raise UserError("Please clear 'Need Material?' text box in order to 'Done' this WO!")
            elif rec.x_is_need_attention:
                raise UserError("Please clear 'Need Attention?' text box in order to 'Done' this WO!")
        return super(MrpWorkorder, self).record_production()
