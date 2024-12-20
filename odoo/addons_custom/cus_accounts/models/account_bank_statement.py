from odoo import fields, models, api, _
from odoo.addons.test_convert.tests.test_env import record
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, ValidationError

import PyPDF2
import subprocess
import tempfile
import odoo
import re

from datetime import datetime, timedelta
from calendar import monthrange


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    x_attachment_id = fields.Many2one(comodel_name='ir.attachment', string='Statement', required=False,
                                      domain="[('res_model', '=', 'account.bank.statement'), ('res_id', '=', id)]")
    x_statement_type = fields.Selection([('format1', 'Kuveyt Format 1'),
                                         ('format2', 'Kuveyt Format2')], string="Statement Type", default='format1')

    @api.constrains('date', 'name')
    def check_date_uniqueness(self):
        current_dates = self.env['account.bank.statement'].search([('name', '!=', False)]).mapped('name')
        count = current_dates.count(self.name)
        if count > 1:
            raise ValidationError("Record already exist with same month.")


    @api.model
    def create(self, vals):
        res = super(AccountBankStatement, self).create(vals)
        for rec in res:
            if rec.x_attachment_id:
                rec.x_attachment_id.write({'res_model': self._name, 'res_id': rec.id})
        return res

    def write(self, vals):
        res = super(AccountBankStatement, self).write(vals)
        for rec in self:
            if rec.x_attachment_id:
                rec.x_attachment_id.write({'res_model': self._name, 'res_id': rec.id})
        return res

    def download_statement_lines(self):
        return self.env.ref('cus_accounts.cus_accounts_statement_lines').report_action(self)

    @api.onchange('date')
    def update_statement_reference(self):
        for rec in self:
            if rec.journal_id._origin.id != 7 and rec.date:
                rec.name = 'BS: %s - %s %s' % (rec.journal_id.x_short_code, rec.date.strftime('%b'), rec.date.strftime('%Y'))

    # def get_statement_lines(self):
    #     global second_line_date, second_line_index
    #     for rec in self:
    #         if not rec.x_attachment_id:
    #             continue
    #
    #         file_name = rec.x_attachment_id.store_fname
    #         file_path = "%s/filestore/%s/%s" % (odoo.tools.config['data_dir'], self.env.cr.dbname, file_name)
    #
    #         # Extract text from a PDF file.
    #         # https://pdfminersix.readthedocs.io/en/latest/tutorial
    #         # https://stackoverflow.com/questions/26633348/read-pdf-file-horizontally-with-pdfminer
    #
    #         input_file = open(file_path, 'rb').read()
    #         temp_file = tempfile.NamedTemporaryFile()
    #         temp_file.write(input_file)
    #         temp_file.seek(0)
    #         output_file = tempfile.NamedTemporaryFile()
    #         subprocess.Popen(["pdftotext", "-layout", temp_file.name, output_file.name]).communicate()
    #         pdf_data = str(output_file.read().decode("utf-8"))
    #
    #         # replace multiple spaces with tab
    #         formatted_data = re.sub('  +', '\t', pdf_data)
    #         # raise UserError(formatted_data)
    #
    #         # split by double new line and remove extra spaces
    #         data = [item.strip().replace('\n', '\t') for item in formatted_data.split('\n\n') if item]
    #         # raise UserError(data)
    #         print(data)
    #
    #         date_range = monthrange(rec.date.year, rec.date.month)
    #         date_to = rec.date + timedelta(days=date_range[1])
    #         line_codes = rec.line_ids.mapped('x_line_code')
    #
    #         statement_lines = []
    #         line_number = 1
    #
    #         for item in data:
    #             item = item.replace('.', '|').replace(',', '.').replace('|', ',')
    #             line_items = [line_item.strip() for line_item in re.split('\t+', item) if line_item]
    #             print("Raw Item", item)
    #             print("Split line items", line_items)
    #             try:
    #                 index = 1
    #                 line_date = datetime.strptime(line_items[index], '%d,%m,%Y').date()
    #             except ValueError:
    #                 try:
    #                     index = 2
    #                     line_date = datetime.strptime(line_items[index], '%d,%m,%Y').date()
    #                     print("Parsed line date : ", line_date)
    #                 except ValueError:
    #                     continue
    #             # Check Month Statement Lines
    #             if date_to <= line_date or line_date < rec.date:
    #                 continue
    #
    #             line_code_number = ("00%s" % line_number)[-3:]
    #             line_balance = line_items[index + 2].split('.')[0] + '.' + line_items[index + 2].split('.')[1][:2]
    #             line_code = "%s - %s (%s)" % (rec.journal_id.x_short_code, line_code_number, line_balance)
    #
    #             if line_code in line_codes:
    #                 line_number += 1
    #                 continue
    #
    #             line_amount = float(line_items[index + 1].replace(',', ''))
    #
    #             # Check if line has statement line in its description
    #             try:
    #                 second_line_date = datetime.strptime(line_items[index + 8], '%d,%m,%Y').date()
    #                 second_line_index = index + 8
    #             except (ValueError, IndexError):
    #                 try:
    #                     second_line_date = datetime.strptime(line_items[index + 7], '%d,%m,%Y').date()
    #                     second_line_index = index + 7
    #                 except (ValueError, IndexError):
    #                     try:
    #                         second_line_date = datetime.strptime(line_items[index + 6], '%d,%m,%Y').date()
    #                         second_line_index = index + 6
    #                     except (ValueError, IndexError):
    #                         try:
    #                             second_line_date = datetime.strptime(line_items[index + 5], '%d,%m,%Y').date()
    #                             second_line_index = index + 5
    #                         except (ValueError, IndexError):
    #                             try:
    #                                 second_line_date = datetime.strptime(line_items[index + 4], '%d,%m,%Y').date()
    #                                 second_line_index = index + 4
    #                             except (ValueError, IndexError):
    #                                 second_line_date = False
    #
    #             # Check PDF last line
    #             last_line_identifier = '5 Maddesi gereğince nitelikli elektronik imza ile'
    #             if last_line_identifier in line_items[index + 3:] and index == 1:
    #                 line_name = line_items[index + 3:line_items.index(last_line_identifier) - 2]
    #             elif last_line_identifier in line_items[index + 3:] and index == 2:
    #                 line_name = [line_items[index - 2]] + line_items[index + 3:line_items.index(last_line_identifier) - 2]
    #             elif index == 1:
    #                 line_name = line_items[index + 3:] if not second_line_date \
    #                     else line_items[index + 3:line_items.index(second_line_date.strftime('%d,%m,%Y')) - 2]
    #             else:
    #                 line_name = [line_items[index - 2]] + line_items[index + 3:] if not second_line_date \
    #                     else [line_items[index - 2]] + line_items[index + 3:line_items.index(second_line_date.strftime('%d,%m,%Y')) - 2]
    #             line_name = ' '.join(line_name)
    #
    #             statement_lines.append((0, 0, {
    #                 'x_line_code': line_code,
    #                 'date': line_date,
    #                 'name': line_name.replace('  ', ' '),
    #                 'amount': line_amount,
    #             }))
    #             line_number += 1
    #
    #             if second_line_date:
    #                 if date_to > second_line_date >= rec.date:  # Month Statement Lines End
    #                     line_code_number = ("00%s" % line_number)[-3:]
    #                     line_balance = (line_items[second_line_index + 2].split('.')[0]
    #                                     + '.' +
    #                                     line_items[second_line_index + 2].split('.')[1][:2])
    #                     line_code = "%s - %s (%s)" % (rec.journal_id.x_short_code, line_code_number, line_balance)
    #
    #                     if line_code not in line_codes:
    #                         line_amount = float(line_items[second_line_index + 1].replace(',', ''))
    #
    #                         # Check PDF last line
    #                         if last_line_identifier in line_items[index + 3:]:
    #                             line_name = [line_items[second_line_index - 2]] + line_items[index + 3:line_items.index(last_line_identifier) - 2]
    #                         else:
    #                             line_name = [line_items[second_line_index - 2]] + line_items[second_line_index + 3:]
    #                         line_name = ' '.join(line_name)
    #
    #                         statement_lines.append((0, 0, {
    #                             'x_line_code': line_code,
    #                             'date': second_line_date,
    #                             'name': line_name.replace('  ', ' '),
    #                             'amount': line_amount,
    #                         }))
    #                         line_number += 1
    #
    #         rec.line_ids = statement_lines
    #         rec.balance_end_real = rec.balance_end

    def get_statement_lines(self):
        # Read the PDF file
        for rec in self:
            if rec.x_statement_type == 'format2':
                if not rec.x_attachment_id:
                    continue

                file_name = rec.x_attachment_id.store_fname
                file_path = "%s/filestore/%s/%s" % (odoo.tools.config['data_dir'], self.env.cr.dbname, file_name)

                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfFileReader(file)
                    pdf_data = ""
                    for page_num in range(reader.getNumPages()):
                        page = reader.getPage(page_num)
                        pdf_data += page.extractText() + "\n"

                # Split the text data into lines
                lines = pdf_data.splitlines()

                # Remove empty lines and leading/trailing whitespace
                lines = [line.strip() for line in lines if line.strip()]

                # Combine lines into entries
                entries = []
                current_entry = []
                for line in lines:
                    if line.startswith(('Referans Kodu', 'TOPLAM')) or (
                            line.split() and len(line.split()[0].split('.')) == 3):
                        if current_entry:
                            entries.append(current_entry)
                        current_entry = [line]
                    else:
                        current_entry.append(line)
                if current_entry:
                    entries.append(current_entry)

                for entry in entries:
                    if len(entry) == 42 or len(entry) == 43 or len(entry) == 44:
                        slice = entry[2:-39]
                        concat = ' '.join((slice))
                        del entry[2:-39]
                        del entry[-36:]
                        entry.insert(2, concat)
                        continue
                    if len(entry) > 5:
                        slice = entry[2:-3]
                        concat = ' '.join((slice))
                        del entry[2:-3]
                        entry.insert(2, concat)

                date_range = monthrange(rec.date.year, rec.date.month)
                date_to = rec.date + timedelta(days=date_range[1])
                line_codes = rec.line_ids.mapped('x_line_code')

                statement_lines = []
                line_number = 1
                for line in entries:
                    if len(line) > 4:
                        try:
                            # date_str = line[0].replace('.', '/')
                            line_date = datetime.strptime(line[0], "%d.%m.%Y").date()
                        except ValueError as e:
                            # print("ValueError: ", e)  # Debugging: print ValueError if date parsing fails
                            continue

                        # Check Month Statement Lines
                        if date_to <= line_date or line_date < rec.date:
                            continue

                        line_code_number = ("00%s" % line_number)[-3:]
                        try:
                            line_balance = line[4].split('.')[0] + '.' + line[4].split('.')[1][:2]
                        except IndexError as e:
                            print("IndexError (line_balance): ", e)  # Debugging: print IndexError if line balance parsing fails
                            continue

                        line_code = "%s - %s (%s)" % (rec.journal_id.x_short_code, line_code_number, line_balance)

                        if line_code in line_codes:
                            line_number += 1
                            continue

                        try:
                            line_amount = float(line[3].replace(',', ''))
                            line_name = line[2]
                        except IndexError as e:
                            print("IndexError (line_amount/line_name): ", e)  # Debugging: print IndexError if amount/name parsing fails
                            continue

                        statement_lines.append((0, 0, {
                            'x_line_code': line_code,
                            'date': line_date,
                            'name': line_name,
                            'amount': line_amount,
                        }))
                        line_number += 1

                rec.line_ids = statement_lines
                rec.balance_end_real = rec.balance_end
            else:
                global second_line_date, second_line_index
                if not rec.x_attachment_id:
                    continue

                file_name = rec.x_attachment_id.store_fname
                file_path = "%s/filestore/%s/%s" % (odoo.tools.config['data_dir'], self.env.cr.dbname, file_name)

                # Extract text from a PDF file.
                # https://pdfminersix.readthedocs.io/en/latest/tutorial
                # https://stackoverflow.com/questions/26633348/read-pdf-file-horizontally-with-pdfminer

                input_file = open(file_path, 'rb').read()
                temp_file = tempfile.NamedTemporaryFile()
                temp_file.write(input_file)
                temp_file.seek(0)
                output_file = tempfile.NamedTemporaryFile()
                subprocess.Popen(["pdftotext", "-layout", temp_file.name, output_file.name]).communicate()
                pdf_data = str(output_file.read().decode("utf-8"))

                # replace multiple spaces with tab
                formatted_data = re.sub('  +', '\t', pdf_data)
                # raise UserError(formatted_data)

                # split by double new line and remove extra spaces
                data = [item.strip().replace('\n', '\t') for item in formatted_data.split('\n\n') if item]
                # raise UserError(data)
                print(data)

                date_range = monthrange(rec.date.year, rec.date.month)
                date_to = rec.date + timedelta(days=date_range[1])
                line_codes = rec.line_ids.mapped('x_line_code')

                statement_lines = []
                line_number = 1

                for item in data:
                    item = item.replace('.', '|').replace(',', '.').replace('|', ',')
                    line_items = [line_item.strip() for line_item in re.split('\t+', item) if line_item]
                    print("Raw Item", item)
                    print("Split line items", line_items)
                    try:
                        index = 1
                        line_date = datetime.strptime(line_items[index], '%d,%m,%Y').date()
                    except ValueError:
                        try:
                            index = 2
                            line_date = datetime.strptime(line_items[index], '%d,%m,%Y').date()
                            print("Parsed line date : ", line_date)
                        except ValueError:
                            continue
                    # Check Month Statement Lines
                    if date_to <= line_date or line_date < rec.date:
                        continue

                    line_code_number = ("00%s" % line_number)[-3:]
                    line_balance = line_items[index + 2].split('.')[0] + '.' + line_items[index + 2].split('.')[1][:2]
                    line_code = "%s - %s (%s)" % (rec.journal_id.x_short_code, line_code_number, line_balance)

                    if line_code in line_codes:
                        line_number += 1
                        continue

                    line_amount = float(line_items[index + 1].replace(',', ''))

                    # Check if line has statement line in its description
                    try:
                        second_line_date = datetime.strptime(line_items[index + 8], '%d,%m,%Y').date()
                        second_line_index = index + 8
                    except (ValueError, IndexError):
                        try:
                            second_line_date = datetime.strptime(line_items[index + 7], '%d,%m,%Y').date()
                            second_line_index = index + 7
                        except (ValueError, IndexError):
                            try:
                                second_line_date = datetime.strptime(line_items[index + 6], '%d,%m,%Y').date()
                                second_line_index = index + 6
                            except (ValueError, IndexError):
                                try:
                                    second_line_date = datetime.strptime(line_items[index + 5], '%d,%m,%Y').date()
                                    second_line_index = index + 5
                                except (ValueError, IndexError):
                                    try:
                                        second_line_date = datetime.strptime(line_items[index + 4], '%d,%m,%Y').date()
                                        second_line_index = index + 4
                                    except (ValueError, IndexError):
                                        second_line_date = False

                    # Check PDF last line
                    last_line_identifier = '5 Maddesi gereğince nitelikli elektronik imza ile'
                    if last_line_identifier in line_items[index + 3:] and index == 1:
                        line_name = line_items[index + 3:line_items.index(last_line_identifier) - 2]
                    elif last_line_identifier in line_items[index + 3:] and index == 2:
                        line_name = [line_items[index - 2]] + line_items[index + 3:line_items.index(last_line_identifier) - 2]
                    elif index == 1:
                        line_name = line_items[index + 3:] if not second_line_date \
                            else line_items[index + 3:line_items.index(second_line_date.strftime('%d,%m,%Y')) - 2]
                    else:
                        line_name = [line_items[index - 2]] + line_items[index + 3:] if not second_line_date \
                            else [line_items[index - 2]] + line_items[index + 3:line_items.index(second_line_date.strftime('%d,%m,%Y')) - 2]
                    line_name = ' '.join(line_name)

                    statement_lines.append((0, 0, {
                        'x_line_code': line_code,
                        'date': line_date,
                        'name': line_name.replace('  ', ' '),
                        'amount': line_amount,
                    }))
                    line_number += 1

                    if second_line_date:
                        if date_to > second_line_date >= rec.date:  # Month Statement Lines End
                            line_code_number = ("00%s" % line_number)[-3:]
                            line_balance = (line_items[second_line_index + 2].split('.')[0]
                                            + '.' +
                                            line_items[second_line_index + 2].split('.')[1][:2])
                            line_code = "%s - %s (%s)" % (rec.journal_id.x_short_code, line_code_number, line_balance)

                            if line_code not in line_codes:
                                line_amount = float(line_items[second_line_index + 1].replace(',', ''))

                                # Check PDF last line
                                if last_line_identifier in line_items[index + 3:]:
                                    line_name = [line_items[second_line_index - 2]] + line_items[index + 3:line_items.index(last_line_identifier) - 2]
                                else:
                                    line_name = [line_items[second_line_index - 2]] + line_items[second_line_index + 3:]
                                line_name = ' '.join(line_name)

                                statement_lines.append((0, 0, {
                                    'x_line_code': line_code,
                                    'date': second_line_date,
                                    'name': line_name.replace('  ', ' '),
                                    'amount': line_amount,
                                }))
                                line_number += 1

                rec.line_ids = statement_lines
                rec.balance_end_real = rec.balance_end



class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    _order = "x_line_code, statement_id desc, date, sequence, id desc"

    x_line_code = fields.Char(string='Code', required=False)
    x_custom_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags', tracking=True)
    x_document = fields.Binary(string="Doc.", )
    x_document_name = fields.Char(string='Doc. Name', )

    x_all_lines_reconciled = fields.Boolean(related='statement_id.all_lines_reconciled')
    x_line_ids = fields.One2many(related='statement_id.line_ids')
    x_state = fields.Selection(related='statement_id.state')

    x_currency_id = fields.Many2one(related='company_id.currency_id')

    x_amount_in_usd = fields.Monetary(string='Amount in USD', store=True, readonly=True,
        compute='_compute_amount_in_usd', currency_field='x_currency_id')

    active = fields.Boolean('Active', default=True)

    @api.depends('amount')
    def _compute_amount_in_usd(self):
        currency_usd = self.env['res.currency'].search([('name', '=', 'USD')])
        for rec in self:
            if rec.amount < 0:
                rec.x_amount_in_usd = (rec.journal_currency_id._convert(abs(rec.amount), currency_usd, rec.company_id, rec.date)) * -1
            else:
                rec.x_amount_in_usd = rec.journal_currency_id._convert(rec.amount, currency_usd, rec.company_id, rec.date)


    def action_archive(self):
        records_to_archive = self.filtered(lambda record: not record.x_journal_entries)
        return records_to_archive.toggle_active()

    @api.depends('x_payment_ids')
    def compute_invoices_bills(self):
        super(AccountBankStatementLine, self).compute_invoices_bills()
        for rec in self:
            rec.x_invoice_ids.update({'x_statement_line_id': rec.id})
            if rec.x_document:
                # rec.x_invoice_ids.update({'x_document': rec.x_document})
                rec.x_invoice_ids.update({'x_reconciled_doc': rec.x_document})

    def action_bank_reconcile_bank_statement(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {'statement_line_ids': self.statement_id.line_ids.ids, 'company_ids.id': self.company_id.id},
        }

    def write(self, vals):
        for r in self:
            if vals.get("date") is not None:
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Date: %s &rarr; %s</p>" % (self.date, vals.get("date")))
            if vals.get("name") is not None:
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Label: %s &rarr; %s</p>" % (self.name, vals.get("name")))
            if vals.get("partner_id") is not None:
                partner_name = self.env['res.partner'].browse(vals.get("partner_id")).name
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Partner: %s &rarr; %s</p>" % (self.partner_id.name, partner_name))
            if vals.get("ref") is not None:
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Reference: %s &rarr; %s</p>" % (self.ref, vals.get("ref")))
            if vals.get("amount") is not None:
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Amount: %s &rarr; %s</p>" % (self.amount, vals.get("amount")))
            if vals.get("note") is not None:
                r.statement_id.message_post(body="<p>&nbsp; &nbsp; &bull; Notes: %s &rarr; %s</p>" % (self.note, vals.get("note")))
        return super(AccountBankStatementLine, self).write(vals)











