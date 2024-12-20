from odoo import api, fields, models
from odoo.exceptions import UserError

import base64, io, os, csv
from xlrd import open_workbook


class BomLineAdditionWizard(models.TransientModel):
    _name = "bom.line.addition.wizard"
    _description = "BoM Line Addition"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product', required=False)
    x_taraz_part_id = fields.Many2one('taraz.part.number', 'Taraz Part', related="x_product_id.x_taraz_part_number_id")

    x_ref_des = fields.Char(string='Ref Des', required=False)
    x_bom_lines = fields.Integer(string='BoM Lines', default=1, required=False)
    x_quantity = fields.Float(string='Quantity per Line', digits='Product Unit of Measure', default=1, required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)
    x_notes = fields.Char(string='Notes', required=False)

    x_critical = fields.Selection(selection=[('critical', 'Critical')], string='Critical')
    x_variant = fields.Selection(selection=[('variant', 'Variant')], string='Variant')
    x_investor_product = fields.Boolean(string="Investor Product?")

    x_import_file = fields.Binary(string="Import BoM Lines")
    x_file_name = fields.Char(string='File Name', required=False)

    @api.model
    def default_get(self, fields_list):
        res = super(BomLineAdditionWizard, self).default_get(fields_list)
        res.update({'x_bom_tool_id': self.env.context.get('active_id')})
        return res

    @api.onchange('x_product_id')
    def update_uom_id(self):
        for rec in self:
            rec.x_uom_id = rec.x_product_id.uom_id.id

    def add_bom_lines(self):
        for rec in self:
            bom_id = rec.x_bom_tool_id.x_base_bom_id
            if rec.x_import_file:
                filename, filetype = os.path.splitext(self.x_file_name)
                if filetype != '.csv':
                    raise UserError('Invalid file type!\nImport .csv file.')

                csv_data = base64.b64decode(rec.x_import_file)
                try:
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                except:
                    data_file = io.StringIO(csv_data.decode("latin-1"))

                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)

                header_row = ['RefDes', 'Part #', 'BoM Lines', 'Quantity', 'UoM']
                if any(x not in file_reader[0] for x in header_row):
                    raise UserError(
                        'Invalid file headers!'
                        '\n'
                        'They should be '
                        'RefDes | Part # | BoM Lines | Quantity | UoM'
                        ' in same sequence'
                    )

                bom_lines = []
                for row in file_reader:
                    if row[0] == 'RefDes':
                        continue

                    product_id = self.env['product.template'].search([('name', '=', row[1])])
                    if not product_id:
                        taraz_part_id = self.env['taraz.part.number'].search([('x_name', '=', row[1])])
                        if taraz_part_id:
                            product_id = taraz_part_id.x_alternate_ids.mapped('x_product_id')[0]
                    uom = self.env['uom.uom'].search([('name', '=', row[4])], limit=1)

                    count = bom_id.x_bom_line_ids.mapped('x_part_description').count('Manually Imported Parts')
                    ref_des = row[0].split(', ')
                    if int(row[2]) == len(ref_des):
                        for element in ref_des:
                            bom_lines.append((0, 0, {
                                'x_name': row[1],
                                'x_part_description': 'Manually Imported Parts',
                                'x_ref_des': element if int(row[2]) == len(ref_des) else '%s%s' % (element, count),
                                'x_product_id': product_id.id,
                                'x_quantity': row[3] or 1,
                                'x_uom_id': uom.id or product_id.uom_id.id,
                                'x_critical': rec.x_critical,
                                'x_notes': rec.x_notes,
                                'x_new': True,
                            }))
                    else:
                        for x in range(int(row[2])):
                            count += 1
                            bom_lines.append((0, 0, {
                                'x_name': row[1],
                                'x_part_description': 'Manually Imported Parts',
                                'x_ref_des': '%s%s' % (row[0], count),
                                'x_product_id': product_id.id,
                                'x_quantity': row[3] or 1,
                                'x_uom_id': uom.id or product_id.uom_id.id,
                                'x_critical': rec.x_critical,
                                'x_notes': rec.x_notes,
                                'x_new': True,
                            }))

                bom_id.x_bom_line_ids = bom_lines

            if rec.x_product_id:
                count = bom_id.x_bom_line_ids.mapped('x_part_description').count('Manually Added Parts')

                for x in range(rec.x_bom_lines):
                    count += 1
                    line_id = self.env['base.bom.lines'].create({
                        'x_base_bom_id': bom_id.id,
                        'x_name': rec.x_product_id.name,
                        'x_part_description': 'Manually Added Parts',
                        'x_ref_des': '%s%s' % (rec.x_ref_des, count),
                        'x_product_id': rec.x_product_id.id,
                        'x_quantity': rec.x_quantity,
                        'x_uom_id': rec.x_uom_id.id,
                        'x_critical': rec.x_critical,
                        'x_notes': rec.x_notes,
                        'x_new': True,
                    })
                    if rec.x_variant:
                        line_id.write({'x_variant': rec.x_variant})

            rec.x_bom_tool_id.filter_base_bom_lines()
            if rec.x_variant:
                rec.x_bom_tool_id.filter_variant_bom_lines()





