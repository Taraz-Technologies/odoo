# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')

    @api.model
    def default_get(self, fields_list):
        rec = super(HrPayslipEmployees, self).default_get(fields_list)
        rec.update({
            'employee_ids': self.env['hr.employee'].search([('contract_warning', '=', False)]).ids
        })
        return rec

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            payslip_run = self.env['hr.payslip.run'].browse(active_id)
            [run_data] = payslip_run.read([
                'date_start', 'date_end', 'x_payment_date', 'x_date', 'x_rate', 'credit_note'
            ])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'date': run_data.get('x_date'),
                'x_payment_date': run_data.get('x_payment_date'),
                'x_payroll_rate_id': payslip_run.x_payroll_rate_id.id,
                'x_rate': run_data.get('x_rate'),
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.calculate_work_days_of_month()
        payslips.get_leaves()
        payslips.compute_payslip_data()
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
