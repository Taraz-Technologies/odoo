from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    x_bom_tool_id = fields.Many2one(related="product_tmpl_id.x_bom_tool_id")
    x_percentage_investor = fields.Float(string="Investor Share", compute="_compute_percentage", store=True, )
    x_percentage_taraz = fields.Float(string="Taraz Share", compute="_compute_percentage", store=True, )
    x_can_be_manufactured = fields.Float(string='Can be Manufactured', digits='Product Unit of Measure')

    x_bom_tool_line_ids = fields.One2many(comodel_name='bom.tool.lines', inverse_name='x_bom_id',
                                          string='BoM Tool Lines')

    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        for rec in self:
            if rec.product_uom_id.category_id.id != rec.product_tmpl_id.uom_id.category_id.id:
                rec.product_uom_id = rec.product_tmpl_id.uom_id.id
        return res

    @api.depends('bom_line_ids.x_line_cost', 'bom_line_ids.x_investor_product')
    def _compute_percentage(self):
        for rec in self:
            investor_share = sum(rec.bom_line_ids.filtered(lambda l: l.x_investor_product).mapped('x_line_cost'))
            taraz_share = sum(rec.bom_line_ids.filtered(lambda l: not l.x_investor_product).mapped('x_line_cost'))
            total_cost = sum(rec.bom_line_ids.mapped('x_line_cost'))

            rec.x_percentage_investor = investor_share / total_cost if total_cost != 0 else 0
            rec.x_percentage_taraz = taraz_share / total_cost if total_cost != 0 else 0

    def compute_bom_lines(self):
        for rec in self:
            if not rec.x_bom_tool_id:
                raise UserError("BoM Tool of '%s' is not defined!" % rec.product_tmpl_id.name)
            elif rec.x_bom_tool_id.state != 'active':
                raise UserError("BoM Tool of '%s' is not active!" % rec.product_tmpl_id.name)

            variant_id = self.env['product.variant'].search([
                ('x_product_id', '=', rec.product_tmpl_id.id)
            ], limit=1, order="id desc")
            if variant_id:
                if variant_id.x_status != 'defined':
                    raise UserError("Variant BoM status of '%s' is 'Undefined'!" % rec.product_tmpl_id.name)
                variant = 'variant'
                input_bom_id = variant_id.x_bom_id
            elif rec.product_tmpl_id.id == rec.x_bom_tool_id.x_base_product_id.id:
                variant = False
                input_bom_id = rec.x_bom_tool_id.x_base_bom_id
            else:
                raise UserError("Input BoM of '%s' not found!" % rec.product_tmpl_id.name)

            input_bom_line_ids = input_bom_id.x_bom_line_ids.filtered(
                lambda l: not l.x_dnp and l.x_variant == variant and not l.x_move_to_tool_id
                and not l.x_design_deleted and not l.x_deleted and l.x_product_id
            )

            bom_tool_line_ids = []
            line_ids = rec.x_bom_tool_id.x_base_bom_id.mapped('x_bom_line_ids')
            for line in input_bom_line_ids:
                base_line_id = line if not variant else line_ids.filtered(lambda l: l.x_ref_des == line.x_ref_des)
                rule_line_id = self.env['bom.line.rules.lines'].search([('x_line_id', 'in', base_line_id.ids)], limit=1)
                bom_tool_line_ids.append((0, 0, {
                    'x_line_id': line.id,
                    'x_base_line_id': base_line_id.ids[0] if len(base_line_id.ids) > 1 else base_line_id.id,
                    'x_quantity': line.x_real_quantity * rec.product_qty,
                    'x_replacement_rule_line_id': rule_line_id.id,
                }))
            rec.x_bom_tool_line_ids = [(2, line.id) for line in rec.x_bom_tool_line_ids]
            rec.x_bom_tool_line_ids = bom_tool_line_ids

            bom_line_ids = []
            can_be_manufactured = rec.product_qty
            sequence = 0
            for product in input_bom_line_ids.mapped('x_product_id'):
                line_ids = input_bom_line_ids.filtered(lambda l: l.x_product_id.id == product.id)
                operation_id = line_ids[0].x_operation_id.id if line_ids[0].x_operation_id else False
                investor_product = True if any(x for x in line_ids.mapped('x_investor_product')) else False
                ref_des = ', '.join(str(ref_des) for ref_des in line_ids.mapped('x_ref_des'))
                product_id = product.product_variant_ids.id

                quantity = sum(line_ids.mapped('x_real_quantity')) * rec.product_qty
                original_available = product.product_variant_ids.free_qty
                # Original Part Full Quantity
                if original_available >= quantity:
                    bom_line_ids.append((0, 0, {
                        'sequence': sequence,
                        'x_ref_des': ref_des,
                        'x_product_id': product_id,
                        'product_id': product_id,
                        'product_qty': quantity,
                        'x_investor_product': investor_product,
                        'operation_id': operation_id,
                    }))
                    sequence += 1
                    quantity = 0
                    continue
                # Alternate Part Full Quantity
                if quantity != 0:
                    alt_ids = line_ids[0].x_usage_ids.filtered(lambda l: l.x_usage == 'auto_use').mapped('x_alternate_id')
                    alt_ids = alt_ids.filtered(lambda l: l.x_product_id.id != product.id)
                    for line in alt_ids.filtered(lambda l: l.x_product_id.product_variant_ids.free_qty >= quantity):
                        available = line.x_product_id.product_variant_ids.free_qty
                        bom_line_ids.append((0, 0, {
                            'sequence': sequence,
                            'x_ref_des': ref_des,
                            'x_product_id': product_id,
                            'product_id': line.x_product_id.product_variant_ids.id,
                            'product_qty': quantity if quantity <= available else available,
                            'x_investor_product': investor_product,
                            'operation_id': operation_id,
                        }))
                        sequence += 1
                        quantity = 0
                        break
                    if quantity == 0:
                        continue
                # Compromised Part Full Quantity
                if quantity != 0:
                    comp_ids = line_ids[0].x_usage_ids.filtered(lambda l: l.x_usage == 'auto_use')
                    comp_ids = comp_ids.mapped('x_compromised_id').mapped('x_compromised_id').mapped('x_alternate_ids')
                    for line in comp_ids.filtered(lambda l: l.x_product_id.product_variant_ids.free_qty >= quantity):
                        available = line.x_product_id.product_variant_ids.free_qty
                        bom_line_ids.append((0, 0, {
                            'sequence': sequence,
                            'x_ref_des': ref_des,
                            'x_product_id': product_id,
                            'product_id': line.x_product_id.product_variant_ids.id,
                            'product_qty': quantity if quantity <= available else available,
                            'x_investor_product': investor_product,
                            'operation_id': operation_id,
                        }))
                        sequence += 1
                        quantity = 0
                        break
                    if quantity == 0:
                        continue
                # Alternate Part Partial Quantity
                if quantity != 0:
                    alt_ids = line_ids[0].x_usage_ids.filtered(lambda l: l.x_usage == 'auto_use').mapped('x_alternate_id')
                    alt_ids = alt_ids.filtered(lambda l: l.x_product_id.id != product.id)
                    for line in alt_ids.filtered(lambda l: l.x_product_id.product_variant_ids.free_qty > 0):
                        available = line.x_product_id.product_variant_ids.free_qty
                        bom_line_ids.append((0, 0, {
                            'sequence': sequence,
                            'x_ref_des': ref_des,
                            'x_product_id': product_id,
                            'product_id': line.x_product_id.product_variant_ids.id,
                            'product_qty': quantity if quantity <= available else available,
                            'x_investor_product': investor_product,
                            'operation_id': operation_id,
                        }))
                        sequence += 1
                        quantity = 0 if quantity <= available else quantity - available
                        if quantity == 0:
                            break
                    if quantity == 0:
                        continue
                # Compromised Part Partial Quantity
                if quantity != 0:
                    comp_ids = line_ids[0].x_usage_ids.filtered(lambda l: l.x_usage == 'auto_use')
                    comp_ids = comp_ids.mapped('x_compromised_id').mapped('x_compromised_id').mapped('x_alternate_ids')
                    for line in comp_ids.filtered(lambda l: l.x_product_id.product_variant_ids.free_qty > 0):
                        available = line.x_product_id.product_variant_ids.free_qty
                        bom_line_ids.append((0, 0, {
                            'sequence': sequence,
                            'x_ref_des': ref_des,
                            'x_product_id': product_id,
                            'product_id': line.x_product_id.product_variant_ids.id,
                            'product_qty': quantity if quantity <= available else available,
                            'x_investor_product': investor_product,
                            'operation_id': operation_id,
                        }))
                        sequence += 1
                        quantity = 0 if quantity <= available else quantity - available
                        if quantity == 0:
                            break
                    if quantity == 0:
                        continue
                # Remaining Quantity of Original Part
                if quantity != 0:
                    bom_line_ids.append((0, 0, {
                        'sequence': sequence,
                        'x_ref_des': ref_des,
                        'x_product_id': product_id,
                        'product_id': product_id,
                        'product_qty': quantity,
                        'x_investor_product': investor_product,
                        'operation_id': operation_id,
                    }))
                    sequence += 1
                    quantity = 0 if quantity <= original_available else quantity - original_available

                if quantity > 0:
                    line_qty = sum(line_ids.mapped('x_real_quantity')) * rec.product_qty
                    if can_be_manufactured > math.floor((line_qty - quantity) / len(line_ids)):
                        can_be_manufactured = math.floor((line_qty - quantity) / len(line_ids))

            rec.bom_line_ids = [(2, line.id) for line in rec.bom_line_ids]
            rec.bom_line_ids = bom_line_ids
            rec.x_can_be_manufactured = can_be_manufactured
            rec.x_bom_tool_id.state = 'active'

    def apply_automation_rules(self):
        for rec in self:
            for line in rec.x_bom_tool_line_ids.filtered(lambda l: l.x_replacement_rule_line_id.x_master_line):
                master_line_id = rec.bom_line_ids.filtered(
                    lambda l: line.x_ref_des in l.x_ref_des and l.product_id.id != line.x_product_id.id
                )

                replacement_rule_id = line.x_replacement_rule_id
                replacement_rule_line_id = line.x_replacement_rule_line_id
                if replacement_rule_line_id.x_config_product_id_1.id:
                    if master_line_id.product_id.product_tmpl_id.id == replacement_rule_line_id.x_config_product_id_1.id:
                        for rule_line in replacement_rule_id.x_rule_line_ids:
                            child_line_id = rec.bom_line_ids.filtered(
                                lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                            child_line_id.product_id = rule_line.x_config_product_id_1.product_variant_id.id
                            child_line_id.onchange_product_uom_id()
                            child_line_id.onchange_product_id()
                if replacement_rule_line_id.x_config_product_id_2.id:
                    if master_line_id.product_id.product_tmpl_id.id == replacement_rule_line_id.x_config_product_id_2.id:
                        for rule_line in replacement_rule_id.x_rule_line_ids:
                            child_line_id = rec.bom_line_ids.filtered(
                                lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                            child_line_id.product_id = rule_line.x_config_product_id_2.product_variant_id.id
                            child_line_id.onchange_product_uom_id()
                            child_line_id.onchange_product_id()
                if replacement_rule_line_id.x_config_product_id_3.id:
                    if master_line_id.product_id.product_tmpl_id.id == replacement_rule_line_id.x_config_product_id_3.id:
                        for rule_line in replacement_rule_id.x_rule_line_ids:
                            child_line_id = rec.bom_line_ids.filtered(
                                lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                            child_line_id.product_id = rule_line.x_config_product_id_3.product_variant_id.id
                            child_line_id.onchange_product_uom_id()
                            child_line_id.onchange_product_id()
                if replacement_rule_line_id.x_config_product_id_4.id:
                    if master_line_id.product_id.product_tmpl_id.id == replacement_rule_line_id.x_config_product_id_4.id:
                        for rule_line in replacement_rule_id.x_rule_line_ids:
                            child_line_id = rec.bom_line_ids.filtered(
                                lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                            child_line_id.product_id = rule_line.x_config_product_id_4.product_variant_id.id
                            child_line_id.onchange_product_uom_id()
                            child_line_id.onchange_product_id()
                if replacement_rule_line_id.x_config_product_id_5.id:
                    if master_line_id.product_id.product_tmpl_id.id == replacement_rule_line_id.x_config_product_id_5.id:
                        for rule_line in replacement_rule_id.x_rule_line_ids:
                            child_line_id = rec.bom_line_ids.filtered(
                                lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                            child_line_id.product_id = rule_line.x_config_product_id_5.product_variant_id.id
                            child_line_id.onchange_product_uom_id()
                            child_line_id.onchange_product_id()
                else:
                    for rule_line in replacement_rule_id.x_rule_line_ids:
                        child_line_id = rec.bom_line_ids.filtered(
                            lambda l: rule_line.x_line_id.x_ref_des in l.x_ref_des)
                        child_line_id.product_id = rule_line.x_line_id.x_product_id.product_variant_id.id
                        child_line_id.onchange_product_uom_id()
                        child_line_id.onchange_product_id()


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    x_line_cost = fields.Float(string="Cost", compute="_compute_subtotal_cost", store=True)

    x_ref_des = fields.Char(string='RefDes')

    x_product_id = fields.Many2one(comodel_name='product.product')
    x_taraz_part_number_id = fields.Many2one(related="x_product_id.x_taraz_part_number_id")
    x_alternate_ids = fields.Many2many(comodel_name="product.product", string="Alternates",
                                       relation="product_product_mrp_bom_line_rel_1",
                                       column1="product_product_id", column2="mrp_bom_line_id",
                                       compute="_compute_data", store=True)
    x_compromise_ids = fields.Many2many(comodel_name="product.product", string="Compromised",
                                        relation="product_product_mrp_bom_line_rel_2",
                                        column1="product_product_id", column2="mrp_bom_line_id",
                                        compute="_compute_data", store=True)
    x_product_ids = fields.Many2many(comodel_name="product.product", string="Related Products",
                                     relation="product_product_mrp_bom_line_rel_3",
                                     column1="product_product_id", column2="mrp_bom_line_id",
                                     compute="_compute_data", store=True)

    x_mounting_type = fields.Selection(related="x_taraz_part_number_id.x_mounting_type", readonly=False, store=True)
    x_original_product_id = fields.Many2one(comodel_name='product.product', string='BoM Tool Part',
                                            compute="_compute_data", store=True, readonly=False)
    x_taraz_part_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part #',
                                      compute="_compute_data", store=True, readonly=False)

    x_free_qty = fields.Float(related="product_id.free_qty")
    x_uom_id = fields.Many2one(related="product_id.uom_id")
    x_part_status = fields.Selection(selection=[
        ('short', 'Short'), ('alt', 'Alternate'), ('comp', 'Compromised'), ('waiting', 'Waiting Another Move'),
        ('partially_available', 'Partially Available'), ('assigned', 'Available'), ('done', 'Done'),
    ], string='Status', compute="_compute_line_status", store=True)

    def write(self, vals):
        if vals.get('product_qty') is not None and round(vals.get('product_qty'), 4) != self.product_qty:
            if self.x_part_status in ('assigned', 'done') and self.product_qty != 0:
                raise UserError("Cannot update BoM Line quantity once it's stock is available i.e. picking is done!")
        return super(MrpBomLine, self).write(vals)

    @api.constrains('bom_id', 'product_id')
    def product_id_constrains(self):
        for rec in self:
            if rec.env['mrp.production'].search([
                ('bom_id', 'in', rec.bom_id.ids), ('state', 'not in', ('draft', 'done', 'cancel'))
            ], limit=1):
                duplicate_lines_ids = len(
                    rec.bom_id.bom_line_ids.filtered(
                        lambda l: l.product_id.id == rec.product_id.id
                        and l.x_part_status not in ('assigned', 'done')
                        and l.product_qty != 0
                    )
                )
                if duplicate_lines_ids > 1:
                    raise UserError(
                        'You cannot create duplicate BoM lines!'
                        '\n'
                        'You can update existing BoM Line quantity.'
                    )

    @api.depends('product_id', 'product_qty')
    def _compute_line_status(self):
        for rec in self:
            if rec.x_part_status in ('waiting', 'partially_available', 'assigned', 'done'):
                break
            elif rec.x_free_qty < rec.product_qty:
                rec.x_part_status = 'short'
            elif rec.product_id.id == rec.x_original_product_id.id:
                rec.x_part_status = False
            elif rec.product_id.id in rec.x_alternate_ids.ids:
                rec.x_part_status = 'alt'
            elif rec.product_id.id in rec.x_compromise_ids.ids:
                rec.x_part_status = 'comp'

    @api.depends('product_qty', 'product_id.x_average_price')
    def _compute_subtotal_cost(self):
        for rec in self:
            rec.x_line_cost = rec.product_qty * rec.product_id.x_average_price

    @api.depends('x_product_id', 'x_taraz_part_number_id.x_alternate_ids', 'x_taraz_part_number_id.x_compromised_ids')
    def _compute_data(self):
        for rec in self:
            rec.x_original_product_id = rec.x_product_id.id
            rec.x_taraz_part_id = rec.x_taraz_part_number_id.id
            rec.x_alternate_ids = rec.x_taraz_part_number_id.x_alternate_ids.mapped('x_product_id').mapped(
                'product_variant_ids').ids
            rec.x_compromise_ids = rec.x_taraz_part_number_id.x_compromised_ids.mapped('x_compromised_id').mapped(
                'x_alternate_ids').mapped('x_product_id').mapped('product_variant_ids').ids
            rec.x_product_ids = rec.x_alternate_ids.ids + rec.x_compromise_ids.ids

    def action_duplicate_bom_line(self):
        for rec in self:
            product_id = rec.x_product_ids.filtered(
                lambda l: l.id not in rec.bom_id.bom_line_ids.mapped('product_id').ids
            )
            if product_id:
                rec.copy({'product_id': product_id[0].id})
            elif rec.x_part_status in ('assigned', 'done'):
                rec.copy()
            else:
                raise UserError(
                    "Cannot create duplicate line"
                    "\nAlternates & Compromised are not defined or already in use.")

    def unlink(self):
        manufacturing_ids = self.env['mrp.production'].search([
            ('bom_id', 'in', self.bom_id.ids), ('state', 'not in', ('draft', 'done', 'cancel'))
        ])
        if manufacturing_ids:
            raise UserError(_(
                'You can not delete a BoM Line with running manufacturing orders.'
                '\n%s'
                '\nPlease close or cancel it first.'
                % ', '.join(manufacturing_ids.mapped('name'))
            ))
        return super(MrpBomLine, self).unlink()
