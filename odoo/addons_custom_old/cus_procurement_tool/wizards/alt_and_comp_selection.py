from odoo import api, models, fields


class AltCompSelection(models.TransientModel):
    _name = 'alt.comp.selection'
    _description = 'Alt & Comp Selection'

    # x_proc_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='Procurement Cycle', required=False)
    # x_component_id = fields.Many2one(comodel_name='component.list', string='Component', required=False)
    # x_product_id = fields.Many2one(comodel_name='product.product', string='Component', readonly=True)
    # x_missing_qty = fields.Float(string='Missing', readonly=True, store=True)
    # x_alternate_ids = fields.Many2many('alt.comp.selection.alternates', string='Alternates',)
    # x_compromised_ids = fields.Many2many('alt.comp.selection.compromised', string='Compromised',)




