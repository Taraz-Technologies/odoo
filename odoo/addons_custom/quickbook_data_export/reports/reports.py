
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from datetime import datetime
import xlsxwriter

class ReportXlsx(models.AbstractModel):
    _name = 'report.data_quickbooks.report_xlsx'
    _description = 'Report XLSX'
    _inherit = 'report.report_xlsx.abstract'

    def add_row(self, sheet, row, row_data, format):
        column = 0
        for cell_data in row_data:
            sheet.write(row, column, cell_data, format)
            column += 1

    def _get_pkr_rate(self,date, currency_id, currency_rate):
        invoice_currency_rate = self.env['res.currency.rate'].search([('name', '=', date), ('currency_id', '=', 165)], limit=1).rate
        invoice_currency_rate = invoice_currency_rate if invoice_currency_rate else currency_rate
        if currency_id != 2:
            other_currency_rate = self.env['res.currency.rate'].search([('name', '=', date), ('currency_id', '=', currency_id)], limit=1).rate
            other_currency_rate = other_currency_rate if other_currency_rate else self.env['res.currency.rate'].search([('currency_id', '=', currency_id)], limit=1).rate
            invoice_currency_rate = invoice_currency_rate / other_currency_rate
        return invoice_currency_rate

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet("Sheet1")
        bold = workbook.add_format({'font_size': 12, 'bold': True})
        font_size = workbook.add_format({'font_size': 12})

        currency_rate = self.env['res.currency.rate'].search([('currency_id', '=', 165)], limit=1).rate
        #------------------------------
        # --------------- Invoice ---------------
        #------------------------------
        row = 0
        row_data = ['!ACCNT','NAME','ACCNTTYPE',]
        self.add_row(sheet, row, row_data, bold)

        for invoice in objs.x_invoice_ids:
            for line in invoice.invoice_line_ids:
                if line.account_id.x_quickbooks_name:
                    NAME = line.account_id.x_quickbooks_name
                    quickbooks_accounts = self.env['accounts.quickbooks'].search([]).mapped('x_name')
                    if not NAME in quickbooks_accounts:
                        ACCNTTYPE = False
                        if line.account_id.user_type_id.name == 'Receivable':
                            ACCNTTYPE = 'AR'
                        elif line.account_id.user_type_id.name == 'Payable':
                            ACCNTTYPE = 'AP'
                        elif line.account_id.user_type_id.name == 'Bank and Cash':
                            ACCNTTYPE = 'BANK'
                        elif line.account_id.user_type_id.name == 'Current Assets':
                            ACCNTTYPE = 'OCASSET'
                        elif line.account_id.user_type_id.name == 'Fixed Assets':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.account_id.user_type_id.name == 'Current Liabilities':
                            ACCNTTYPE = 'OCLIAB'
                        elif line.account_id.user_type_id.name == 'Non-current Liabilities':
                            ACCNTTYPE = 'LTLIAB'
                        elif line.account_id.user_type_id.name == 'Equity':
                            ACCNTTYPE = 'EQUITY'
                        elif line.account_id.user_type_id.name == 'Income':
                            ACCNTTYPE = 'INC'
                        elif line.account_id.user_type_id.name == 'Expenses':
                            ACCNTTYPE = 'EXP'
                        elif line.account_id.user_type_id.name == 'Depreciation':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.account_id.user_type_id.name == 'Cost of Revenue':
                            ACCNTTYPE = 'COGS'
                        if ACCNTTYPE:
                            self.env['accounts.quickbooks'].create({'x_name': NAME, 'x_type':ACCNTTYPE, })
                            row += 1
                            row_data = ['ACCNT',NAME,ACCNTTYPE,]
                            self.add_row(sheet, row, row_data, font_size)
                if line.product_id.categ_id.property_account_expense_categ_id.x_quickbooks_name:
                    NAME = line.product_id.categ_id.property_account_expense_categ_id.x_quickbooks_name
                    quickbooks_accounts = self.env['accounts.quickbooks'].search([]).mapped('x_name')
                    if not NAME in quickbooks_accounts:
                        ACCNTTYPE = False
                        if line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Receivable':
                            ACCNTTYPE = 'AR'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Payable':
                            ACCNTTYPE = 'AP'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Bank and Cash':
                            ACCNTTYPE = 'BANK'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Current Assets':
                            ACCNTTYPE = 'OCASSET'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Fixed Assets':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Current Liabilities':
                            ACCNTTYPE = 'OCLIAB'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Non-current Liabilities':
                            ACCNTTYPE = 'LTLIAB'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Equity':
                            ACCNTTYPE = 'EQUITY'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Income':
                            ACCNTTYPE = 'INC'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Expenses':
                            ACCNTTYPE = 'EXP'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Depreciation':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.product_id.categ_id.property_account_expense_categ_id.user_type_id.name == 'Cost of Revenue':
                            ACCNTTYPE = 'COGS'
                        if ACCNTTYPE:
                            self.env['accounts.quickbooks'].create({'x_name': NAME, 'x_type':ACCNTTYPE, })
                            row += 1
                            row_data = ['ACCNT',NAME,ACCNTTYPE,]
                            self.add_row(sheet, row, row_data, font_size)

        row += 1
        row_data = ['!INVITEM','NAME','INVITEMTYPE','DESC','ACCNT','ASSETACCNT','COGSACCNT','PRICE','COST',]
        self.add_row(sheet, row, row_data, bold)

        for invoice in objs.x_invoice_ids:
            pkr_currency_rate = self.env['res.currency.rate'].search([('name', '=', invoice.invoice_date), ('currency_id', '=', 165)], limit=1).rate
            pkr_currency_rate = pkr_currency_rate if pkr_currency_rate else currency_rate
            invoice_currency_rate = pkr_currency_rate
            if invoice.currency_id.id != 2:
                ocr = self.env['res.currency.rate'].search([('name', '=', invoice.invoice_date), ('currency_id', '=', invoice.currency_id.id)], limit=1).rate
                ocr = ocr if ocr else self.env['res.currency.rate'].search([('currency_id', '=', invoice.currency_id.id)], limit=1).rate
                invoice_currency_rate = invoice_currency_rate / ocr

            for line in invoice.invoice_line_ids:
                if line.account_id.x_quickbooks_name:
                    NAME = line.product_id.name
                    if line.product_id.type == 'product':
                        INVITEMTYPE = 'INVENTORY'
                    else:
                        INVITEMTYPE = 'SERV'
                    DESC = line.name
                    ACCNT = line.account_id.x_quickbooks_name
                    ASSETACCNT = line.product_id.categ_id.property_stock_valuation_account_id.x_quickbooks_name
                    COGSACCNT = line.product_id.categ_id.property_account_expense_categ_id.x_quickbooks_name
                    PRICE = line.price_unit if invoice.currency_id == 165 else round(line.price_unit * invoice_currency_rate, 0)
                    COST = round(line.product_id.standard_price * pkr_currency_rate, 0)
                    row += 1
                    row_data = ['INVITEM',NAME,INVITEMTYPE,DESC,ACCNT,ASSETACCNT,COGSACCNT,PRICE,COST,]
                    self.add_row(sheet, row, row_data, font_size)

        row += 1
        row_data = ['!CLASS','NAME',]
        self.add_row(sheet, row, row_data, bold)
        row += 1
        row_data = ['CLASS','class',]
        self.add_row(sheet, row, row_data, font_size)

        row += 1
        row_data = ['!CUST', 'NAME', 'COMPANYNAME', 'FIRSTNAME', 'PHONE1', 'MOBILE1', 'EMAIL', 'CONT1', 'BADDR1', 'BADDR2', 'BADDR3', 'BADDR4', 'BADDR5', ]
        self.add_row(sheet, row, row_data, bold)

        customers = []
        for invoice in objs.x_invoice_ids:
            if invoice.partner_id.parent_id:
                NAME = invoice.partner_id.parent_id.x_quickbooks_name if invoice.partner_id.parent_id.x_quickbooks_name else invoice.partner_id.parent_id.name
                CONT1 = invoice.partner_id.name if invoice.partner_id.name else ''
            else:
                NAME = invoice.partner_id.x_quickbooks_name if invoice.partner_id.x_quickbooks_name else invoice.partner_id.name
                CONT1 = invoice.partner_id.x_contact_name if invoice.partner_id.x_contact_name else ''
            BADDR1 = invoice.partner_id.street if invoice.partner_id.street else ''
            BADDR2 = invoice.partner_id.street2 if invoice.partner_id.street2 else ''
            BADDR3 = invoice.partner_id.city if invoice.partner_id.city else ''
            BADDR4 = invoice.partner_id.state_id.name if invoice.partner_id.state_id else ''
            BADDR5 = invoice.partner_id.country_id.name if invoice.partner_id.country_id else ''
            PHONE1 = invoice.partner_id.phone if invoice.partner_id.phone else ''
            MOBILE1 = invoice.partner_id.mobile if invoice.partner_id.mobile else ''
            EMAIL = invoice.partner_id.email if invoice.partner_id.email else ''

            if not NAME in customers:
                row += 1
                row_data = ['CUST', NAME, NAME, CONT1, PHONE1, MOBILE1, EMAIL, CONT1, BADDR1, BADDR2, BADDR3, BADDR4, BADDR5, ]
                self.add_row(sheet, row, row_data, font_size)
                customers.append(NAME)

            quickbooks_name = self.env['contacts.quickbooks'].search([]).mapped('x_name')
            if not NAME in quickbooks_name:
                self.env['contacts.quickbooks'].create({'x_name': NAME, 'x_type': 'CUST',})

        row += 1
        row_data = ['!TRNS','TRNSID','TRNSTYPE','DATE','ACCNT','NAME','CLASS','AMOUNT','DOCNUM','MEMO','CLEAR','TOPRINT','NAMEISTAXABLE','ADDR1','ADDR3','TERMS','SHIPVIA','SHIPDATE',]
        self.add_row(sheet, row, row_data, bold)

        row += 1
        row_data =  ['!SPL','SPLID','TRNSTYPE','DATE','ACCNT','NAME','CLASS','AMOUNT','DOCNUM','MEMO','CLEAR','QNTY','PRICE','INVITEM','TAXABLE','OTHER2','YEARTODATE','WAGEBASE',]
        self.add_row(sheet, row, row_data, bold)

        row += 1
        row_data = ['!ENDTRNS',]
        self.add_row(sheet, row, row_data, bold)

        for invoice in objs.x_invoice_ids:
            invoice_currency_rate = self._get_pkr_rate(invoice.invoice_date, invoice.currency_id.id, currency_rate)

            DATE = invoice.invoice_date.strftime('%d/%m/%y')
            AMOUNT = invoice.amount_total if invoice.currency_id == 165 else round(invoice.amount_total * invoice_currency_rate, 0)
            DOCNUM = invoice.invoice_origin.replace('Clearing', 'Clear') if invoice.invoice_origin else invoice.name.replace('Clearing', 'Clear')

            if invoice.partner_id.parent_id:
                NAME = invoice.partner_id.parent_id.x_quickbooks_name if invoice.partner_id.parent_id.x_quickbooks_name else invoice.partner_id.parent_id.name
                ACCNT = invoice.partner_id.parent_id.property_account_receivable_id.x_quickbooks_name
            else:
                NAME = invoice.partner_id.x_quickbooks_name if invoice.partner_id.x_quickbooks_name else invoice.partner_id.name
                ACCNT = invoice.partner_id.property_account_receivable_id.x_quickbooks_name

            row += 1
            row_data = ['TRNS', '', 'INVOICE', DATE, ACCNT, NAME, '', AMOUNT, DOCNUM, '', 'N', 'Y', 'N', '', '', '', '', DATE]
            self.add_row(sheet, row, row_data, font_size)

            for line in invoice.invoice_line_ids:
                if line.account_id.x_quickbooks_name:
                    ACCNT = line.account_id.x_quickbooks_name
                    PRICE = AMOUNT = line.price_subtotal if invoice.currency_id == 165 else round(line.price_subtotal * invoice_currency_rate, 0)
                    QNTY = -line.quantity
                    INVITEM = line.product_id.name

                    row += 1
                    row_data = ['SPL', '', 'INVOICE', DATE, ACCNT, '', '', -AMOUNT, '', '', 'N', QNTY, PRICE, INVITEM, 'Y', '', 0, 0, ]
                    self.add_row(sheet, row, row_data, font_size)

            row += 1
            sheet.write(row, 0, 'ENDTRNS', font_size)
        #------------------------------
        # --------------- Bill ---------------
        #------------------------------
        row += 1
        row_data = ['!ACCNT','NAME','ACCNTTYPE',]
        self.add_row(sheet, row, row_data, bold)

        for bill in objs.x_bill_ids:
            for line in bill.invoice_line_ids:
                if line.account_id.x_quickbooks_name:
                    NAME = line.account_id.x_quickbooks_name
                    quickbooks_accounts = self.env['accounts.quickbooks'].search([]).mapped('x_name')
                    if not NAME in quickbooks_accounts:
                        ACCNTTYPE = False
                        if line.account_id.user_type_id.name == 'Receivable':
                            ACCNTTYPE = 'AR'
                        elif line.account_id.user_type_id.name == 'Payable':
                            ACCNTTYPE = 'AP'
                        elif line.account_id.user_type_id.name == 'Bank and Cash':
                            ACCNTTYPE = 'BANK'
                        elif line.account_id.user_type_id.name == 'Current Assets':
                            ACCNTTYPE = 'OCASSET'
                        elif line.account_id.user_type_id.name == 'Fixed Assets':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.account_id.user_type_id.name == 'Current Liabilities':
                            ACCNTTYPE = 'OCLIAB'
                        elif line.account_id.user_type_id.name == 'Non-current Liabilities':
                            ACCNTTYPE = 'LTLIAB'
                        elif line.account_id.user_type_id.name == 'Equity':
                            ACCNTTYPE = 'EQUITY'
                        elif line.account_id.user_type_id.name == 'Income':
                            ACCNTTYPE = 'INC'
                        elif line.account_id.user_type_id.name == 'Expenses':
                            ACCNTTYPE = 'EXP'
                        elif line.account_id.user_type_id.name == 'Depreciation':
                            ACCNTTYPE = 'FIXASSET'
                        elif line.account_id.user_type_id.name == 'Cost of Revenue':
                            ACCNTTYPE = 'COGS'
                        if ACCNTTYPE:
                            self.env['accounts.quickbooks'].create({'x_name': NAME, 'x_type': ACCNTTYPE, })
                            row += 1
                            row_data = ['ACCNT',NAME,ACCNTTYPE,]
                            self.add_row(sheet, row, row_data, font_size)
        # row += 1
        # row_data = ['!INVITEM','NAME','INVITEMTYPE','DESC','ACCNT','ASSETACCNT','COGSACCNT','PRICE','COST',]
        # self.add_row(sheet, row, row_data, bold)
        #
        # for bill in objs.x_bill_ids:
        #     pkr_currency_rate = self.env['res.currency.rate'].search([('name', '=', bill.invoice_date), ('currency_id', '=', 165)], limit=1).rate
        #     pkr_currency_rate = pkr_currency_rate if pkr_currency_rate else currency_rate
        #     bill_currency_rate = pkr_currency_rate
        #     if bill.currency_id.id != 2:
        #         ocr = self.env['res.currency.rate'].search([('name', '=', bill.invoice_date), ('currency_id', '=', bill.currency_id.id)], limit=1).rate
        #         ocr = ocr if ocr else self.env['res.currency.rate'].search([('currency_id', '=', bill.currency_id.id)], limit=1).rate
        #         bill_currency_rate = bill_currency_rate / ocr
        #
        #     for line in bill.invoice_line_ids:
        #         if line.product_id.type == 'product' and line.account_id.x_quickbooks_name and \
        #                 line.product_id.categ_id.parent_id.name != 'Inventory' and line.product_id.categ_id.name != 'Inventory':
        #             NAME = line.product_id.name
        #             INVITEMTYPE = 'INVENTORY'
        #             DESC = line.name
        #             ACCNT = line.account_id.x_quickbooks_name if line.account_id.x_quickbooks_name else line.account_id.name
        #             ASSETACCNT = line.product_id.categ_id.property_stock_valuation_account_id.x_quickbooks_name
        #             COGSACCNT = line.product_id.categ_id.property_account_expense_categ_id.x_quickbooks_name
        #             PRICE = line.price_unit if bill.currency_id == 165 else round(line.price_unit * bill_currency_rate, 0)
        #             COST = round(line.product_id.standard_price * bill_currency_rate, 0)
        #             row += 1
        #             row_data = ['INVITEM',NAME,INVITEMTYPE,DESC,ACCNT,ASSETACCNT,COGSACCNT,PRICE,COST,]
        #             self.add_row(sheet, row, row_data, font_size)
        row += 1
        row_data = ['!CLASS','NAME',]
        self.add_row(sheet, row, row_data, bold)
        row += 1
        row_data = ['CLASS','class',]
        self.add_row(sheet, row, row_data, font_size)

        row += 1
        row_data = ['!VEND','NAME','COMPANYNAME','PRINTAS','ADDR1','ADDR2','ADDR3','ADDR4','ADDR5','VTYPE','CONT1','FIRSTNAME','PHONE1','PHONE2','EMAIL',]
        self.add_row(sheet, row, row_data, bold)

        vendors = []
        for bill in objs.x_bill_ids:
            if bill.partner_id.parent_id:
                NAME = bill.partner_id.parent_id.x_quickbooks_name if bill.partner_id.parent_id.x_quickbooks_name else bill.partner_id.parent_id.name
                CONT1 = bill.partner_id.name if bill.partner_id.name else ''
            else:
                NAME = bill.partner_id.x_quickbooks_name if bill.partner_id.x_quickbooks_name else bill.partner_id.name
                CONT1 = bill.partner_id.x_contact_name if bill.partner_id.x_contact_name else ''
            ADDR1 = bill.partner_id.street if bill.partner_id.street else ''
            ADDR2 = bill.partner_id.street2 if bill.partner_id.street2 else ''
            ADDR3 = bill.partner_id.city if bill.partner_id.city else ''
            ADDR4 = bill.partner_id.state_id.name if bill.partner_id.state_id else ''
            ADDR5 = bill.partner_id.country_id.name if bill.partner_id.country_id else ''
            PHONE1 = bill.partner_id.phone if bill.partner_id.phone else ''
            MOBILE1 = bill.partner_id.mobile if bill.partner_id.mobile else ''
            EMAIL = bill.partner_id.email if bill.partner_id.email else ''

            if not NAME in vendors:
                row += 1
                row_data = ['VEND', NAME, NAME, '', ADDR1, ADDR2, ADDR3, ADDR4, ADDR5, '', CONT1, CONT1, PHONE1, MOBILE1, EMAIL, ]
                self.add_row(sheet, row, row_data, font_size)
                vendors.append(NAME)

            quickbooks_name = self.env['contacts.quickbooks'].search([]).mapped('x_name')
            if not NAME in quickbooks_name:
                self.env['contacts.quickbooks'].create({'x_name': NAME, 'x_type': 'VEND',})

        row += 1
        row_data = ['!TRNS','TRNSID','TRNSTYPE','DATE','ACCNT','NAME','CLASS','AMOUNT','DOCNUM','MEMO','CLEAR','TOPRINT','ADDR5','DUEDATE','TERMS',]
        self.add_row(sheet, row, row_data, bold)

        row += 1
        row_data =  ['!SPL','SPLID','TRNSTYPE','DATE','ACCNT','NAME','CLASS','AMOUNT','INVITEM','MEMO','CLEAR','QNTY','PRICE','REIMBEXP','SERVICEDATE',]
        self.add_row(sheet, row, row_data, bold)

        row += 1
        row_data = ['!ENDTRNS',]
        self.add_row(sheet, row, row_data, bold)

        if not objs.x_export_bills:
            bills = objs.x_bill_ids
        else:
            bills = objs.x_export_bills

        for bill in bills:
            payments = bill.x_registered_payments.count('Rs.')
            if payments == 0:
                payments = bill.x_registered_payments.count('$')
            if payments == 0:
                payments = bill.x_registered_payments.count('£')
            if payments == 0:
                payments = bill.x_registered_payments.count('€')

            # if payments == 1:
            #     invoice_date = bill.invoice_payments_widget.split('"date": ')[1].split(', "')[0].replace('"',"'")
            #     invoice_date = datetime.strptime(invoice_date,'%Y-%m-%d').strftime('%d/%m/%y')

            bill_currency_rate = self._get_pkr_rate(bill.invoice_date, bill.currency_id.id, currency_rate)

            TRNSTYPE = 'CHECK' if payments == 1 else 'BILL'
            DATE = bill.invoice_date.strftime('%d/%m/%y')
            AMOUNT = bill.amount_total if bill.currency_id == 165 else round(bill.amount_total * bill_currency_rate, 0)
            MEMO = bill.x_registered_payments
            DOCNUM = bill.invoice_origin.replace('Clearing', 'Clear') if bill.invoice_origin else bill.name.replace('Clearing', 'Clear')

            if bill.partner_id.parent_id:
                ACCNT = bill.partner_id.parent_id.property_account_payable_id.x_quickbooks_name
                NAME = bill.partner_id.parent_id.x_quickbooks_name if bill.partner_id.parent_id.x_quickbooks_name else bill.partner_id.parent_id.name
            else:
                ACCNT = bill.partner_id.property_account_payable_id.x_quickbooks_name
                NAME = bill.partner_id.x_quickbooks_name if bill.partner_id.x_quickbooks_name else bill.partner_id.name

            if TRNSTYPE == 'CHECK':
                ACCNT = bill.x_payment_method.default_credit_account_id.x_quickbooks_name if bill.x_payment_method.default_credit_account_id.x_quickbooks_name else bill.x_payment_method.default_credit_account_id.name

            row += 1
            row_data = ['TRNS', '', TRNSTYPE, DATE, ACCNT, NAME, 'class', -AMOUNT, DOCNUM, MEMO, 'N', 'N', '', DATE, 'Net 30',]
            self.add_row(sheet, row, row_data, font_size)
            # ------------------------------ Add Expense and Tax Lines ------------------------------
            for line in bill.invoice_line_ids:
                if line.account_id.x_quickbooks_name and line.product_id and not 'Inventory' in line.account_id.name and not line.is_landed_costs_line:
                    ACCNT = line.account_id.x_quickbooks_name if line.account_id.x_quickbooks_name else line.account_id.name
                    NAME = 'FBR PURCHASE' if 'GST' in line.product_id.name or 'Sale Tax' in line.product_id.name else ''
                    AMOUNT = line.price_subtotal if bill.currency_id == 165 else round(line.price_subtotal * bill_currency_rate, 0)
                    MEMO = line.name if line.name else line.product_id.name
                    row += 1
                    row_data = ['SPL', '', TRNSTYPE, DATE, ACCNT, NAME, 'class', AMOUNT, '', MEMO, 'N', '', '', 'NOTHING', '0/0/0', ]
                    self.add_row(sheet, row, row_data, font_size)

                for tax in line.tax_ids:
                    for journal_items_line in bill.line_ids:
                        if journal_items_line.name == tax.name and journal_items_line.account_id.x_quickbooks_name:
                            ACCNT = journal_items_line.account_id.x_quickbooks_name
                            AMOUNT = round(journal_items_line.amount_currency, 0)
                            MEMO = journal_items_line.name
                            row += 1
                            row_data = ['SPL', '', TRNSTYPE, DATE, ACCNT, 'FBR PURCHASES', 'class', AMOUNT, '', MEMO, 'N', '', '', 'NOTHING', '0/0/0', ]
                            self.add_row(sheet, row, row_data, font_size)
            # ------------------------------ Add Inventory Lines ------------------------------
            for line in bill.invoice_line_ids:
                if line.account_id.x_quickbooks_name and line.product_id and ('Inventory' in line.account_id.name or line.is_landed_costs_line):
                    AMOUNT = line.price_subtotal if bill.currency_id == 165 else round(line.price_subtotal * bill_currency_rate, 0)
                    INVITEM = line.name if line.name else line.product_id.name
                    row += 1
                    row_data = ['SPL', '', TRNSTYPE, DATE, 'Inventory Asset', '', 'class', AMOUNT, 'Inventory', INVITEM, 'N', AMOUNT, 1, 'NOTHING', '0/0/0', ]
                    self.add_row(sheet, row, row_data, font_size)

            row += 1
            sheet.write(row, 0, 'ENDTRNS', font_size)

        if not objs.x_export_bills:
            # ------------------------------ Assessed Value Inventory Bill ------------------------------
            inventory_items = ['CONN IDC', 'CONN BNC', 'CAP FILM', 'VARISTOR', 'LED', 'IC TRANSCEIVER', 'RELAY', 'CONN HEADER', 'CONN SOCKET', 'CBL RIBN', 'CRYSTAL',
                               'HEAT SINK', 'IC MUX/DEMUX', 'IC BUF', 'IC GATE', 'IC TRNSLTR', 'FIXED IND', 'CAP CER', 'DIODE', 'IC REG', 'RES ', 'IC OPAMP',
                               'CURRENT SENSOR', 'RES SMD', 'IC SWITCH', 'DIODE ARRAY', 'ADAPTER', 'SPACER', 'WASHER', 'IC FPGA', 'THERMOSTAT', 'CHOKE', 'Encoders',
                               'SWITCH ROCKER', 'REG', 'IC MCU', 'DCDC CONV', 'SUPPRESSOR ESD', 'IDC', 'TZR', 'TZCC', 'CONN RCPT', 'MOSFET', 'IGBT', 'FUSE', 'Fuse',
                               'PCB TERM BLOCK', 'PCB', 'TERM BLK', ]
            assessed_value_bill_ids = self.env['account.move'].search([('state', '=', 'posted'), ('type', '=', 'in_invoice'),
                                                                       ('x_purchase_type', '=', 'Clearing'), ('x_assessed_value', '!=', 0),
                                                                       ('invoice_date', '<=', objs.x_date_to), ('invoice_date', '>=', objs.x_date_from)])
            assessed_value_bills = []
            for bill in assessed_value_bill_ids:
                DATE = bill.invoice_date.strftime('%d/%m/%y')
                AMOUNT = bill.x_assessed_value
                MEMO1 = 'Assessed Value: PKR ' + str(bill.x_assessed_value)
                MEMO2 = 'Items: ('
                if len(bill.x_related_po_s.ids) == 1:
                    for po in bill.x_related_po_s:
                        DOCNUM = po.name
                        if po.partner_id.parent_id:
                            ACCNT = po.partner_id.parent_id.property_account_payable_id.x_quickbooks_name
                            NAME = po.partner_id.parent_id.x_quickbooks_name if po.partner_id.parent_id.x_quickbooks_name else po.partner_id.parent_id.name
                        else:
                            ACCNT = po.partner_id.property_account_payable_id.x_quickbooks_name
                            NAME = po.partner_id.x_quickbooks_name if po.partner_id.x_quickbooks_name else po.partner_id.name

                        line_descriptions = po.order_line.mapped('name')
                        for item in inventory_items:
                            for line_desc in line_descriptions:
                                if item in line_desc and not item in MEMO2:
                                    MEMO2 = MEMO2 + item if MEMO2 == 'Items: (' else MEMO2 + ', ' + item
                else:
                    vendor_ids = bill.x_related_po_s.mapped('partner_id')
                    NAME = 'YE - Yuzens Electronics, Co., Ltd.' if '69' in vendor_ids else 'Reship US'
                    DOCNUM = bill.ref
                    ACCNT = 'Accounts Payable'
                    order_lines = bill.x_related_po_s.mapped('order_line')
                    for order_line in order_lines:
                        line_descriptions = order_line.mapped('name')
                        for item in inventory_items:
                            for line_desc in line_descriptions:
                                if item in line_desc and not item in MEMO2:
                                    MEMO2 = MEMO2 + item if MEMO2 == 'Items: (' else MEMO2 + ', ' + item

                MEMO2 = MEMO2 + ')'

                DOCNUM = DOCNUM.replace('_ClearingA', '') if '_ClearingA' in DOCNUM else DOCNUM
                DOCNUM = DOCNUM.replace('_ClearingB', '') if '_ClearingB' in DOCNUM else DOCNUM
                DOCNUM = DOCNUM.replace('_Clearing', '') if '_Clearing' in DOCNUM else DOCNUM
                if not DOCNUM in assessed_value_bills:
                    assessed_value_bills.append(DOCNUM)
                    row += 1
                    row_data = ['TRNS', '', 'BILL', DATE, ACCNT, NAME, 'class', -AMOUNT, DOCNUM, MEMO1, 'N', 'N', '', DATE, 'Net 30',]
                    self.add_row(sheet, row, row_data, font_size)
                    row += 1
                    row_data = ['SPL', '', 'BILL', DATE, 'Inventory Asset', '', 'class', AMOUNT, 'Inventory', MEMO2, 'N', AMOUNT, 1, 'NOTHING', '0/0/0', ]
                    self.add_row(sheet, row, row_data, font_size)
                    row += 1
                    sheet.write(row, 0, 'ENDTRNS', font_size)
        else:
            objs.x_export_bills = False
        #------------------------------
        # --------------- Internal Transfer ---------------
        #------------------------------
        row += 1
        row_data = ['!TRNS','TRNSID','TRNSTYPE','DATE','ACCNT','AMOUNT','DOCNUM','MEMO','CLEAR',]
        self.add_row(sheet, row, row_data, bold)

        row += 1
        row_data =  ['!SPL','SPLID','TRNSTYPE','DATE','ACCNT','AMOUNT','DOCNUM','MEMO','CLEAR',]
        self.add_row(sheet, row, row_data, bold)

        for transfer in objs.x_internal_transfer_ids:
            DATE = transfer.payment_date.strftime('%d/%m/%y')
            ACCNT = transfer.journal_id.default_credit_account_id.x_quickbooks_name
            AMOUNT = transfer.amount
            DOCNUM = transfer.name
            MEMO = transfer.communication
            row += 1
            row_data = ['TRNS', '', 'TRANSFER', DATE, ACCNT, -AMOUNT, DOCNUM, MEMO, 'N']
            self.add_row(sheet, row, row_data, font_size)

            ACCNT = transfer.destination_journal_id.default_credit_account_id.x_quickbooks_name
            row += 1
            row_data = ['SPL', '', 'TRANSFER', DATE, ACCNT, AMOUNT, '', '', 'N']
            self.add_row(sheet, row, row_data, font_size)

            row += 1
            sheet.write(row, 0, 'ENDTRNS', font_size)









