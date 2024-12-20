from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html_escape as escape
import logging

_logger = logging.getLogger("*__addons_custom__*")


class BaseBomLines(models.Model):
    _name = "base.bom.lines"
    _description = "Base BoM Lines"
    _rec_name = "display_name"

    x_base_bom_id = fields.Many2one(comodel_name='base.bom', string='Base BoM', required=False)
    x_base_product_id = fields.Many2one(related='x_base_bom_id.x_product_id', store=True)
    x_bom_tool_id = fields.Many2one(related="x_base_bom_id.x_bom_tool_id", store=True)

    x_update_block_line = fields.Boolean(string='Update Block Lines', compute='_compute_block_lines', store=True)

    display_name = fields.Char(compute="_compute_display_name", store=True)
    x_line_select = fields.Boolean(string='Select', store=True)
    x_aps_line_select = fields.Boolean(string='Select', store=True)

    x_ref_des = fields.Char(string='RefDes', readonly=True)
    x_name = fields.Char(string='Part # (Design)', readonly=True)
    x_part_description = fields.Char(string='Description (Design)', readonly=True)

    x_old_product_id = fields.Many2one(comodel_name='product.template', string='Old Product', readonly=True)

    x_product_id = fields.Many2one(comodel_name='product.template', string='Part #', required=False)
    x_active = fields.Boolean(related='x_product_id.active')
    x_real_quantity = fields.Float(string='Real Quantity', compute="_compute_real_quantity", store=True)
    x_quantity = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM')
    x_prd_investor_product = fields.Boolean(compute="_compute_investor_product", store=True)

    image_128 = fields.Image(related='x_product_id.image_128', string="Image")
    x_taraz_part_id = fields.Many2one(related="x_product_id.x_taraz_part_number_id", store=True)
    x_enable_safety_stock = fields.Boolean(related="x_taraz_part_id.x_enable_safety_stock", store=True, readonly=False)
    x_description = fields.Text(string="Description", related="x_product_id.description")

    x_line_block_id = fields.Many2one(comodel_name='bom.blocks', string='Block', required=False)
    x_station_id = fields.Many2one(comodel_name='bom.line.station', string='Station')
    x_notes = fields.Char(string='Notes')
    x_update_variant_notes = fields.Boolean(compute="update_variant_notes")

    x_move_to_tool_id = fields.Many2one('bom.tool', string='Moved to', domain="[('id', '!=', x_bom_tool_id)]")
    x_move_from_tool_id = fields.Many2one('bom.tool', string='Moved from', readonly=True)
    x_slave_bom_line_id = fields.Many2one('base.bom.lines', 'Slave BoM Line', compute='move_line_to_bom', store=True)
    x_master_bom_line_id = fields.Many2one('base.bom.lines', string='Master BoM Line', readonly=True, store=True)

    x_type = fields.Selection(selection=[
        ('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER'),
    ], string='Mounting Type', readonly=False, related='x_taraz_part_id.x_mounting_type', store=True)

    x_dnp = fields.Selection(selection=[('dnp', 'DNP')], string='DNP')
    x_critical = fields.Selection(selection=[('critical', 'Critical')], string='Critical')
    x_variant = fields.Selection(selection=[('variant', 'Variant')], string='Variant')
    x_investor_product = fields.Boolean(string='Investor Product?')

    x_to_be_reviewed = fields.Boolean(string='To be reviewed', store=True, readonly=False)

    x_design_new = fields.Boolean(string='Design New', store=True, readonly=True)
    x_design_modified = fields.Boolean(string='Design Modified', store=True, readonly=True)
    x_design_deleted = fields.Boolean(string='Design Deleted', store=True, readonly=True)

    x_new = fields.Boolean(string='Odoo New', store=True, readonly=True)
    x_modified = fields.Boolean(string='Odoo Modified', compute='_compute_modified_status', store=True, readonly=True)
    x_deleted = fields.Boolean(string='Odoo Deleted', store=True, readonly=True)

    x_usage_ids = fields.One2many(comodel_name='component.usage', inverse_name='x_base_bom_line_id',
                                  string='Component Usage', compute="_compute_usage", store=True)
    x_routing_id = fields.Many2one(
        comodel_name='mrp.routing', string='Routing',
        related='x_base_bom_id.x_routing_id', store=True, readonly=False,
        help="The list of operations to produce the finished product. The routing is mainly used to "
             "compute work center costs during operations and to plan future loads on work centers "
             "based on production planning.")
    x_operation_id = fields.Many2one(
        comodel_name='mrp.routing.workcenter', string='Consumed in Operation',
        check_company=True, company_dependent=True, domain="[('routing_id', '=', x_routing_id)]",
        help="The operation where the components are consumed, or the finished products created.")

    x_custom_tag_ids = fields.Many2many('custom.tags', string="Tags")



    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = ['|', '|', '|',  '|', '|', ('x_ref_des', operator, name), ('x_name', operator, name),
                      ('x_product_id.name', operator, name), ('x_taraz_part_id.x_name', operator, name),
                      ('x_part_description', operator, name), ('x_product_id.description', operator, name)]
            product_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))

    @api.onchange('x_product_id')
    def update_uom_id(self):
        for rec in self:
            rec.x_uom_id = rec.x_product_id.uom_id.id

    @api.depends('x_notes')
    def update_variant_notes(self):
        for rec in self:
            if rec.x_base_product_id.id == rec.x_bom_tool_id.x_base_product_id.id and rec.x_variant == 'variant':
                rec.x_bom_tool_id.x_variant_ids.mapped('x_bom_id').mapped('x_bom_line_ids').filtered(
                    lambda l: l.x_ref_des == rec.x_ref_des
                ).write({'x_notes': rec.x_notes})

    @api.depends('x_product_id', 'x_quantity', 'x_uom_id')
    def _compute_real_quantity(self):
        for rec in self:
            if rec.x_product_id.uom_id and rec.x_uom_id:
                rec.x_real_quantity = rec.x_uom_id._compute_quantity(rec.x_quantity, rec.x_product_id.uom_id, rounding_method='HALF-UP')

    @api.depends('x_investor_product')
    def _compute_investor_product(self):
        for rec in self:
            rec.x_prd_investor_product = False
            self.env['base.bom.lines'].search([
                ('x_investor_product', '!=', False), ('x_product_id', '=', rec.x_product_id.id)
            ]).update({'x_prd_investor_product': True})

    @api.depends('x_taraz_part_id', 'x_taraz_part_id.x_alternate_ids', 'x_taraz_part_id.x_compromised_ids', 'x_dnp', 'x_deleted')
    def _compute_usage(self):
        for rec in self:
            rec.x_usage_ids = False
        #     rec.x_usage_ids = [(2, line.id) for line in rec.x_usage_ids]
        #     rec.x_to_be_reviewed = False
        #     if not rec.x_bom_tool_id.x_base_product_id and (rec.x_dnp or rec.x_deleted):
        #         continue
        #
        #     usage_ids = []
        #     for line in rec.x_taraz_part_id.x_alternate_ids:
        #         usage_ids.append({
        #             'x_base_bom_line_id': rec.id,
        #             'x_alternate_id': line.id,
        #             'x_product_id': rec.x_bom_tool_id.x_base_product_id.id,
        #             'x_usage': 'auto_use',
        #         })
        #
        #     for line in rec.x_taraz_part_id.x_compromised_ids:
        #         usage_ids.append({
        #             'x_base_bom_line_id': rec.id,
        #             'x_compromised_id': line.id,
        #             'x_product_id': rec.x_bom_tool_id.x_base_product_id.id,
        #             'x_usage': 'use',
        #         })
        #
        #     self.env['component.usage'].create(usage_ids)
        #     if len(rec.x_usage_ids) > 1:
        #         if rec.x_bom_tool_id.state == 'active':
        #             rec.x_bom_tool_id.state = 'to_be_review'
        #         rec.x_to_be_reviewed = True

    @api.depends('x_line_block_id')
    def _compute_block_lines(self):
        for rec in self:
            if rec.x_master_bom_line_id:
                rec.x_master_bom_line_id.x_line_block_id = rec.x_line_block_id.id
            if rec.x_slave_bom_line_id:
                rec.x_slave_bom_line_id.x_line_block_id = rec.x_line_block_id.id

    @api.depends('x_move_to_tool_id')
    def move_line_to_bom(self):
        for rec in self:
            replacement_block_id = False
            if rec.x_slave_bom_line_id:
                rule_id = self.env['bom.line.rules'].search([('x_line_id', '=', rec._origin.id)])
                replacement_block_id = rule_id.x_replacement_block_id if rule_id else False
                rec.x_slave_bom_line_id.write({'x_variant': False})
                rec.x_slave_bom_line_id.unlink()

            if not rec.x_move_to_tool_id:
                break

            if rec.x_move_from_tool_id and rec.x_master_bom_line_id:
                raise UserError('Error! Cannot move line which is moved from other BoM')

            line_id = rec.copy({
                'x_base_bom_id': rec.x_move_to_tool_id.x_base_bom_id.id,
                'x_move_to_tool_id': False,
                'x_move_from_tool_id': rec.x_bom_tool_id.id,
                'x_master_bom_line_id': rec._origin.id,
            })

            line_id.write({'x_variant': rec.x_variant})

            if replacement_block_id:
                self.env['bom.line.rules'].create({
                    'x_bom_tool_id': rec.x_bom_tool_id.id,
                    'x_line_id': line_id.id,
                    'x_replacement_block_id': replacement_block_id.id,
                })

            rec.x_move_to_tool_id.filter_base_bom_lines()
            rec.write({'x_variant': False})
            rec.x_slave_bom_line_id = line_id.id

    @api.depends('x_product_id', 'x_taraz_part_id')
    def _compute_modified_status(self):
        for rec in self:
            if rec.x_name != rec.x_product_id.name and rec.x_name != rec.x_taraz_part_id.x_name and rec.x_product_id:
                rec.x_modified = True

    @api.depends('x_name', 'x_ref_des')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s (%s)' % (rec.x_name, rec.x_ref_des)

    def aps_lines_define(self):
        for rec in self:
            rec.x_bom_tool_id.x_search_aps_bom_lines = rec.x_taraz_part_id.x_name
            rec.x_bom_tool_id.define_aps_bom_lines()

    def select_bom_line(self):
        for rec in self:
            rec.x_line_select = not rec.x_line_select

    def select_aps_bom_line(self):
        for rec in self:
            rec.get_lines_taraz_part_data(not rec.x_aps_line_select)

    def get_lines_taraz_part_data(self, aps_line_select):
        for rec in self:
            rec.x_aps_line_select = aps_line_select
            rec.x_bom_tool_id.update({
                'x_alternate_usage_ids': [(2, line.id) for line in rec.x_bom_tool_id.x_alternate_usage_ids],
                'x_compromised_usage_ids': [(2, line.id) for line in rec.x_bom_tool_id.x_compromised_usage_ids]
            })

            taraz_part_id = rec.x_bom_tool_id.x_aps_bom_line_ids.mapped('x_taraz_part_id')
            line_ids = rec.x_bom_tool_id.x_aps_bom_line_ids.filtered(lambda l: l.x_aps_line_select)
            if len(taraz_part_id) != 1 or not line_ids:
                rec.x_bom_tool_id.update({
                    'x_aps_selected_message': 'Select Unique Taraz Part # to make definitions',
                    'x_aps_selected_ref_des': 'Select Unique Taraz Part # to make definitions',
                    'x_aps_taraz_part_id': False,
                    'x_aps_description': '',
                })
                break

            alternate_usage_ids = []
            for line in taraz_part_id.x_alternate_ids:
                usage = line_ids[0].x_usage_ids.filtered(lambda l: l.x_alternate_id.id == line.id)[0].x_usage
                alternate_usage_ids.append((0, 0, {'x_alternate_id': line.id, 'x_usage': usage}))

            compromised_usage_ids = []
            for line in taraz_part_id.x_compromised_ids:
                usage = line_ids[0].x_usage_ids.filtered(lambda l: l.x_compromised_id.id == line.id)[0].x_usage
                compromised_usage_ids.append((0, 0, {'x_compromised_id': line.id, 'x_usage': usage}))

            rec.x_bom_tool_id.update({
                'x_aps_selected_message': '.',
                'x_aps_selected_ref_des': ', '.join(str(ref_des) for ref_des in line_ids.mapped('x_ref_des')),
                'x_aps_taraz_part_id': taraz_part_id.id,
                'x_aps_description': rec.x_description,
                'x_alternate_usage_ids': alternate_usage_ids,
                'x_compromised_usage_ids': compromised_usage_ids,
            })

    def write(self, vals):
        # Update Old Product
        if vals.get('x_product_id'):
            for rec in self:
                vals['x_old_product_id'] = rec.x_product_id.id
                if rec.x_line_block_id:
                    line_id = rec.x_line_block_id.x_bom_line_ids.filtered(lambda l: l.x_name == rec.x_name
                                                                          and not l.x_product_id)
                    line_id.x_product_id = vals.get('x_product_id')

                product_id = rec.env['product.template'].browse(vals.get('x_product_id'))
                body = (
                    "<p><strong>"
                    + escape(rec.x_base_product_id.name)
                    + ": "
                    + escape(rec.x_ref_des)
                    + "</strong> part # is changed from <strong>"
                    + escape(rec.x_product_id.name)
                    + "</strong> to <strong>"
                    + escape(product_id.name)
                    + "</strong>."
                )
                rec.x_bom_tool_id.send_line_update_email(body)

        # Create, Delete Variant BoM Lines
        if vals.get('x_variant') in ['variant']:
            for rec in self:
                for variant in rec.x_bom_tool_id.x_variant_ids:
                    variant_bom = variant.x_bom_id
                    if not variant_bom.x_bom_line_ids.filtered(lambda l: l.x_ref_des == rec.x_ref_des):
                        variant_bom.x_bom_line_ids = [(0, 0, {
                            'x_name': vals.get('x_name') or rec.x_name,
                            'x_part_description': vals.get('x_part_description') or rec.x_part_description,
                            'x_ref_des': vals.get('x_ref_des') or rec.x_ref_des,
                            'x_old_product_id': vals.get('x_old_product_id') or rec.x_old_product_id.id,
                            'x_product_id': vals.get('x_product_id') or rec.x_product_id.id,

                            'x_quantity': vals.get('x_quantity') or rec.x_quantity,
                            'x_uom_id': vals.get('x_uom_id') or rec.x_uom_id.id,

                            'x_line_block_id': vals.get('x_line_block_id') or rec.x_line_block_id.id,
                            'x_dnp': vals.get('x_dnp') or rec.x_dnp if variant.x_status == 'undefined' else 'dnp',
                            'x_critical': vals.get('x_critical') or rec.x_critical,
                            'x_variant': vals.get('x_variant') or rec.x_variant,
                            'x_notes': vals.get('x_notes') or rec.x_notes,
                        })]
        elif vals.get('x_variant') is not None:
            for rec in self:
                rec.x_bom_tool_id.x_variant_ids.mapped('x_bom_id').mapped('x_bom_line_ids').filtered(
                    lambda l: l.x_ref_des == rec.x_ref_des
                ).unlink()

        return super(BaseBomLines, self).write(vals)

    def unlink(self):
        for rec in self:
            rec.x_usage_ids.unlink()
            self.env['bom.line.rules'].search([('x_line_id', '=', rec._origin.id)]).unlink()
        return super(BaseBomLines, self).unlink()


class ComponentUsage(models.Model):
    _inherit = 'component.usage'

    x_base_bom_line_id = fields.Many2one(comodel_name='base.bom.lines', string='Base BoM Line', required=False)
    x_base_bom_id = fields.Many2one(related="x_base_bom_line_id.x_base_bom_id")
    x_bom_tool_id = fields.Many2one(related="x_base_bom_line_id.x_bom_tool_id")
    x_line_block_id = fields.Many2one(related="x_base_bom_line_id.x_line_block_id")
    x_type = fields.Selection(related="x_base_bom_line_id.x_critical")


class MassComponentUsage(models.Model):
    _inherit = "mass.component.usage"

    x_base_bom_line_id = fields.Many2one(comodel_name='base.bom.lines', string='Base BoM Line', required=False)
    x_base_bom_id = fields.Many2one(related="x_base_bom_line_id.x_base_bom_id")
    x_bom_tool_id = fields.Many2one(related="x_base_bom_line_id.x_bom_tool_id")
    x_line_block_id = fields.Many2one(related="x_base_bom_line_id.x_line_block_id")
    x_type = fields.Selection(related="x_base_bom_line_id.x_critical")
