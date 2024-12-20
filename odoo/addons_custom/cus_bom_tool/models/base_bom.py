from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class BaseBom(models.Model):
    _name = "base.bom"
    _description = "Input BoMs"
    _rec_name = 'display_name'

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True)

    x_name = fields.Char(string='BoM Version', required=False)
    x_bom_tool_id = fields.Many2one(comodel_name='bom.tool', string='BoM Tool', required=False)
    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_bom_file = fields.Binary(string="BoM File (.csv)")
    x_pnp_file = fields.Binary(string="PNP File (.csv)")
    x_bom_comment = fields.Text(string="Comment", required=False, tracking=True)

    x_bom_line_ids = fields.One2many(comodel_name='base.bom.lines', inverse_name='x_base_bom_id', string='BoM Lines')
    x_routing_id = fields.Many2one(
        comodel_name='mrp.routing', string='Routing', check_company=True, tracking=True, company_dependent=True,
        domain=lambda self: [('company_id', '=', self.env.company.id)],
        help="The operations for producing this BoM.  When a routing is specified, the production orders will "
             " be executed through work orders, otherwise everything is processed in the production order itself. ")

    @api.onchange('x_routing_id')
    def onchange_routing_id(self):
        for rec in self:
            for line in rec.x_bom_line_ids:
                operation_id = rec.x_routing_id.operation_ids.filtered(
                    lambda o:  o.workcenter_id.x_mounting_type and o.workcenter_id.x_mounting_type == line.x_type
                )
                line.x_operation_id = operation_id[0].id if operation_id else False

    @api.depends('x_name', 'x_product_id.name', 'write_date')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s: %s' % (rec.x_name, rec.x_product_id.name)

    def unlink(self):
        self.x_bom_line_ids.unlink()
        return super(BaseBom, self).unlink()




