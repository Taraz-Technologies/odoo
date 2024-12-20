from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class BomBlocks(models.Model):
    _name = 'bom.blocks'
    _description = "BoM Blocks"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)

    x_name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                         default=lambda self: _('New'))
    x_description = fields.Char(string='Description', required=False, tracking=True)
    x_variant = fields.Boolean(string='Variant Block?', required=False, tracking=True)
    x_block_file = fields.Binary(string="Attach File", )

    x_comment = fields.Text(string="Comment", required=False, tracking=True)

    x_bom_line_ids = fields.One2many(comodel_name='block.bom.lines', inverse_name='x_block_id', string='BoM Lines')

    x_bom_tool_ids = fields.Many2many(comodel_name='bom.tool', string='Used in BoMs')

    @api.model
    def create(self, vals):
        if vals.get('x_name', _('New')) == _('New'):
            vals['x_name'] = self.env['ir.sequence'].next_by_code('bom.blocks') or 'New'
        return super(BomBlocks, self).create(vals)

    @api.depends('x_name', 'x_description')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s (%s)' % (rec.x_name, rec.x_description)

    def unlink(self):
        for rec in self:
            rec.x_bom_line_ids.unlink()
        return super(BomBlocks, self).unlink()


class BlockBomLines(models.Model):
    _name = "block.bom.lines"
    _description = "Block BoM Lines"
    _rec_name = "x_product_id"
    _order = "x_product_id"

    x_block_id = fields.Many2one(comodel_name='bom.blocks', string='Block', required=False)

    image_128 = fields.Image(related='x_product_id.image_128', string="Image")

    x_name = fields.Char(string='Part # (Design)', readonly=True)
    x_part_description = fields.Char(string='Description (Design)', readonly=True)

    x_taraz_part_id = fields.Many2one(related="x_product_id.x_taraz_part_number_id", store=True)
    x_product_id = fields.Many2one(comodel_name='product.template', string='Part #', required=False)
    x_description = fields.Text(string="Description", related="x_product_id.description")

    x_real_quantity = fields.Float(string='Real Quantity', compute="_compute_real_quantity", store=True)
    x_quantity = fields.Float(string='Quantity', required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM')

    x_type = fields.Selection(selection=[('smd', 'SMD'), ('th', 'TH'), ('other', 'OTHER')], string='Mounting Type')
    x_station_id = fields.Many2one(comodel_name='bom.line.station', string='Station')
    x_notes = fields.Char(string='Notes')

    @api.onchange('x_product_id')
    def update_uom_id(self):
        for rec in self:
            rec.x_uom_id = rec.x_product_id.uom_id.id

    @api.depends('x_product_id', 'x_quantity', 'x_uom_id')
    def _compute_real_quantity(self):
        for rec in self:
            if rec.x_product_id.uom_id and rec.x_uom_id:
                rec.x_real_quantity = rec.x_uom_id._compute_quantity(rec.x_quantity, rec.x_product_id.uom_id, rounding_method='HALF-UP')



