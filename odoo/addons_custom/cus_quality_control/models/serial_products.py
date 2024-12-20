from odoo import fields, models, api


class SerialNumber(models.Model):
    _inherit = "serial.number"

    x_status = fields.Selection(selection=[
        ('pass', 'Pass'), ('rework', 'Rework'), ('rework_w_fine', 'Rework (Fine)'), ('fail', 'Fail'),
    ], string='Status', readonly=False, compute='_compute_status', store=True)

    x_qc_checklist_ids = fields.One2many(comodel_name='qc.checklist', inverse_name='x_serial_product_id',
                                         string='QC Checklist', required=False)

    x_notes = fields.Text(string="Notes", required=False)

    def get_qc_checklist(self):
        for rec in self:
            rec.x_qc_checklist_ids = [(2, line.id) for line in rec.x_qc_checklist_ids]
            qc_checklist_ids = []
            for line in rec.x_manufacturing_id.x_bom_tool_id.x_qc_checklist_ids:
                qc_checklist_ids.append((0, 0, {
                    'x_checklist': line.x_checklist,
                    'x_description': line.x_description,
                    'x_notes': line.x_notes,
                    'x_typical_value': line.x_typical_value,
                }))
            rec.x_qc_checklist_ids = qc_checklist_ids

    @api.depends('x_qc_checklist_ids', 'x_qc_checklist_ids.x_status')
    def _compute_status(self):
        for rec in self:
            if all(status == 'pass' for status in rec.x_qc_checklist_ids.mapped('x_status')):
                rec.x_status = 'pass'
            elif any(status == 'fail' for status in rec.x_qc_checklist_ids.mapped('x_status')):
                rec.x_status = 'fail'


class QcChecklist(models.Model):
    _name = 'qc.checklist'
    _description = "QC Checklist"

    x_serial_product_id = fields.Many2one(comodel_name='serial.number', string='Serial Product', required=False)

    x_checklist = fields.Char(string='Checklist', required=False)
    x_description = fields.Text(string='Description', required=False)
    x_notes = fields.Text(string='Notes', required=False)
    x_typical_value = fields.Char(string='Typical Value', required=False)

    x_measured_value = fields.Char(string='Measured Value', required=False)
    x_status = fields.Selection(selection=[('pass', 'Pass'), ('fail', 'Fail')], string='Status', required=False, )











