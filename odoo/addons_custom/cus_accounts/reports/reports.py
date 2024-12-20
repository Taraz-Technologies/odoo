from odoo import models


class StatementLinesExcelReport(models.AbstractModel):
    _name = 'report.cus_accounts.cus_accounts_statement_lines'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Export St. Lines"

    def generate_xlsx_report(self, workbook, data, objs):
        font_size_bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})
        for obj in objs:
            sheet = workbook.add_worksheet(obj.name)

            headers = [
                'Line Code', 'Date', 'Label', 'Partner', 'Reference', 'Transaction Type',
                'Notes', 'Amount', 'Bank Account', 'Amount Currency', 'Currency'
            ]

            row = 0
            for column in range(len(headers)):
                sheet.write(row, column, headers[column], font_size_bold)

            for line in obj.line_ids:
                row += 1
                vals = [
                    line.x_line_code,
                    line.date,
                    line.name,
                    line.partner_id.name,
                    line.ref,
                    line.transaction_type,
                    line.note,
                    line.amount,
                    line.account_number,
                    line.amount_currency,
                    line.currency_id.name
                ]
                for column in range(len(vals)):
                    sheet.write(row, column, vals[column], font_size)










