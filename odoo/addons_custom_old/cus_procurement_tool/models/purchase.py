from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.misc import formatLang
import logging

_logger = logging.getLogger("*__addons_custom__*")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_internal_ref = fields.Char(string='Internal Reference', required=False)
    x_demand_list_ids = fields.Many2many(comodel_name='component.list.demand.details', string='Demand Details')
    x_proc_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='Proc. Cycle', required=False)

    x_show_hs_code = fields.Boolean(string='Show HS Code', required=False)
    x_show_coo = fields.Boolean(string='Show COO', required=False)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        super(PurchaseOrder, self)._name_search(name)
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('x_internal_ref', operator, name), ('partner_ref', operator, name)]
        purchase_order_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(purchase_order_ids).with_user(name_get_uid))

    @api.depends('name', 'partner_ref', 'x_internal_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            if po.x_internal_ref:
                name += ' (' + po.x_internal_ref + ')'
            if po.partner_ref:
                name += ' (' + po.partner_ref + ')'
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
            result.append((po.id, name))
        return result
