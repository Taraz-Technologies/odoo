from odoo import api, fields, models
from odoo.exceptions import UserError

import base64
import io
import csv
from xlrd import open_workbook


class ImportBomFiles(models.TransientModel):
    _name = "import.bom.files"
    _description = "Import BoM Files"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_product_type_fg = fields.Selection(related='x_bom_tool_id.x_product_type_fg')
    x_product_type_sfg = fields.Selection(related='x_bom_tool_id.x_product_type_sfg')

    x_base_product_id = fields.Many2one('product.template', 'Product', related='x_bom_tool_id.x_base_product_id')

    x_bom_file = fields.Binary(string="BoM File (.csv)")
    x_pnp_file = fields.Binary(string="PNP File (.csv)")

    x_pcb_product_id = fields.Many2one(comodel_name='product.template', string='Related PCB')

    x_import_type = fields.Selection(selection=[
        ('previous_data', 'Import with previous definitions'),
        ('raw_data', 'Raw Data'),
    ], string='Import Type', default='previous_data', )

    x_base_bom_id = fields.Many2one(comodel_name='base.bom', string='Definitions BoM',
                                    domain="[('x_product_id', '=', x_base_product_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super(ImportBomFiles, self).default_get(fields_list)
        res.update({
            'x_bom_tool_id': self.env.context.get('active_id'),
            'x_base_bom_id': self.env['bom.tool'].browse(self.env.context.get('active_id')).x_base_bom_id.id,
        })
        return res

    def import_files(self):
        for rec in self:
            if rec.x_product_type_fg == 'pcb' or rec.x_product_type_sfg == 'pcb':
                if not rec.x_bom_file or not rec.x_pnp_file:
                    raise UserError('Please select both BoM & PnP files!')

                # Get Data from files
                csv_data = base64.b64decode(rec.x_pnp_file)
                try:
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                except:
                    data_file = io.StringIO(csv_data.decode("latin-1"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)

                header_row = ['RefDes', 'Name', 'Pattern', 'X (mm)', 'Y (mm)', 'Side', 'Rotate', 'Value', 'Hierarchy']
                if any(x not in file_reader[0] for x in header_row):
                    raise UserError('Invalid PNP file!')
                elif all(x in file_reader[0] for x in header_row) and len(file_reader[0]) != len(header_row):
                    raise UserError('Invalid PNP file!')

                bom_lines_from_files = []
                for row in file_reader:
                    if row[0] == 'RefDes':
                        continue
                    elif not row[7]:
                        name = False
                    elif len(row) == 8:
                        name = row[7] if str(row[5]) in ('Top', 'Bottom') else row[8]
                    elif len(row) == 9:
                        if row[8] and 'Block' not in str(row[8]):
                            name = '%s,%s' % (row[7], row[8])
                        else:
                            name = row[7] if str(row[5]) in ('Top', 'Bottom') else row[8]
                    elif len(row) == 10:
                        if row[9] and 'Block' not in str(row[9]):
                            name = '%s,%s' % (row[8], row[9])
                        elif row[8] and 'Block' not in str(row[8]):
                            name = '%s,%s' % (row[7], row[8]) if str(row[5]) in ('Top', 'Bottom') else '%s,%s' % (
                            row[8], row[9]) if row[9] else row[8]
                        else:
                            name = row[7] if str(row[5]) in ('Top', 'Bottom') else row[8]
                    elif len(row) == 11:
                        if row[10] and 'Block' not in str(row[10]):
                            name = '%s,%s' % (row[9], row[10])
                        elif row[9] and 'Block' not in str(row[9]):
                            name = '%s,%s' % (row[8], row[9]) if str(row[5]) in ('Top', 'Bottom') else '%s,%s' % (
                            row[9], row[10]) if row[10] else '%s,%s' % (row[8], row[9]) if row[9] else row[8]
                        elif row[8] and 'Block' not in str(row[8]):
                            name = '%s,%s' % (row[7], row[8]) if str(row[5]) in ('Top', 'Bottom') else '%s,%s' % (
                            row[8], row[9]) if row[9] else row[8]
                        else:
                            name = row[7] if str(row[5]) in ('Top', 'Bottom') else row[8]
                    else:
                        name = False

                    if row[0] == 'RefDes' or name == '' or not name:
                        continue

                    name = name.upper()
                    name = name.replace('0.1UF', '100NF')
                    name = name.replace('NP0', 'C0G')
                    name = name.replace('NPO', 'C0G')

                    block = [x for x in row if 'Block' in str(x)]
                    block = block[0].split(' ')[0] if len(block) > 0 else False
                    bom_lines_from_files.append({
                        'ref_des': row[0],
                        'name': name,
                        'description': row[1].upper(),
                        'block': block,
                        'block_id': False,
                        'type': 'smd',
                        'dnp': 'dnp' if 'DNP' in str(row[0]) else False,
                    })

                csv_data = base64.b64decode(rec.x_bom_file)
                try:
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                except:
                    data_file = io.StringIO(csv_data.decode("latin-1"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)

                header_row = ['RefDes', 'Value', 'Name', 'Quantity']
                if any(x not in file_reader[0] for x in header_row):
                    raise UserError('Invalid BoM file!')
                if all(x in file_reader[0] for x in header_row) and len(file_reader[0]) != len(header_row):
                    raise UserError('Invalid BoM file!')

                pnp_ref_des = [data['ref_des'] for data in bom_lines_from_files]
                for row in file_reader:
                    if row[0] in ['RefDes', 'Value'] or row[1] in ['M3', 'M4', ''] or not row[1]:
                        continue
                    ref_des = row[0].split(', ')
                    for element in ref_des:
                        if element in pnp_ref_des or [ref_des for ref_des in pnp_ref_des if element + '_' in ref_des]:
                            continue

                        name = row[1].upper()
                        name = name.replace('0.1UF', '100NF')
                        name = name.replace('NP0', 'C0G')
                        name = name.replace('NPO', 'C0G')

                        bom_lines_from_files.append({
                            'ref_des': element,
                            'name': name,
                            'description': row[2].upper(),
                            'block': False,
                            'block_id': False,
                            'type': 'other',
                            'dnp': 'dnp' if 'DNP' in str(row[0]) else False,
                        })

                # Create Temp. Blocks
                blocks_from_files = []
                for line in [data for data in bom_lines_from_files if data['block']]:
                    block_number = [data for data in blocks_from_files if data['block'] == line['block']]
                    if block_number:
                        block_number = block_number[0]
                        block_line = [data for data in block_number['block_lines'] if data['name'] == line['name']]
                        if block_line:
                            block_line[0]['quantity'] += 1
                        else:
                            block_number['block_lines'].append({
                                'name': line['name'],
                                'description': line['description'],
                                'quantity': 1,
                                'type': line['type'],
                            })
                    else:
                        blocks_from_files.append({
                            'block': line['block'],
                            'block_lines': [{
                                'name': line['name'],
                                'description': line['description'],
                                'quantity': 1,
                                'type': line['type'],
                            }]
                        })

                # Create BoM with version
                bom_version = 'BOM.%s' % rec.x_pcb_product_id.name.split('.')[-1]
                base_bom_id = self.env['base.bom'].create({
                    'x_name': bom_version,
                    'x_product_id': rec.x_base_product_id.id,
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'x_bom_file': rec.x_bom_file,
                    'x_pnp_file': rec.x_pnp_file,
                })
                rec.x_bom_tool_id.x_base_bom_id = base_bom_id.id

                # Check if block exist if not then create and assign block to bom lines
                bom_tool_blocks = []
                block_id = False
                for block in blocks_from_files:
                    block_exist = False
                    block_ids = self.env['bom.blocks'].search([])
                    for block_id in block_ids:
                        if len(block['block_lines']) == len(block_id.x_bom_line_ids):
                            block_matched = True
                            for block_line in block_id.x_bom_line_ids:
                                matched_line = [line for line in block['block_lines'] if
                                                line['name'] == block_line.x_name and line[
                                                    'quantity'] == block_line.x_quantity]
                                if not matched_line:
                                    block_matched = False
                                    break
                            if block_matched:
                                block_exist = True

                                for line in [data for data in bom_lines_from_files if data['block'] == block['block']]:
                                    line['block_id'] = block_id.id

                                bom_block = [data for data in bom_tool_blocks if data['x_block_id'] == block_id.id]
                                if bom_block:
                                    bom_block[0]['x_quantity'] += 1
                                else:
                                    bom_tool_blocks.append({
                                        'x_bom_tool_id': rec.x_bom_tool_id.id,
                                        'x_block_id': block_id.id,
                                        'x_quantity': 1,
                                    })

                                block_id.x_bom_tool_ids = [(4, rec.x_bom_tool_id.id)]
                                break

                    if not block_exist:
                        block_id = self.env['bom.blocks'].create({'x_description': 'New'})

                        for line in block['block_lines']:
                            product_id = self.env['product.template'].search([('name', '=', line['name'])])
                            if not product_id:
                                taraz_part_id = self.env['taraz.part.number'].search([('x_name', '=', line['name'])])
                                if taraz_part_id:
                                    product_id = taraz_part_id.x_alternate_ids.mapped('x_product_id')[0]
                            block_id.x_bom_line_ids = [(0, 0, {
                                'x_name': line['name'],
                                'x_part_description': line['description'],
                                'x_product_id': product_id.id,
                                'x_quantity': line['quantity'],
                                'x_uom_id': product_id.uom_id.id,
                            })]

                        for line in [data for data in bom_lines_from_files if data['block'] == block['block']]:
                            line['block_id'] = block_id.id

                        bom_tool_blocks.append({
                            'x_bom_tool_id': rec.x_bom_tool_id.id,
                            'x_block_id': block_id.id,
                            'x_quantity': 1,
                        })

                        block_id.x_bom_tool_ids = [(4, rec.x_bom_tool_id.id)]

                rec.x_bom_tool_id.x_attached_block_ids.unlink()
                for block in bom_tool_blocks:
                    self.env['bom.tool.blocks'].create(block)

                design_bom_line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: not l.x_new)
                for line in bom_lines_from_files:
                    vals = {
                        'x_base_bom_id': base_bom_id.id,
                        'x_name': line['name'],
                        'x_part_description': line['description'],
                        'x_ref_des': line['ref_des'],
                        'x_line_block_id': line['block_id'],
                        'x_deleted': True if line['name'] == 'M3' else False
                    }

                    product_id = self.env['product.template'].search([('name', '=', line['name'])])
                    if not product_id:
                        taraz_part_id = self.env['taraz.part.number'].search([('x_name', '=', line['name'])])
                        if taraz_part_id:
                            product_id = taraz_part_id.x_alternate_ids.mapped('x_product_id')[0]

                    design_bom_line_id = design_bom_line_ids.filtered(lambda l: l.x_ref_des == line['ref_des'])
                    if design_bom_line_id and rec.x_import_type == 'previous_data':
                        vals['x_old_product_id'] = design_bom_line_id.x_old_product_id.id
                        vals['x_product_id'] = design_bom_line_id.x_product_id.id

                        vals['x_real_quantity'] = design_bom_line_id.x_real_quantity
                        vals['x_quantity'] = design_bom_line_id.x_quantity
                        vals['x_uom_id'] = design_bom_line_id.x_uom_id.id

                        vals['x_station_id'] = design_bom_line_id.x_station_id.id

                        vals['x_dnp'] = design_bom_line_id.x_dnp
                        vals['x_critical'] = design_bom_line_id.x_critical
                        vals['x_variant'] = design_bom_line_id.x_variant
                        vals['x_notes'] = design_bom_line_id.x_notes

                        vals['x_move_to_tool_id'] = design_bom_line_id.x_move_to_tool_id.id
                        vals['x_slave_bom_line_id'] = design_bom_line_id.x_slave_bom_line_id.id

                        vals['x_move_from_tool_id'] = design_bom_line_id.x_move_from_tool_id.id
                        vals['x_master_bom_line_id'] = design_bom_line_id.x_master_bom_line_id.id

                        design_bom_line_id.x_move_to_tool_id = False

                        vals['x_modified'] = design_bom_line_id.x_modified
                        vals['x_deleted'] = design_bom_line_id.x_deleted

                        vals['x_design_modified'] = True if name != design_bom_line_id.x_name else False
                    else:
                        vals['x_product_id'] = product_id.id
                        vals['x_quantity'] = 1
                        vals['x_uom_id'] = product_id.uom_id.id or False
                        vals['x_dnp'] = line['dnp']
                        vals['x_design_new'] = True

                    line_id = self.env['base.bom.lines'].create(vals)
                    line_id.move_line_to_bom()

                # Define Design deleted Lines
                ref_des_from_files = [data['ref_des'] for data in bom_lines_from_files]
                for line in design_bom_line_ids:
                    if line.x_ref_des not in ref_des_from_files:
                        line_id = line.copy({
                            'x_base_bom_id': base_bom_id.id,
                            'x_design_deleted': True,
                        })

                        line.x_move_to_tool_id = False
                        line_id.move_line_to_bom()

                # Add New lines created in odoo
                odoo_bom_line_ids = rec.x_base_bom_id.x_bom_line_ids.filtered(lambda l: l.x_new)
                for line in odoo_bom_line_ids:
                    line_id = line.copy({
                        'x_base_bom_id': base_bom_id.id,
                        'x_line_block_id': block_id.id if block_id else False
                    })

                    line.x_move_to_tool_id = False
                    line_id.move_line_to_bom()

                if rec.x_pcb_product_id:
                    vals = {
                        'x_base_bom_id': base_bom_id.id,
                        'x_name': rec.x_pcb_product_id.name,
                        'x_part_description': rec.x_pcb_product_id.description,
                        'x_ref_des': 'PCB1',
                        'x_product_id': rec.x_pcb_product_id.id,
                        'x_uom_id': rec.x_pcb_product_id.uom_id.id,
                    }
                    self.env['base.bom.lines'].create(vals)
            else:
                if not rec.x_bom_file:
                    raise UserError('Please select BoM file!')

                # Get Data from files
                file_data = base64.b64decode(rec.x_bom_file)
                workbook = open_workbook(file_contents=file_data)
                sheet = workbook.sheet_by_index(0)

                file_headers = ['RefDes', 'Product', 'Description', 'Quantity', 'UoM', 'Mounting Type',
                                'DNP', 'Critical', 'Variant', 'Notes', 'Investor Product?']
                idx = {
                    'RefDes': -1,
                    'Product': -1,
                    'Description': -1,
                    'Quantity': -1,
                    'UoM': -1,
                    'Mounting Type': -1,
                    'DNP': -1,
                    'Critical': -1,
                    'Variant': -1,
                    'Notes': -1,
                    'Investor Product?': -1,
                }

                for c_idx in range(sheet.ncols):
                    if sheet.cell_value(0, c_idx) in file_headers:
                        idx[sheet.cell_value(0, c_idx)] = c_idx

                if idx['Product'] == -1 and not idx['Quantity'] == -1:
                    raise UserError('Product and Quantity column is not defined in BoM file!')
                elif idx['Product'] == -1:
                    raise UserError('Product column is not defined in BoM file!')
                elif idx['Quantity'] == -1:
                    raise UserError('Quantity column is not defined in BoM file!')

                # Create BoM with version
                bom_version = self.env['base.bom'].search_count([('x_product_id', '=', rec.x_base_product_id.id)])
                bom_version = '%s%s' % (0, bom_version + 1)
                bom_version = 'BOM.%s' % bom_version[-2:]
                base_bom_id = self.env['base.bom'].create({
                    'x_name': bom_version,
                    'x_product_id': rec.x_base_product_id.id,
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'x_bom_file': rec.x_bom_file,
                })
                rec.x_bom_tool_id.x_base_bom_id = base_bom_id.id

                ref_des = 1
                for r_idx in range(1, sheet.nrows):
                    domain = [('name', '=', sheet.cell_value(r_idx, idx['Product']))]
                    product_id = self.env['product.template'].search(domain)
                    if not product_id:
                        domain = [('x_name', '=', sheet.cell_value(r_idx, idx['Product']))]
                        taraz_part_id = self.env['taraz.part.number'].search(domain)
                        if taraz_part_id:
                            product_id = taraz_part_id.x_alternate_ids.mapped('x_product_id')[0]

                    uom_name = sheet.cell_value(r_idx, idx['UoM']) if idx['UoM'] != -1 else product_id.uom_id.name
                    uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                    vals = {
                        'x_base_bom_id': base_bom_id.id,
                        'x_ref_des': sheet.cell_value(r_idx, idx['RefDes']) if idx['RefDes'] != -1 else 'PRT%s' % ref_des,
                        'x_product_id': product_id.id,
                        'x_quantity': sheet.cell_value(r_idx, idx['Quantity']) if idx['Quantity'] != -1 else 1,
                        'x_uom_id': uom.id if uom else product_id.uom_id.id,
                        'x_name': sheet.cell_value(r_idx, idx['Product']),
                        'x_part_description': sheet.cell_value(r_idx, idx['Description']) if idx['Description'] != -1 else False,
                        'x_notes': sheet.cell_value(r_idx, idx['Notes']) if idx['Notes'] != -1 else False,
                        'x_type': sheet.cell_value(r_idx, idx['Mounting Type']) if idx['Mounting Type'] != -1 else False,
                        'x_dnp': sheet.cell_value(r_idx, idx['DNP']) if idx['DNP'] != -1 else False,
                        'x_critical': sheet.cell_value(r_idx, idx['Critical']) if idx['Critical'] != -1 else False,
                        'x_variant': sheet.cell_value(r_idx, idx['Variant']) if idx['Variant'] != -1 else False,
                        'x_investor_product': sheet.cell_value(r_idx, idx['Investor Product?']) if idx['Investor Product?'] != -1 else False,
                    }
                    line_id = self.env['base.bom.lines'].create(vals)
                    line_id.move_line_to_bom()
                    ref_des += 1

            rec.x_bom_tool_id.filter_base_bom_lines()
