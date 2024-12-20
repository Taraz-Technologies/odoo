from odoo import fields, models


class BomToolLines(models.Model):
    _name = "bom.tool.lines"
    _description = "Bom Tool Lines"
    _rec_name = "x_line_id"

    x_bom_id = fields.Many2one(comodel_name='mrp.bom', string='BoM', required=False)
    x_line_id = fields.Many2one(comodel_name='base.bom.lines', string='Tool Line', required=False)
    x_base_line_id = fields.Many2one(comodel_name='base.bom.lines', string='Base Line', required=False)
    x_ref_des = fields.Char(related="x_line_id.x_ref_des")
    x_product_tmpl_id = fields.Many2one(related="x_line_id.x_product_id")
    x_product_id = fields.Many2one(related="x_line_id.x_product_id.product_variant_id")
    x_quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    x_uom_id = fields.Many2one(related="x_line_id.x_product_id.uom_id")
    x_description = fields.Text(related="x_line_id.x_product_id.description")
    x_notes = fields.Char(related="x_line_id.x_notes")

    x_replacement_rule_line_id = fields.Many2one(comodel_name='bom.line.rules.lines', string='Rule Line')
    x_master_line = fields.Boolean(related="x_replacement_rule_line_id.x_master_line")
    x_replacement_rule_id = fields.Many2one(related="x_replacement_rule_line_id.x_bom_line_rule_id", string="Rule")




