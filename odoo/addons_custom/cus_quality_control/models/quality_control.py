from odoo import fields, models, api
from odoo.exceptions import UserError


class QualityControl(models.Model):
    _name = "quality.control"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quality Control"
    _rec_name = "x_product_id"

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'),
    ], string='Status', default='draft', )

    x_manufacturing_id = fields.Many2one(comodel_name='mrp.production', string='Manufacturing Order', tracking=True)
    x_product_id = fields.Many2one(related="x_manufacturing_id.product_id")
    x_bom_tool_id = fields.Many2one(related="x_manufacturing_id.x_bom_tool_id")
    x_mrp_demand_ids = fields.One2many(related="x_manufacturing_id.x_mrp_demand_ids")

    x_serial_product_ids = fields.Many2many(comodel_name='serial.number', string='Product with Serial Numbers',
                                            compute="get_serial_products", store=True, readonly=False)
    x_checklist_ids = fields.Many2many(comodel_name='bom.tool.qc.checklist', string='Check List')
    x_qc_complete = fields.Boolean(compute="check_qc_status", store=True)
    x_quantity = fields.Float(string='Quantity', required=False)

    x_department_ids = fields.Many2many(comodel_name='hr.department', string='Departments')
    x_fine_amount = fields.Float(string='Fine Amount', required=False)
    x_split_by = fields.Selection(selection=[
        ('equally', 'Equally'), ('by_share', 'By Share'), ('by_percentage', 'By Percentage'),
    ], string='Split By', default='equally', required=True, )
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency',
                                    default=lambda self: self.env.ref('base.USD').id)

    x_stock_valuation_layer_id = fields.Many2one(comodel_name='stock.valuation.layer', string='Valuation', required=False)

    x_distribute_fine = fields.Boolean(compute="distribute_production_fine", store=True)

    x_employee_ids = fields.One2many(comodel_name='qc.employee.fines', inverse_name='x_quality_id', string='Employees')

    x_deadline = fields.Datetime(string='Deadline', compute='_compute_deadline', store=True)

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    @api.depends('x_manufacturing_id', 'x_manufacturing_id.date_deadline')
    def _compute_deadline(self):
        for rec in self:
            rec.x_deadline = rec.x_manufacturing_id.date_deadline

    @api.depends('x_department_ids', 'x_fine_amount', 'x_split_by')
    def distribute_production_fine(self):
        for rec in self:
            if rec.x_split_by == 'equally':
                fine = rec.x_fine_amount / len(rec.x_employee_ids) if len(rec.x_employee_ids) != 0 else 0
                rec.x_employee_ids.write({'x_fine_amount': fine})
            elif rec.x_split_by == 'by_share':
                total_shares = sum(rec.x_employee_ids.mapped('x_share'))
                for employee in rec.x_employee_ids:
                    employee.x_fine_amount = rec.x_fine_amount * employee.x_share / total_shares if total_shares != 0 else 0
            elif rec.x_split_by == 'by_percentage':
                for employee in rec.x_employee_ids:
                    employee.x_fine_amount = rec.x_fine_amount * employee.x_percentage / 1
            else:
                rec.x_employee_ids.write({'x_fine_amount': 0})

    @api.onchange('x_department_ids')
    def get_employees(self):
        for rec in self:
            rec.x_employee_ids = [(2, line.id) for line in rec.x_employee_ids]
            employee_ids = self.env['hr.employee'].search([
                ('department_id', 'in', rec.x_department_ids.ids), ('contract_warning', '=', False)
            ])
            employee_lines = []
            for employee in employee_ids:
                employee_lines.append((0, 0, {'x_employee_id': employee.id}))
            rec.x_employee_ids = employee_lines

    @api.depends('x_manufacturing_id')
    def get_serial_products(self):
        for rec in self:
            rec.x_serial_product_ids.x_qc_checklist_ids = \
                [(2, line.id) for line in rec.x_serial_product_ids.mapped('x_qc_checklist_ids')]

            qc_ids = self.env['quality.control'].sudo().search([('x_manufacturing_id', '=', rec.x_manufacturing_id.id)])
            if qc_ids:
                qc_quantity = sum(qc_ids.mapped('x_quantity'))
                serial_numbers = ['0000%s' % (x + 1) for x in range(int(qc_quantity - rec.x_quantity), int(qc_quantity))]
                serial_numbers = ['-%s' % serial_number[-4:] for serial_number in serial_numbers]
            else:
                serial_numbers = ['0000%s' % (x + 1) for x in range(int(rec.x_quantity))]
                serial_numbers = ['-%s' % serial_number[-4:] for serial_number in serial_numbers]

            rec.x_serial_product_ids = [(5, 0)]
            for line in rec.x_manufacturing_id.x_serial_numbers:
                if line.x_serial_number[-5:] in serial_numbers:
                    rec.x_serial_product_ids = [(4, line.id)]
            rec.x_serial_product_ids.get_qc_checklist()

    @api.depends('x_serial_product_ids.x_status')
    def check_qc_status(self):
        for rec in self:
            rec.x_qc_complete = False if False in rec.x_serial_product_ids.mapped('x_status') else True

    def set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def start_qc(self):
        for rec in self:
            rec.state = 'in_progress'

    def mark_as_done(self):
        for rec in self:
            rec.create_internal_transfer()

    def mark_as_done_with_complete_qc(self):
        for rec in self:
            rec.create_internal_transfer()
            serial_product_ids = rec.x_serial_product_ids.filtered(lambda l: not l.x_status)
            serial_product_ids.write({'x_status': 'pass'})
            qc_checklist_ids = serial_product_ids.mapped('x_qc_checklist_ids').filtered(lambda l: not l.x_status)
            qc_checklist_ids.write({'x_status': 'pass'})

    def create_internal_transfer(self):
        for rec in self:
            rec.state = 'done'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("You can not delete a Quality Control that is not in draft state.")
        return super(QualityControl, self).unlink()


class QcEmployeeFines(models.Model):
    _name = 'qc.employee.fines'
    _description = 'QC Employee Fines'

    x_quality_id = fields.Many2one(comodel_name='quality.control', string='Quality Control', required=False)
    x_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=False)
    x_share = fields.Float(string='Share', required=False)
    x_percentage = fields.Float(string='Percentage', required=False)
    x_currency_id = fields.Many2one(related="x_quality_id.x_currency_id")
    x_fine_amount = fields.Float(string='Fine Amount', required=False)

    @api.onchange('x_share', 'x_percentage')
    def compute_amount(self):
        for rec in self:
            rec.x_quality_id.distribute_production_fine()
