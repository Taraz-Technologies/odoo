from odoo import fields, models, api
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_custom_tag_ids = fields.Many2many(
        comodel_name='custom.tags', relation='custom_tags_stock_move_rel_1',
        column1='stock_move_id', column2='custom_tag_id', string="Tags", compute="_compute_tag_ids", store=True,
    )
    x_notes = fields.Text(related='picking_id.note')

    # def write(self, vals):
    #     for record in self:
    #         old_values = record.x_custom_tag_ids.ids
    #     res = super(StockMove, self).write(vals)
    #     for record in self:
    #         if 'x_custom_tag_ids' in vals:
    #             self.x_custom_tag_ids._track_many2many_changes(
    #                 record, 'x_custom_tag_ids', old_values=old_values, new_values=vals['x_custom_tag_ids']
    #             )
    #     return res

    @api.depends('picking_id', 'picking_id.x_tag_ids')
    def _compute_tag_ids(self):
        for rec in self:
            rec.x_custom_tag_ids = [(6, 0, rec.picking_id.x_tag_ids.ids)]


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_location_ids = fields.Many2many(comodel_name='stock.location', string='Recommended Locations',
                                      relation="stock_location_stock_move_line_rel_1",
                                      column1="stock_location_id", column2="stock_move_line_id",
                                      compute="_compute_recommended_locations", store=True)

    x_source_manufacturing_id = fields.Many2one(
        comodel_name="mrp.production", string="Source Manufacturing Order",
        compute="_compute_source_manufacturing_id", store=True
    )

    @api.depends('move_id.origin', 'reference')
    def _compute_source_manufacturing_id(self):
        for rec in self:
            rec.x_source_manufacturing_id = self.env['mrp.production'].search([
                '|', ('name', '=', rec.move_id.origin), ('name', '=', rec.reference)
            ], limit=1).id

    @api.depends('product_id', 'picking_id.x_show_recommended_locations')
    def _compute_recommended_locations(self):
        for rec in self:
            quant_location_ids = False
            if rec.picking_id.x_show_recommended_locations:
                domain_quant_loc, domain_move_in_loc, domain_move_out_loc = rec.product_id._get_domain_locations()
                domain_quant = [('product_id', '=', rec.product_id.id)] + domain_quant_loc
                quant_location_ids = self.env['stock.quant'].search(domain_quant).mapped('location_id').ids
                if not quant_location_ids and rec.product_id.dk_category and rec.product_id.dk_category:
                    quant_location_ids = self.env['stock.location'].search([
                        ('x_product_type_id', '=', rec.product_id.dk_category.id),
                        ('x_product_sub_type_id', '=', rec.product_id.dk_sub_category.id),
                    ]).ids
                elif not quant_location_ids and rec.product_id.dk_category and not rec.product_id.dk_category:
                    quant_location_ids = self.env['stock.location'].search([
                        ('x_product_type_id', '=', rec.product_id.dk_category.id),
                    ]).ids
                elif not quant_location_ids and not rec.product_id.dk_category and rec.product_id.dk_category:
                    quant_location_ids = self.env['stock.location'].search([
                        ('x_product_sub_type_id', '=', rec.product_id.dk_sub_category.id),
                    ]).ids
            rec.x_location_ids = quant_location_ids


