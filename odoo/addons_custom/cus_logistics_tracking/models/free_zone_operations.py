import subprocess
import tempfile
import odoo
import re

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class FreeZoneOperations(models.Model):
    _name = 'free.zone.operations'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Free Zone Operations'
    _rec_name = 'x_form_field_01'

    x_operation_type = fields.Selection(
        string='Operation Type',
        selection=[
            ('import', 'Import'),
            ('export', 'Export'), ],
        required=True,
        default='import',
        tracking=True)

    x_type = fields.Selection(
        string='Package Type',
        selection=[
            ('purchase', 'Purchase Order'),
            ('consolidation', 'Consolidation'), ],
        required=True,
        default='purchase',
        tracking=True)
    x_bill_ids = fields.Many2many(
        comodel_name='account.move',
        relation='free_zone_operations_account_move_rel',
        column1='free_zone_operations_id',
        column2='account_move_id',
        string='Bills')
    x_purchase_ids = fields.Many2many(
        comodel_name='purchase.order',
        relation='free_zone_operations_purchase_order_rel',
        column1='free_zone_operations_id',
        column2='purchase_order_id',
        string='Purchase Orders')
    x_consolidation_ids = fields.Many2many(
        comodel_name='consolidation.tracking',
        relation='free_zone_operations_consolidation_tracking_rel',
        column1='free_zone_operations_id',
        column2='consolidation_tracking_id',
        string='Consolidations')
    x_attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attach File',
        copy=False,
        domain="[('res_model', '=', 'free.zone.operations'), ('res_id', '=', id)]",
        tracking=True)
    x_attachment_name = fields.Char(
        related='x_attachment_id.name',
        string='Download File Name')
    x_attachment = fields.Binary(
        related='x_attachment_id.datas',
        string='Download File')
    x_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=2,
        required=False,
        tracking=True,
        compute='_compute_currency_id',
        store=True)
    x_tag_ids = fields.Many2many(
        comodel_name='custom.tags',
        string='Tags',
        tracking=True,
    )
    x_folder_name = fields.Char(
        string='Folder Name',
        copy=False,
        tracking=True,
        compute='_compute_folder_name',
        store=True)

    x_form_field_01 = fields.Char(
        string='Form No.',
        copy=False,
        tracking=True)
    x_form_field_02 = fields.Selection(
        string='İŞLEM YÖNÜ',
        selection=[
            ("from_turkey", "Bölgeye Türkiye'den Mal-Hizmet Girişi"),
            ("from_abroad", "Bölgeye Yurt Dışından Mal-Hizmet Girişi"), ],
        copy=False,
        tracking=True)
    x_form_field_03 = fields.Selection(
        string='İŞLEM KONUSU',
        selection=[
            ("Ticari-Mal", "Ticari-Mal"),
            ("Ticari Olmayan-Demirbaş", "Ticari Olmayan-Demirbaş"),
            ("Ticari Olmayan-Sarf Malzemesi", "Ticari Olmayan-Sarf Malzemesi"),
            ("Ticari Olmayan-Yatırım ve Tesis", "Ticari Olmayan-Yatırım ve Tesis"),
            ("Ticari Olmayan-Hizmet Alımı", "Ticari Olmayan-Hizmet Alımı"), ],
        copy=False,
        tracking=True,
        required=True)
    x_form_field_04 = fields.Selection(
        string='İŞLEM TÜRÜ',
        selection=[
            ("Kesin Alış/Satış", "Kesin Alış/Satış"),
            ("Diğer İşlem Türleri-5000$ Altı", "Diğer İşlem Türleri-5000$ Altı"), ],
        copy=False,
        tracking=True)
    x_form_field_05 = fields.Char(
        string='SEVKİYAT ŞEKLİ',
        copy=False,
        tracking=True)
    x_form_field_06 = fields.Char(
        string='TAŞIT CİNSİ',
        copy=False,
        tracking=True)
    x_form_field_07 = fields.Float(
        string='Mal Bedeli Toplamları',
        copy=False,
        tracking=True,
        required=True)
    x_form_field_08 = fields.Float(
        string='CIF Toplamı',
        copy=False,
        tracking=True)
    x_form_field_09 = fields.Date(
        string='GİRİŞ / ÇIKIŞ Tarih',
        copy=False,
        tracking=True)
    x_form_field_10 = fields.Float(
        string='Brüt Ağırlık Toplamı',
        copy=False,
        tracking=True)
    x_form_field_11 = fields.Date(
        string='Formu Tarih',
        copy=False,
        tracking=True)
    x_form_field_12 = fields.Float(
        string='KAP',
        copy=False,
        tracking=True)
    x_form_field_13 = fields.Many2one(
        comodel_name='res.currency',
        string='Mal Bedeli Toplamları Currency',
        copy=False,
        tracking=True)
    x_form_field_14 = fields.Many2one(
        comodel_name='res.currency',
        string='CIF Toplamı Currency',
        copy=False,
        tracking=True)

    x_receipt_ids = fields.One2many(
        comodel_name='free.zone.receipts',
        inverse_name='x_operation_id',
        string='Receipts')

    x_ignore_subject_of_transaction = fields.Boolean(
        string='Ignore Subject of Transaction',
        required=False)

    x_cost_lines_ids = fields.One2many(
        comodel_name='free.zone.landed.costs',
        inverse_name='x_operation_id',
        string='Cost Lines',
        required=False)

    x_product_ids = fields.One2many(
        comodel_name='free.zone.products',
        inverse_name='x_operation_id',
        string='Products')

    x_value_mismatch_warning = fields.Char(
        string='Value Mismatch Warning',
        compute='_compute_value_mismatch_warning',
        required=False)

    x_partner_id = fields.Many2one('res.partner', string="Vendor")

    @api.model
    def create(self, vals):
        res = super(FreeZoneOperations, self).create(vals)
        # if 'x_tag_ids' in vals:
        #     self.x_tag_ids._track_many2many_changes(res, 'x_tag_ids', new_values=vals['x_tag_ids'])
        for rec in res:
            if rec.x_attachment_id:
                rec.x_attachment_id.write({'res_model': self._name, 'res_id': rec.id})
        return res

    def write(self, vals):
        old_values = self.x_tag_ids.ids
        res = super(FreeZoneOperations, self).write(vals)
        new_values = self.x_tag_ids.ids
        if 'x_tag_ids' in vals:
            self.x_tag_ids._track_many2many_changes(
                self, 'x_tag_ids', old_values=old_values, new_values=new_values
            )
        for rec in self:
            if rec.x_attachment_id:
                rec.x_attachment_id.write({'res_model': self._name, 'res_id': rec.id})
        return res

    @api.depends('x_form_field_13')
    def _compute_currency_id(self):
        for rec in self:
            rec.x_currency_id = rec.x_form_field_13.id

    @api.depends('x_form_field_07', 'x_product_ids', 'x_product_ids.x_subtotal')
    def _compute_value_mismatch_warning(self):
        for rec in self:
            if round(rec.x_form_field_07, 2) != round(sum(rec.x_product_ids.mapped('x_subtotal')), 2):
                rec.x_value_mismatch_warning = ('Declared value (Mal Bedeli Toplamları) does not match with the '
                                                'products total value.')
            else:
                rec.x_value_mismatch_warning = False

    @api.onchange('x_type')
    def _onchange_x_type(self):
        for rec in self:
            if rec.x_type == 'purchase':
                rec.x_consolidation_ids = False
            elif rec.x_type == 'consolidation':
                rec.x_purchase_ids = False
            else:
                rec.x_purchase_ids = False
                rec.x_consolidation_ids = False
            rec.x_partner_id = False

    @api.onchange('x_purchase_ids', 'x_consolidation_ids')
    def update_vendor_id(self):
        for rec in self:
            if rec.x_purchase_ids:
                rec.x_partner_id = rec.x_purchase_ids.mapped('partner_id')[0].id
            elif rec.x_consolidation_ids:
                rec.x_partner_id = rec.x_consolidation_ids.mapped('x_partner_id')[0].id
            else:
                rec.x_partner_id = False

    @api.depends(
        'x_type', 'x_purchase_ids', 'x_consolidation_ids', 'x_form_field_01', 'x_form_field_03', 'x_product_ids.x_tracking_id'
    )
    def _compute_folder_name(self):
        for rec in self:
            if rec.x_type == 'purchase':
                rec.x_folder_name = '%s - %s - %s - %s - %s' % (
                    rec.x_form_field_01,
                    rec.x_form_field_03,
                    ', '.join(rec.x_product_ids.mapped('x_tracking_id').mapped('display_name')),
                    ', '.join(rec.x_purchase_ids.mapped('partner_id').mapped('country_id').mapped('name')),
                    ', '.join(rec.x_purchase_ids.mapped('partner_id').mapped('name')),
                )
            elif rec.x_type == 'consolidation':
                rec.x_folder_name = '%s - %s - %s - %s - %s' % (
                    rec.x_form_field_01,
                    rec.x_form_field_03,
                    ', '.join(rec.x_product_ids.mapped('x_tracking_id').mapped('display_name')),
                    ', '.join(rec.x_consolidation_ids.mapped('x_partner_id').mapped('country_id').mapped('name')),
                    ', '.join(rec.x_consolidation_ids.mapped('x_partner_id').mapped('name')),
                )
            else:
                rec.x_folder_name = 'Operations'

    def compute_landed_cost_lines(self):
        for rec in self:
            rec.x_cost_lines_ids = [(2, cost_line.id) for cost_line in rec.x_cost_lines_ids]
            cost_line_ids = self.env['stock.landed.cost'].search([
                ('picking_ids', 'in', rec.x_receipt_ids.mapped('x_picking_id').ids),
            ]).mapped('cost_lines')
            cost_lines = [(0, 0, {
                'x_cost_line_id': cost_line.id,
                'x_product_id': cost_line.product_id.id,
                'x_split_method': cost_line.split_method,
                'x_unit_price': cost_line.price_unit,
            }) for cost_line in cost_line_ids]
            rec.x_cost_lines_ids = cost_lines

    def compute_landed_cost(self):
        for rec in self:
            amount_equal = sum(rec.x_cost_lines_ids.filtered(lambda l: l.x_split_method == 'equal').mapped('x_unit_price'))
            amount_quantity = sum(rec.x_cost_lines_ids.filtered(lambda l: l.x_split_method == 'by_quantity').mapped('x_unit_price'))
            amount_current_cost_price = sum(rec.x_cost_lines_ids.filtered(lambda l: l.x_split_method == 'by_current_cost_price').mapped('x_unit_price'))
            amount_weight = sum(rec.x_cost_lines_ids.filtered(lambda l: l.x_split_method == 'by_weight').mapped('x_unit_price'))
            amount_volume = sum(rec.x_cost_lines_ids.filtered(lambda l: l.x_split_method == 'by_volume').mapped('x_unit_price'))

            total_qty = sum(rec.x_product_ids.mapped('x_quantity'))
            total_weight = sum([line.x_quantity * line.x_unit_weight for line in rec.x_product_ids])
            total_volume = sum(rec.x_product_ids.mapped('x_volume'))
            total_value = sum(rec.x_product_ids.mapped('x_subtotal'))

            equal_amount_addition = amount_equal / len(rec.x_product_ids) if rec.x_product_ids else 0
            for product in rec.x_product_ids:
                product.x_new_subtotal = product.x_subtotal + equal_amount_addition
                product.x_new_subtotal += product.x_quantity / total_qty * amount_quantity if total_qty else 0
                product.x_new_subtotal += product.x_subtotal / total_value * amount_current_cost_price if total_value else 0
                product.x_new_subtotal += (product.x_unit_weight * product.x_quantity) / total_weight * amount_weight if total_weight else 0
                product.x_new_subtotal += product.x_volume / total_volume * amount_volume if total_volume else 0
                product.x_new_subtotal = round(product.x_new_subtotal, 2)

    def update_receipt_list(self):
        for rec in self:
            rec.x_receipt_ids = [(2, receipt.id) for receipt in rec.x_receipt_ids]

            if rec.x_type == 'purchase':
                receipt_ids = rec.x_purchase_ids.mapped('picking_ids').filtered(lambda l: l.state != 'cancel').ids
                receipt_list = [(0, 0, {'x_picking_id': receipt}) for receipt in receipt_ids]
            elif rec.x_type == 'consolidation':
                receipt_ids = rec.x_consolidation_ids.mapped('x_receipt_ids')
                receipt_list = [(0, 0, {
                    'x_consolidation_id': receipt.x_consolidation_id.id, 'x_picking_id': receipt.x_picking_id.id
                }) for receipt in receipt_ids]

            rec.x_receipt_ids = receipt_list
            rec.x_bill_ids.update({
                'x_related_po_s': rec.x_receipt_ids.mapped('x_purchase_id').ids,
                'x_picking_ids': rec.x_receipt_ids.mapped('x_picking_id').ids,
            })
            rec.update_product_list()

    def update_product_list(self):
        for rec in self:
            rec.x_product_ids = [(2, product.id) for product in rec.x_product_ids]

            receipt_ids = rec.x_receipt_ids.mapped('x_picking_id')
            move_ids = receipt_ids.mapped('move_ids_without_package').filtered(lambda l: l.quantity_done != 0)
            product_list = [(0, 0, {
                'x_picking_id': move.picking_id.id,
                'x_product_id': move.product_id.id,
                'x_form_field_03': move.product_id.x_form_field_03,
                'x_uom_id': move.product_uom.id,
                'x_quantity': move.quantity_done,
                'x_unit_price': move.purchase_line_id.price_unit if move.purchase_line_id else 0,
            }) for move in move_ids if
                            move.product_id.x_form_field_03 == rec.x_form_field_03 or rec.x_ignore_subject_of_transaction]
            rec.x_product_ids = product_list
            rec.get_pdf_data()

    def get_pdf_data(self):
        for rec in self:
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
            # replace multiple spaces and line feed with tab
            formatted_data = re.sub('  +', '\t', re.sub('\n', '\t', pdf_data))
            # split by new line and remove empty lines
            data = [item.strip() for item in formatted_data.split('\t') if item]

            error_message = ['Following are the mismatched fields in the PDF file.', 'PDF Field ---> Odoo Field']

            translation_dict = {
                'A.B.D.': 'United States',
                'Almanya': 'Germany',
                'Türkiye': 'Turkey',
                'Malezya': 'Malaysia',
                'TL': 'TRY',
            }

            form_field_01 = False
            form_field_02 = False
            form_field_03 = False
            form_field_04 = False
            form_field_05 = False
            form_field_06 = False
            form_field_07 = False
            form_field_08 = False
            form_field_09 = False
            form_field_10 = False
            form_field_11 = False
            form_field_12 = False
            form_field_13 = False
            form_field_14 = False

            for index in range(len(data)):
                if 'No :' in data[index] and not form_field_01:
                    form_field_01 = data[index + 1]
                elif 'İŞLEM YÖNÜ' in data[index] and not form_field_02:
                    form_field_02 = data[index + 3]
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_02 and rec.x_form_field_02 != form_field_02:
                        error_message.append('%s ---> %s' % (form_field_02, rec.x_form_field_02))
                elif 'İŞLEM KONUSU' in data[index] and not form_field_03:
                    form_field_03 = data[index + 1]
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_03 and rec.x_form_field_03 != form_field_03:
                        error_message.append('%s ---> %s' % (form_field_03, rec.x_form_field_03))
                elif 'İŞLEM TÜRÜ' in data[index] and not form_field_04:
                    form_field_04 = data[index + 1]
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_04 and rec.x_form_field_04 != form_field_04:
                        error_message.append('%s ---> %s' % (form_field_04, rec.x_form_field_04))
                elif 'SEVKİYAT ŞEKLİ' in data[index] and not form_field_05:
                    form_field_05 = data[index + 3]
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_05 and rec.x_form_field_05 != form_field_05:
                        error_message.append('%s ---> %s' % (form_field_05, rec.x_form_field_05))
                elif ('TAŞIT CİNSİ' in data[index] or 'TAIT CNS' in data[index]) and not form_field_06:
                    form_field_06 = data[index + 2]
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_06 and rec.x_form_field_06 != form_field_06:
                        error_message.append('%s ---> %s' % (form_field_06, rec.x_form_field_06))
                elif 'Mal Bedeli Toplamları' in data[index] and not form_field_07:
                    form_field_07 = float(data[index + 5].split(' ')[0])
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_07 and rec.x_form_field_07 != form_field_07:
                        error_message.append('%s ---> %s' % (form_field_07, rec.x_form_field_07))
                    currency = data[index + 5].split(' ')[1]
                    currency = 'TRY' if currency == 'TL' else currency
                    form_field_13 = self.env['res.currency'].search([('name', '=', currency)]).id
                elif 'CIF Toplamı' in data[index] and not form_field_08:
                    form_field_08 = float(data[index + 5].split(' ')[0])
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_08 and rec.x_form_field_08 != form_field_08:
                        error_message.append('%s ---> %s' % (form_field_08, rec.x_form_field_08))
                    currency = data[index + 5].split(' ')[1]
                    currency = 'TRY' if currency == 'TL' else currency
                    form_field_14 = self.env['res.currency'].search([('name', '=', currency)]).id
                elif 'GİRİŞ / ÇIKIŞ' in data[index] and not form_field_09:
                    form_field_09 = datetime.strptime(data[index + 7], ":%d.%m.%Y").date()
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_09 and rec.x_form_field_09 != form_field_09:
                        error_message.append('%s ---> %s' % (form_field_09, rec.x_form_field_09))
                elif 'Brüt Ağırlık Toplamı' in data[index] and not form_field_10:
                    form_field_10 = float(data[index + 5].split(' ')[0])
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_10 and rec.x_form_field_10 != form_field_10:
                        error_message.append('%s ---> %s' % (form_field_10, rec.x_form_field_10))
                elif 'Tarih :' in data[index] and not form_field_11:
                    form_field_11 = datetime.strptime(data[index + 1], "%d.%m.%Y").date()
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_11 and rec.x_form_field_11 != form_field_11:
                        error_message.append('%s ---> %s' % (form_field_11, rec.x_form_field_11))
                elif 'Kap Toplamları' in data[index] and not form_field_12:
                    form_field_12 = float(data[index + 5].split(' ')[0])
                    if rec.x_form_field_01 and rec.x_form_field_01 == form_field_01 \
                            and rec.x_form_field_12 and rec.x_form_field_12 != form_field_12:
                        error_message.append('%s ---> %s' % (form_field_12, rec.x_form_field_12))

            if len(error_message) > 2:
                raise UserError('\n'.join(error_message))

            for product in rec.x_product_ids:
                try:
                    product_name = product.x_product_id.name.upper()

                    # Ülke / Menşei
                    country_of_origin = [
                        data[data.index(item) - 1] for item in data if product_name in item
                    ][0].split('/')[1].strip()
                    country_id = self.env['res.country'].search([
                        '|', ('x_turkish_translation', '=', country_of_origin), ('name', '=', country_of_origin),
                    ])
                    product.x_country_id = country_id.id or product.x_country_id.id

                    # Malın Cinsi
                    if self.env.user.lang == 'tr_TR':
                        product.description = [data[data.index(item)] for item in data if product_name in item][0]
                    else:
                        product.x_description_translation = [data[data.index(item)] for item in data if product_name in item][0]
                    product.x_product_id.onchange_description_field()
                    product.x_product_id.onchange_description_translation_field()

                    # GTIP
                    hs_code = [data[data.index(item) + 1] for item in data if product_name in item][0]

                    hs_code_id = self.env['hs.code.database'].search([
                        ('x_hs_code', '=', hs_code), ('x_country_id', '=', 224)
                    ])
                    if not hs_code_id:
                        hs_code_id = self.env['hs.code.database'].create({'x_country_id': 224, 'x_hs_code': hs_code})
                    product.x_hs_code_tr_id = hs_code_id.id or product.x_hs_code_tr_id.id
                except IndexError:
                    try:
                        qty = str(round(product.x_quantity, 2)) if product.x_quantity % 1 else str(
                            int(product.x_quantity))
                        subtotal = str(round(product.x_subtotal, 2)) if product.x_subtotal % 1 else str(
                            int(product.x_subtotal))
                        field_index = -8 if [data[data.index(item) - 4] for item in data if subtotal in item][
                                                0] == 'KAP' else -7

                        # Ülke / Menşei (Menşei)
                        country_of_origin = [
                            data[data.index(item) + field_index]
                            for item in data if subtotal in item and qty == data[data.index(item) - 3]
                        ][0].split('/')[1].strip()

                        country_id = self.env['res.country'].search([
                            '|', ('x_turkish_translation', '=', country_of_origin), ('name', '=', country_of_origin),
                        ])
                        product.x_country_id = country_id.id or product.x_country_id.id

                        # Malın Cinsi
                        if self.env.user.lang == 'tr_TR':
                            product.description = [
                                data[data.index(item) + field_index + 1]
                                for item in data if subtotal in item and qty == data[data.index(item) - 3]
                            ][0]
                        else:
                            product.x_description_translation = [
                                data[data.index(item) + field_index + 1]
                                for item in data if subtotal in item and qty == data[data.index(item) - 3]
                            ][0]
                        product.x_product_id.onchange_description_field()
                        product.x_product_id.onchange_description_translation_field()

                        # GTIP
                        hs_code = [
                            data[data.index(item) + field_index + 2]
                            for item in data if subtotal in item and qty == data[data.index(item) - 3]
                        ][0]

                        hs_code_id = self.env['hs.code.database'].search([
                            ('x_hs_code', '=', hs_code), ('x_country_id', '=', 224)
                        ])
                        if not hs_code_id:
                            hs_code_id = self.env['hs.code.database'].create(
                                {'x_country_id': 224, 'x_hs_code': hs_code})
                        product.x_hs_code_tr_id = hs_code_id.id or product.x_hs_code_tr_id.id
                    except IndexError:
                        pass

            rec.x_form_field_01 = form_field_01
            rec.x_form_field_02 = form_field_02
            rec.x_form_field_03 = form_field_03
            rec.x_form_field_04 = form_field_04
            rec.x_form_field_05 = form_field_05
            rec.x_form_field_06 = form_field_06
            rec.x_form_field_07 = form_field_07
            rec.x_form_field_08 = form_field_08
            rec.x_form_field_09 = form_field_09
            rec.x_form_field_10 = form_field_10
            rec.x_form_field_11 = form_field_11
            rec.x_form_field_12 = form_field_12
            rec.x_form_field_13 = form_field_13
            rec.x_form_field_14 = form_field_14

            rec.x_receipt_ids.mapped('x_picking_id').update({
                'x_attachment_name': rec.x_attachment_name,
                'x_attachment': rec.x_attachment,
                'x_form_field_01': rec.x_form_field_01,
                'x_form_field_02': rec.x_form_field_02,
                'x_form_field_03': rec.x_form_field_03,
                'x_form_field_04': rec.x_form_field_04,
                'x_form_field_05': rec.x_form_field_05,
                'x_form_field_06': rec.x_form_field_06,
                'x_form_field_07': rec.x_form_field_07,
                'x_form_field_08': rec.x_form_field_08,
                'x_form_field_09': rec.x_form_field_09,
                'x_form_field_10': rec.x_form_field_10,
                'x_form_field_11': rec.x_form_field_11,
                'x_form_field_12': rec.x_form_field_12,
                'x_form_field_13': rec.x_form_field_13.id,
                'x_form_field_14': rec.x_form_field_14.id,
            })

    def action_create_landed_cost_bill(self):
        for rec in self:
            bill_id = self.env['account.move'].create({
                'type': 'in_invoice',
                # 'partner_id': rec.x_partner_id.id,
                # 'partner_shipping_id': rec.x_partner_id.id,
                'ref': '%s' % rec.x_form_field_01,
                'invoice_date': rec.x_form_field_09,
                'journal_id': 1 if rec.x_receipt_ids.mapped('x_picking_id')[0].company_id.id == 1 else 97,
                'invoice_incoterm_id': False,
                'x_purchase_type': 'Clearing',
                'x_item_type': 'Landed Cost',
                'x_related_po_s': rec.x_receipt_ids.mapped('x_purchase_id').ids,
                'x_picking_ids': rec.x_receipt_ids.mapped('x_picking_id').ids,
                'x_free_zone_operation_id': rec.id,
                'x_attachment_name': rec.x_attachment_name,
                'x_attachment': rec.x_attachment,
                'x_form_field_01': rec.x_form_field_01,
                'x_form_field_02': rec.x_form_field_02,
                'x_form_field_03': rec.x_form_field_03,
                'x_form_field_04': rec.x_form_field_04,
                'x_form_field_05': rec.x_form_field_05,
                'x_form_field_06': rec.x_form_field_06,
                'x_form_field_07': rec.x_form_field_07,
                'x_form_field_08': rec.x_form_field_08,
                'x_form_field_09': rec.x_form_field_09,
                'x_form_field_10': rec.x_form_field_10,
                'x_form_field_11': rec.x_form_field_11,
                'x_form_field_12': rec.x_form_field_12,
                'x_form_field_13': rec.x_form_field_13.id,
                'x_form_field_14': rec.x_form_field_14.id,
            })
            rec.x_bill_ids = [(4, bill_id.id)]
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            return dict(action, view_mode='form', res_id=bill_id.id, views=[(False, 'form')])

    def action_view_bills(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        domain = [('id', 'in', self.x_bill_ids.ids)]
        views = [(self.env.ref('account.view_invoice_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, views=views)

    def action_view_landed_costs(self):
        self.ensure_one()
        action = self.env.ref('stock_landed_costs.action_stock_landed_cost').read()[0]
        domain = [('id', 'in', self.x_bill_ids.mapped('landed_costs_ids').ids)]
        context = dict(self.env.context)
        views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree').id, 'tree'), (False, 'form'),
                 (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', self.x_receipt_ids.mapped('x_picking_id').ids)]
        return action

    def unlink(self):
        for rec in self:
            rec.x_receipt_ids.unlink()
            rec.x_cost_lines_ids.unlink()
            rec.x_product_ids.unlink()
        return super(FreeZoneOperations, self).unlink()


class FreeZoneReceipts(models.Model):
    _name = "free.zone.receipts"
    _description = "Free Zone Receipts"
    _rec_name = 'x_picking_id'

    x_operation_id = fields.Many2one(comodel_name='free.zone.operations', string='Consolidation', required=False)

    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', required=False)
    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Receipt', required=False)

    x_purchase_id = fields.Many2one(related="x_picking_id.purchase_id")
    x_priority = fields.Selection(related="x_picking_id.priority", readonly=False, store=True)
    x_status = fields.Selection(related="x_picking_id.state")
    x_tracking_id = fields.Many2one(related="x_picking_id.x_tracking_id", readonly=False, store=True)
    x_volume = fields.Float(related="x_tracking_id.x_volume", store=True)
    x_weight = fields.Float(related="x_tracking_id.x_weight", readonly=False, store=True)

    def open_url(self):
        for rec in self:
            if rec.x_tracking_id.x_carrier_id.x_tracking_url and rec.x_tracking_id.x_tracking_ref:
                return {
                    'type': 'ir.actions.act_url',
                    'url': rec.x_tracking_id.x_carrier_id.x_tracking_url.replace(
                        '{Tracking Ref}', rec.x_tracking_id.x_tracking_ref
                    ),
                    'target': 'new',
                }


class FreeZoneLandedCosts(models.Model):
    _name = "free.zone.landed.costs"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Free Zone Landed Costs"

    x_operation_id = fields.Many2one(comodel_name='free.zone.operations', string='Consolidation', required=False)
    x_cost_line_id = fields.Many2one(comodel_name='stock.landed.cost.lines', string='Cost Line', required=False)
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    x_split_method = fields.Selection(
        string='Split Method',
        selection=[
            ('equal', 'Equal'),
            ('by_quantity', 'By Quantity'),
            ('by_current_cost_price', 'By Current Cost'),
            ('by_weight', 'By Weight'),
            ('by_volume', 'By Volume'),
            ('custom_duty', 'Custom Duty'),
            ('additional_custom_duty', 'Additional Custom Duty'),
            ('regulatory_duty', 'Regulatory Duty'),
        ], required=True, default='equal')
    x_unit_price = fields.Float(string='Cost', required=False)


class FreeZoneProducts(models.Model):
    _name = "free.zone.products"
    _description = "Free Zone Products"
    _rec_name = 'x_product_id'

    x_operation_id = fields.Many2one(comodel_name='free.zone.operations', string='Consolidation', required=False)
    x_currency_id = fields.Many2one(related="x_operation_id.x_currency_id")

    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Receipt', required=False)
    x_tracking_id = fields.Many2one(related="x_picking_id.x_tracking_id", readonly=False, store=True)

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_description = fields.Text(related="x_product_id.description", readonly=False, store=True)
    x_form_field_03 = fields.Selection(related="x_product_id.x_form_field_03", readonly=False, store=True)
    x_country_id = fields.Many2one(related="x_product_id.x_country_id", readonly=False, store=True)
    x_description_translation = fields.Text(related="x_product_id.x_description_translation", readonly=False, store=True)
    x_hs_code_tr_id = fields.Many2one(related="x_product_id.x_hs_code_tr_id", readonly=False, store=True)
    x_unit_weight = fields.Float(related="x_product_id.x_unit_weight", readonly=False, store=True)
    x_volume = fields.Float(related="x_product_id.volume", readonly=False, store=True)

    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)

    x_quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    x_unit_price = fields.Float(string='Unit Price', required=False, digits='Product Price')
    x_subtotal = fields.Float(string='Subtotal', compute="_compute_subtotal", store=True)

    x_new_unit = fields.Float(string='New Unit', compute="_compute_new_unit", store=True, digits='Product Price')
    x_new_subtotal = fields.Float(string='New Subtotal', required=False)

    @api.depends('x_quantity', 'x_unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.x_subtotal = round(rec.x_quantity * rec.x_unit_price, 2)

    @api.depends('x_new_subtotal')
    def _compute_new_unit(self):
        for rec in self:
            rec.x_new_unit = round(rec.x_new_subtotal / rec.x_quantity, 5) if rec.x_quantity else 0
