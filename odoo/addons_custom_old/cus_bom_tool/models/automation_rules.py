from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class BomLineRules(models.Model):
    _name = "bom.line.rules"
    _description = "BoM Line Rule"
    _rec_name = "x_line_id"

    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_line_ids = fields.One2many(related="x_bom_tool_id.x_base_bom_id.x_bom_line_ids")

    x_line_id = fields.Many2one('base.bom.lines', 'Master Line', domain="[('id', 'in', x_line_ids)]", required=True)
    x_line_block_id = fields.Many2one(related="x_line_id.x_line_block_id")

    x_rule_line_ids = fields.One2many('bom.line.rules.lines', 'x_bom_line_rule_id', string='Rule Lines')

    @api.onchange('x_line_id')
    def get_rule_lines(self):
        for rec in self:
            rec.x_rule_line_ids.unlink()
            if rec.x_line_id and rec.x_line_block_id:
                line_ids = rec.x_bom_tool_id.x_base_bom_id.x_bom_line_ids
                line_ids = line_ids.filtered(lambda l: l.x_line_block_id.id == rec.x_line_block_id.id)

                ref_des = rec.x_line_id.x_ref_des
                block_number = ref_des.split('_')[1] if len(ref_des.split('_')) > 1 else 0
                if block_number != 0:
                    line_ids = line_ids.filtered(lambda l: '_%s' % block_number in l.x_ref_des)

                rule_line_ids = []
                for line in line_ids:
                    if rec.x_line_id.id == line.id:
                        rule_line_ids.append((0, 0, {'x_master_line': True, 'x_line_id': line.id}))
                    else:
                        rule_line_ids.append((0, 0, {'x_line_id': line.id}))
                rec.x_rule_line_ids = rule_line_ids
            elif rec.x_line_id:
                rec.x_rule_line_ids = [(0, 0, {'x_master_line': True, 'x_line_id': rec.x_line_id.id})]

    def unlink(self):
        for rec in self:
            rec.x_rule_line_ids.unlink()
        return super(BomLineRules, self).unlink()


class BomLineRulesLines(models.Model):
    _name = "bom.line.rules.lines"
    _description = "BoM Line Rule Lines"
    _rec_name = 'x_line_id'

    x_bom_line_rule_id = fields.Many2one(comodel_name='bom.line.rules', string='BoM Line Rule', required=False)
    x_line_ids = fields.One2many(related="x_bom_line_rule_id.x_bom_tool_id.x_base_bom_id.x_bom_line_ids")

    x_master_line = fields.Boolean(string='Master', required=False)

    x_line_id = fields.Many2one('base.bom.lines', 'BoM Line', domain="[('id', 'in', x_line_ids)]", required=True)
    x_config_product_id_1 = fields.Many2one(comodel_name='product.template', string='Configuration 1')
    x_config_product_id_2 = fields.Many2one(comodel_name='product.template', string='Configuration 2')
    x_config_product_id_3 = fields.Many2one(comodel_name='product.template', string='Configuration 3')
    x_config_product_id_4 = fields.Many2one(comodel_name='product.template', string='Configuration 4')
    x_config_product_id_5 = fields.Many2one(comodel_name='product.template', string='Configuration 5')