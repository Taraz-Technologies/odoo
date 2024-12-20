from odoo import models


class PayrollExcelReport(models.AbstractModel):
    _name = 'report.cus_payroll.payroll_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Payroll Excel Report"

    def generate_xlsx_report(self, workbook, data, objs):
        for obj in objs:
            font_size = workbook.add_format({'font_size': 12})
            sheet = workbook.add_worksheet(obj.name)

            row = 0
            sheet.write(row, 0, 'Employee Name', font_size)
            sheet.write(row, 1, 'Designation', font_size)
            sheet.write(row, 2, 'Account #', font_size)
            sheet.write(row, 3, 'Amount', font_size)
            for slip in obj.slip_ids.filtered(lambda l: l.employee_id.bank_account_id):
                if 'Bank Alfalah' in slip.employee_id.bank_account_id.bank_id.name and slip.x_amount_residual != 0:
                    row += 1
                    sheet.write(row, 0, slip.employee_id.bank_account_id.acc_holder_name, font_size)
                    sheet.write(row, 1, slip.employee_id.x_job_title_id.x_name, font_size)
                    sheet.write(row, 2, slip.employee_id.bank_account_id.acc_number, font_size)
                    sheet.write(row, 3, slip.x_amount_residual, font_size)


class WhtPayrollExcelReport(models.AbstractModel):
    _name = 'report.cus_payroll.wht_payroll_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "WHT Payroll Excel Report"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size = workbook.add_format({'font_size': 12})
        total_sheet_data = []
        for obj in objs:
            sheet = workbook.add_worksheet(obj.name)

            row = 0
            sheet.write(row, 0, 'Employee Name', font_size)
            sheet.write(row, 1, 'Designation', font_size)
            sheet.write(row, 2, 'Gross Salary', font_size)
            sheet.write(row, 3, 'WHT Salary', font_size)
            for slip in obj.slip_ids.filtered(lambda l: l.x_wht_salary != 0):
                employees = [item['employee'] for item in total_sheet_data]
                # employees = total_sheet_data.mapped('Employee')
                if slip.employee_id.name in employees:
                    for item in total_sheet_data:
                        if item['employee'] == slip.employee_id.name:
                            item['gross_salary'] += slip.x_gross_salary
                            item['wht_salary'] += slip.x_wht_salary
                else:
                    total_sheet_data.append({
                        'employee': slip.employee_id.name,
                        'designation': slip.employee_id.x_job_title_id.x_name,
                        'gross_salary': slip.x_gross_salary,
                        'wht_salary': slip.x_wht_salary,
                    })
                row += 1
                sheet.write(row, 0, slip.employee_id.name, font_size)
                sheet.write(row, 1, slip.employee_id.job_id.name, font_size)
                sheet.write(row, 2, slip.x_gross_salary, font_size)
                sheet.write(row, 3, slip.x_wht_salary, font_size)

        if len(objs) > 1:
            sheet = workbook.add_worksheet('Total WHT')

            row = 0
            sheet.write(row, 0, 'Employee Name', font_size)
            sheet.write(row, 1, 'Designation', font_size)
            sheet.write(row, 2, 'Gross Salary', font_size)
            sheet.write(row, 3, 'WHT Salary', font_size)
            for data in total_sheet_data:
                row += 1
                sheet.write(row, 0, data['employee'], font_size)
                sheet.write(row, 1, data['designation'], font_size)
                sheet.write(row, 2, data['gross_salary'], font_size)
                sheet.write(row, 3, data['wht_salary'], font_size)


class BonusExcelReport(models.AbstractModel):
    _name = 'report.cus_payroll.bonus_excel_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Bonus Excel Report"

    def generate_xlsx_report(self, workbook, data, objs):
        for obj in objs:
            font_size = workbook.add_format({'font_size': 12})
            sheet = workbook.add_worksheet(obj.x_name)

            row = 0
            sheet.write(row, 0, 'Employee Name', font_size)
            sheet.write(row, 1, 'Designation', font_size)
            sheet.write(row, 2, 'Account #', font_size)
            sheet.write(row, 3, 'Amount', font_size)
            for bonus in obj.x_bonus_ids.filtered(lambda l: l.x_employee_id.bank_account_id):
                if 'Bank Alfalah' in bonus.x_employee_id.bank_account_id.bank_id.name:
                    row += 1
                    sheet.write(row, 0, bonus.x_employee_id.bank_account_id.acc_holder_name, font_size)
                    sheet.write(row, 1, bonus.x_employee_id.x_job_title_id.x_name, font_size)
                    sheet.write(row, 2, bonus.x_employee_id.bank_account_id.acc_number, font_size)
                    sheet.write(row, 3, bonus.x_amount, font_size)










