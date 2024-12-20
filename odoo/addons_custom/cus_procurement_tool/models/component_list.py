from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")

import datetime
import math


class ComponentList(models.Model):
    _name = "component.list"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Component List"
    _rec_name = "x_product_id"
    _order = "x_product_id"

    x_proc_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='Procurement Cycle')

    image_128 = fields.Image(related='x_product_id.image_128', string='Image')
    x_product_id = fields.Many2one(comodel_name='product.product', string='Component', required=False)
    x_taraz_part_id = fields.Many2one(related="x_product_id.x_taraz_part_number_id", store=True)
    x_consider_compromised = fields.Boolean(related="x_taraz_part_id.x_consider_compromised", readonly=False,
                                            store=True, tracking=True)
    x_categ_id = fields.Many2one(related="x_product_id.categ_id", store=True)
    x_remaining_days = fields.Integer(string='Criticality (Days)', compute="compute_remaining_days", store=True,
                                      tracking=True)

    x_description = fields.Text(related="x_product_id.description")

    x_alternate_ids = fields.One2many(related="x_taraz_part_id.x_alternate_ids")
    x_compromised_ids = fields.One2many(related="x_taraz_part_id.x_compromised_ids")

    x_uom_id = fields.Many2one(related="x_product_id.uom_id")
    x_mounting_type = fields.Selection(related="x_product_id.x_mounting_type", store=True, readonly=False,
                                       tracking=True)
    x_country_id = fields.Many2one(related='x_product_id.x_country_id', store=True, readonly=False, tracking=True)

    x_required_qty = fields.Float(string='Required', digits="Product Unit of Measure", tracking=True)
    x_missing_qty = fields.Float(string='Missing', digits="Product Unit of Measure", tracking=True)
    x_incoming_qty = fields.Float(
        string='Incoming (Actual)', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')

    x_qty_available = fields.Float(
        string='Actual Forecasted', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')

    @api.depends('x_product_id.stock_move_ids.product_qty', 'x_product_id.stock_move_ids.state')
    @api.depends_context('company_owned', 'force_company')
    def _compute_custom_quantities(self):
        for rec in self:
            rec.x_incoming_qty = rec.x_product_id.with_context(
                force_company=rec.x_proc_cycle_id.x_company_id.id
            ).x_incoming_qty
            rec.x_qty_available = rec.x_product_id.with_context(
                force_company=rec.x_proc_cycle_id.x_company_id.id
            ).virtual_available

    x_safety_stock = fields.Float(related="x_taraz_part_id.x_safety_stock", string='Safety Stock', tracking=True)
    x_reorder_point = fields.Float(related="x_taraz_part_id.x_reorder_point", string='Reorder Point', tracking=True,
                                   help="Safety Stock + Procurement Duration Stock")

    x_moq = fields.Float(string='MOQ', digits="Product Unit of Measure", required=False, tracking=True,
                         help="Minimum Order Quantity (Missing Quantity)")
    x_roq = fields.Float(string='ROQ', digits="Product Unit of Measure", required=False, tracking=True,
                         help="Reorder Quantity (Missing Quantity + Reorder Point)")
    x_broq = fields.Float(string='BROQ', digits="Product Unit of Measure", required=False, tracking=True,
                          help="Bulk Reorder Quantity (Missing Quantity + Bulk Reorder Point)")

    x_default_qty = fields.Selection(selection=[
        ('rp', 'Reorder Point'),
        ('moq', 'MOQ'),
        ('roq', 'ROQ'),
        ('broq', 'BROQ'),
        ('manual', 'Manual'),
    ], string='Default Qty', default='roq', required=False, tracking=True)

    x_manual_qty = fields.Float(string='Manual Qty', digits="Product Unit of Measure", required=False, tracking=True)

    x_vendor_type = fields.Selection(selection=[
        ('preferred', 'Preferred Vendors'),
        ('all', 'All Vendors'),
    ], string='Vendor Type', default='preferred', required=False, tracking=True)

    x_comment = fields.Text(string="Comment", required=False)

    x_status = fields.Selection(selection=[
        ('draft', 'New Line'),
        ('review', 'Reviewed'),
        ('urgent', 'Urgent'),
        ('ignore', 'Ignore'),
        ('new_demand', 'Updated Line'),
        ('source_alternate', 'Source Alternate'),
        ('cart_defined', 'Cart Defined'),
        ('cart_partially_defined', 'Cart Partially Defined'),
        ('cart_on_hold', 'Cart On Hold'),
        ('cart_updated', 'Cart Updated'),
        ('cart_ordered', 'Cart Ordered'),
        ('cart_partially_ordered', 'Cart Partially Ordered'),
        ('shipped', 'Shipped'),
        ('partially_shipped', 'Partially Shipped'),
        ('received', 'Received'),
    ], string='Status', default="draft", tracking=True)

    x_mergeable_lines = fields.Char(string='Mergeable Lines', compute="compute_mergeable_lines", store=True)
    x_mergeable_line_warning = fields.Char(string='Mergeable Lines Warning', compute="compute_mergeable_lines",
                                           store=True)

    x_quantities_ids = fields.One2many(
        comodel_name='component.list.quantities',
        inverse_name='x_component_id',
        string='Component Quantities',
        required=False)

    x_cart_ids = fields.Many2many(
        comodel_name='procurement.cycle.cart.details',
        string='Carts',
        compute="compute_cart_ids",
        store=True,
        readonly=False)

    x_budget_ids = fields.Many2many(
        comodel_name='procurement.cycle.budget.details',
        string='Budgets',
        compute="compute_budget_ids",
        store=True,
        readonly=False)

    x_demand_detail_ids = fields.One2many(
        comodel_name='component.list.demand.details',
        inverse_name='x_component_id',
        string='Demand Details',
        required=False)

    x_purchase_history_ids = fields.One2many(
        comodel_name='component.list.purchase.history',
        inverse_name='x_component_id',
        string='Purchase History',
        required=False)

    x_quarterly_consumption_ids = fields.Many2many(
        comodel_name='quarterly.consumption',
        string='Quarterly Consumption')

    x_consumption_ids = fields.One2many(
        comodel_name='component.list.consumption',
        inverse_name='x_component_id',
        string='Consumption Details',
        required=False)

    x_sale_ids = fields.Many2many(comodel_name='sale.order', string='Sale Orders')
    x_compute_sale_ids = fields.Boolean(compute="compute_sale_ids")

    @api.depends('x_demand_detail_ids', 'x_demand_detail_ids.x_sale_id')
    def compute_sale_ids(self):
        for rec in self:
            rec.x_sale_ids = [(6, 0, rec.x_demand_detail_ids.mapped('x_sale_id').ids)]
            rec.x_compute_sale_ids = True

    @api.depends('x_product_id', 'x_taraz_part_id')
    def compute_mergeable_lines(self):
        for rec in self:
            mergeable_lines_ids = rec.x_proc_cycle_id.x_short_component_ids.filtered(
                lambda l: l.x_product_id.product_tmpl_id.id in rec.x_taraz_part_id.x_alternate_ids.mapped(
                    'x_product_id').ids
                          or rec.x_product_id.product_tmpl_id.id in l.x_taraz_part_id.x_alternate_ids.mapped(
                    'x_product_id').ids
                          or l.x_taraz_part_id.id in rec.x_taraz_part_id.x_compromised_ids.mapped(
                    'x_compromised_id').ids
                          or rec.x_taraz_part_id.id in l.x_taraz_part_id.x_compromised_ids.mapped(
                    'x_compromised_id').ids
            )
            if len(mergeable_lines_ids) > 1:
                mergeable_lines = ','.join([str(line.x_product_id.name) for line in mergeable_lines_ids])
                for line in mergeable_lines_ids:
                    line.x_mergeable_lines = mergeable_lines
                mergeable_lines_alternates = rec.x_proc_cycle_id.x_short_component_ids.filtered(
                    lambda l: rec.x_product_id.product_tmpl_id.id in l.x_taraz_part_id.x_alternate_ids.mapped(
                        'x_product_id').ids
                              and rec.x_taraz_part_id.id != l.x_taraz_part_id.id
                )
                if mergeable_lines_alternates:
                    rec.x_mergeable_line_warning = ('Warning: Product is alternate in %s but Taraz Part # is not same'
                                                    % (mergeable_lines_alternates[0].x_taraz_part_id.x_name))
                else:
                    rec.x_mergeable_line_warning = False
            else:
                rec.x_mergeable_lines = 'Non Mergeable'
                rec.x_mergeable_line_warning = False

    @api.depends('x_proc_cycle_id.x_cart_ids')
    def compute_cart_ids(self):
        for rec in self:
            rec.x_cart_ids = [(6, 0, rec.x_proc_cycle_id.x_cart_ids.ids)]

    @api.depends('x_proc_cycle_id.x_budget_ids')
    def compute_budget_ids(self):
        for rec in self:
            rec.x_budget_ids = [(6, 0, rec.x_proc_cycle_id.x_budget_ids.ids)]

    @api.onchange('x_default_qty', 'x_reorder_point', 'x_moq', 'x_roq', 'x_broq', 'x_manual_qty')
    def onchange_default_qty(self):
        for rec in self:
            if rec.x_default_qty == 'rp':
                rec.x_manual_qty = rec.x_reorder_point
                rec.x_quantities_ids.update({'x_quantity': rec.x_reorder_point})
            elif rec.x_default_qty == 'moq':
                rec.x_manual_qty = rec.x_moq
                rec.x_quantities_ids.update({'x_quantity': rec.x_moq})
            elif rec.x_default_qty == 'roq':
                rec.x_manual_qty = rec.x_roq
                rec.x_quantities_ids.update({'x_quantity': rec.x_roq})
            elif rec.x_default_qty == 'broq':
                rec.x_manual_qty = rec.x_broq
                rec.x_quantities_ids.update({'x_quantity': rec.x_broq})
            elif rec.x_default_qty == 'manual':
                rec.x_quantities_ids.update({'x_quantity': rec.x_manual_qty})

    def compute_safety_stock(self):
        for rec in self:
            rec.x_taraz_part_id.compute_safety_stock()
            rec.x_moq = rec.x_missing_qty
            rec.x_roq = rec.x_missing_qty + rec.x_reorder_point
            if rec.x_taraz_part_id.x_roq != 0:
                rec.x_broq = rec.x_taraz_part_id.x_roq * math.ceil(
                    rec.x_roq / rec.x_taraz_part_id.x_roq) if rec.x_roq else rec.x_taraz_part_id.x_roq
            else:
                average_lead_time = float(self.env['ir.config_parameter'].sudo().get_param('stock.x_average_lead_time'))
                bulk_stock_months = float(self.env['ir.config_parameter'].sudo().get_param('stock.x_bulk_stock_months'))
                if average_lead_time:
                    bulk_consumption = round(
                        (rec.x_reorder_point - rec.x_safety_stock) / average_lead_time * bulk_stock_months, 0)
                    bulk_reorder_point = rec.x_safety_stock + bulk_consumption
                    rec.x_broq = rec.x_missing_qty + bulk_reorder_point
            if rec.x_roq <= rec.x_qty_available:
                rec.x_status = 'ignore'

    def compute_cart_lines(self):
        for rec in self:
            rec.x_quantities_ids = [(2, line.id) for line in rec.x_quantities_ids]
            product_ids = [{'orig': rec.x_product_id}]
            alt_product_ids = rec.x_taraz_part_id.x_alternate_ids.mapped('x_product_id').mapped(
                'product_variant_id').filtered(lambda l: l.id != rec.x_product_id.id)
            product_ids += [{'alt': alt_product_id} for alt_product_id in alt_product_ids]
            comp_product_ids = rec.x_taraz_part_id.x_compromised_ids.mapped('x_compromised_id').mapped(
                'x_alternate_ids').mapped('x_product_id').mapped('product_variant_id')
            product_ids += [{'comp': comp_product_id} for comp_product_id in comp_product_ids]
            quantities_ids = []
            for product_id in product_ids:
                product = list(product_id.values())[0]
                if product:
                    quantities_ids.append((0, 0, {
                        'x_relation': list(product_id.keys())[0],
                        'x_product_id': product.id,
                        'x_quantity': 0,
                        'x_uom_id': product.uom_id.id,
                    }))
            rec.x_quantities_ids = quantities_ids
            rec.onchange_default_qty()
            rec.x_quantities_ids.onchange_product_id()

    @api.depends('x_demand_detail_ids.x_remaining_days')
    def compute_remaining_days(self):
        for rec in self:
            if rec.x_demand_detail_ids.mapped('x_remaining_days'):
                rec.x_remaining_days = min(rec.x_demand_detail_ids.mapped('x_remaining_days'))

    def unlink(self):
        self.x_quantities_ids.unlink()
        self.x_demand_detail_ids.unlink()
        self.x_purchase_history_ids.unlink()
        self.x_consumption_ids.unlink()
        return super(ComponentList, self).unlink()


class ComponentListQuantities(models.Model):
    _name = "component.list.quantities"
    _description = "Component List Quantities"
    _rec_name = "x_product_id"

    x_component_id = fields.Many2one(comodel_name='component.list', string='PRC Line', required=False)
    x_proc_cycle_id = fields.Many2one(related="x_component_id.x_proc_cycle_id")

    x_relation = fields.Selection(selection=[
        ('orig', 'Original'), ('alt', 'Alternate'), ('comp', 'Compromised'),
    ], string='Relation', default='orig', )
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_description = fields.Text(related="x_product_id.description")
    x_mounting_type = fields.Selection(related="x_product_id.x_mounting_type", store=True)
    x_eoq = fields.Float(string='EOQ', digits="Product Unit of Measure", compute="_compute_eoq", readonly=False,
                         store=True)
    x_quantity = fields.Float(string='Quantity', digits="Product Unit of Measure", required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)

    x_octopart_connector_id = fields.Many2one(comodel_name='octopart.connector', string='Octopart')

    x_seller_ids = fields.Many2many(
        comodel_name='part.seller',
        relation='component_list_quantities_seller_rel',
        column1='x_component_list_quantities_id',
        column2='x_part_seller_id',
        string='Sellers',
        compute="_compute_seller_ids",
        store=True,
    )
    x_seller_id = fields.Many2one(
        comodel_name='part.seller',
        string='Seller',
        domain="["
               "('x_inventory_level', '>', 0), "
               "('x_connector_id', '=', x_octopart_connector_id), "
               "('id', 'in', x_seller_ids), "
               "]",
        compute="_compute_seller_id", readonly=False, store=True)

    x_partner_id = fields.Many2one(related="x_seller_id.x_partner_id", readonly=False, store=True,
                                   context="{'res_partner_search_mode': 'supplier'}",
                                   domain="[('supplier_rank', '>', 0)]")
    x_prc_cart_id = fields.Many2one(
        comodel_name='procurement.cycle.cart.details', string='Cart #', required=False,
        context="{"
                "'default_x_proc_cycle_id': x_proc_cycle_id,"
                "'default_x_partner_id': x_partner_id,"
                "}",
        domain="[('x_proc_cycle_id', '=', x_proc_cycle_id)]")

    x_unit_price = fields.Float(string='Unit Price', compute="_compute_unit_price", store=True, digits=(12, 4))
    x_ext_price = fields.Float(string='Ext. Price', compute="_compute_ext_price", store=True, digits=(12, 4))
    x_overspent = fields.Float(string='Overspent', required=False)

    x_actual_unit_price = fields.Float(string='Actual Unit', digits=(12, 4))
    x_actual_ext_price = fields.Float(string='Actual Ext.', compute="_compute_actual_ext_price", store=True,
                                      digits=(12, 4))

    x_sale_ids = fields.Many2many(comodel_name='sale.order', string='Sale Orders')
    x_cart_status = fields.Selection(related="x_component_id.x_status", store=True)
    x_compute_sale_ids = fields.Boolean(compute="compute_sale_ids")

    def write(self, vals):
        res = super(ComponentListQuantities, self).write(vals)
        eoq = sum(self.x_component_id.x_quantities_ids.filtered(lambda q: q.x_prc_cart_id).mapped('x_eoq'))
        ordered_cart_ids = self.x_component_id.x_quantities_ids.filtered(
            lambda q: q.x_prc_cart_id and q.x_prc_cart_id.x_status in ('cart_partially_ordered', 'cart_ordered')
        )
        if not ordered_cart_ids:
            if eoq < self.x_component_id.x_manual_qty and eoq and self.x_component_id.x_manual_qty:
                self.x_component_id.x_status = 'cart_partially_defined'
            elif eoq >= self.x_component_id.x_manual_qty and eoq and self.x_component_id.x_manual_qty:
                self.x_component_id.x_status = 'cart_defined'
        return res

    def compute_sale_ids(self):
        for rec in self:
            rec.x_sale_ids = [(6, 0, rec.x_component_id.x_demand_detail_ids.mapped('x_sale_id').ids)]
            rec.x_compute_sale_ids = True

    @api.onchange('x_prc_cart_id')
    def onchange_prc_cart_id(self):
        for rec in self:
            if rec.x_prc_cart_id:
                rec.x_partner_id = rec.x_prc_cart_id.x_partner_id.id

    @api.onchange('x_product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.x_uom_id = rec.x_product_id.uom_id.id
            octopart_connector_id = self.env['octopart.connector'].search([
                ('x_product_id', '=', rec.x_product_id.id)], limit=1)
            if octopart_connector_id:
                octopart_connector_id.get_part_details()
            else:
                octopart_connector_id = self.env['octopart.connector'].create({
                    'x_product_id': rec.x_product_id.id,
                })
            rec.x_octopart_connector_id = octopart_connector_id.id

    @api.depends('x_seller_id')
    def _compute_unit_price(self):
        for rec in self:
            rec.x_unit_price = rec.x_seller_id.x_price if rec.x_seller_id else 0
            rec.x_actual_unit_price = rec.x_unit_price if rec.x_actual_unit_price == 0 else rec.x_actual_unit_price

    @api.depends('x_quantity', 'x_component_id.x_vendor_type', 'x_octopart_connector_id')
    def _compute_seller_ids(self):
        for rec in self:
            seller_ids = rec.x_octopart_connector_id.x_seller_ids.sorted(key=lambda s: s.x_quantity, reverse=True)

            if rec.x_component_id.x_vendor_type == 'preferred':
                seller_ids = seller_ids.filtered(
                    lambda s: s.x_partner_id.x_define_vendor_code
                    # or s.x_partner_id.x_preferred_vendor
                )

            final_seller_ids = []
            partner_ids = seller_ids.mapped('x_partner_id')
            for partner_id in partner_ids:
                final_seller_id = seller_ids.filtered(
                    lambda s: s.x_partner_id.id == partner_id.id and s.x_quantity <= rec.x_quantity
                )
                if final_seller_id:
                    final_seller_ids.append(final_seller_id[0].id)

            rec.x_seller_ids = [(6, 0, final_seller_ids)] if rec.x_quantity else [(6, 0, seller_ids.ids)]

    @api.depends('x_quantity', 'x_component_id.x_vendor_type')
    def _compute_seller_id(self):
        for rec in self:
            cost_overhead = float(self.env['ir.config_parameter'].sudo().get_param('stock.x_cost_overhead'))
            if rec.x_component_id.x_vendor_type == 'preferred':
                seller_ids = self.env['part.seller'].search([
                    ('x_inventory_level', '>', 0),
                    ('x_connector_id', '=', rec.x_octopart_connector_id.id),
                    ('x_partner_id.x_define_vendor_code', '!=', False),
                    # ('x_partner_id.x_preferred_vendor', '!=', False),
                ])
            else:
                seller_ids = self.env['part.seller'].search([
                    ('x_inventory_level', '>', 0),
                    ('x_connector_id', '=', rec.x_octopart_connector_id.id),
                ])

            if seller_ids:
                # Get sellers with x_quantity is less than or equal to x_quantity
                qty_seller_ids = seller_ids.filtered(lambda l: l.x_quantity <= rec.x_quantity)
                if qty_seller_ids:
                    # Get seller with minimum price
                    qty_seller_id = qty_seller_ids.sorted(key=lambda l: l.x_price)[0]
                    # Get sellers with subtotal less than or equal to minimum subtotal * (1 + cost_overhead)
                    eoq_seller_ids = seller_ids.filtered(
                        lambda l: l.x_quantity * l.x_price <= rec.x_quantity * qty_seller_id.x_price * (
                                    1 + cost_overhead))
                    # Get seller with minimum price
                    eoq_seller_id = eoq_seller_ids.sorted(key=lambda l: l.x_price)[0]

                    rec.x_seller_id = eoq_seller_id.id
                else:
                    rec.x_seller_id = False
            else:
                rec.x_seller_id = False

    @api.depends('x_quantity', 'x_seller_id')
    def _compute_eoq(self):
        for rec in self:
            if rec.x_seller_id.x_quantity >= rec.x_quantity and rec.x_seller_id.x_inventory_level >= rec.x_quantity:
                rec.x_eoq = rec.x_seller_id.x_quantity
            elif rec.x_quantity >= rec.x_seller_id.x_inventory_level:
                rec.x_eoq = rec.x_seller_id.x_inventory_level
            else:
                rec.x_eoq = rec.x_quantity
            if rec.x_component_id.x_vendor_type == 'preferred':
                seller_ids = self.env['part.seller'].search([
                    ('x_inventory_level', '>', 0),
                    ('x_connector_id', '=', rec.x_octopart_connector_id.id),
                    ('x_partner_id.x_define_vendor_code', '!=', False),
                    # ('x_partner_id.x_preferred_vendor', '!=', False)
                ])
            else:
                seller_ids = self.env['part.seller'].search([
                    ('x_inventory_level', '>', 0),
                    ('x_connector_id', '=', rec.x_octopart_connector_id.id)
                ])
            if seller_ids:
                qty_seller_ids = seller_ids.filtered(lambda l: l.x_quantity <= rec.x_quantity)
                if qty_seller_ids:
                    qty_seller_id = qty_seller_ids.sorted(key=lambda l: l.x_price)[0]
                    if rec.x_quantity * qty_seller_id.x_price != 0:
                        rec.x_overspent = ((rec.x_eoq * rec.x_seller_id.x_price)
                                           / (rec.x_quantity * qty_seller_id.x_price) - 1)
                    else:
                        rec.x_overspent = 0

    @api.depends('x_eoq', 'x_unit_price')
    def _compute_ext_price(self):
        for rec in self:
            rec.x_ext_price = round(rec.x_eoq * rec.x_unit_price, 4)

    @api.depends('x_eoq', 'x_actual_unit_price')
    def _compute_actual_ext_price(self):
        for rec in self:
            rec.x_actual_ext_price = round(rec.x_eoq * rec.x_actual_unit_price, 4)


class ComponentListDemandDetails(models.Model):
    _name = "component.list.demand.details"
    _description = "Component List Demand Details"
    _rec_name = "x_component_id"

    x_component_id = fields.Many2one(comodel_name='component.list', string='Component', required=False)

    x_type = fields.Selection(selection=[
        ('sale', 'Sale'), ('stock', 'Stock Build'), ('internal', 'Internal Demand'), ('safety_stock', 'Safety Stock'),
    ], string='Type', required=False, )
    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=False)
    x_internal_demand_id = fields.Many2one(comodel_name='manual.proc.demand.lines', string='Internal Demand',
                                           required=False)
    x_user_id = fields.Many2one(related='x_internal_demand_id.x_user_id')
    x_url = fields.Char(related='x_internal_demand_id.x_url')
    x_note = fields.Char(related='x_internal_demand_id.x_note')
    x_deadline = fields.Datetime(related="x_sale_id.x_deadline")
    x_remaining_days = fields.Integer(string='Criticality (Days)', compute="compute_remaining_days", store=True)
    x_quantity = fields.Float(string='Required', required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)
    x_manufacturing_id = fields.Many2one(comodel_name='mrp.production', string='Manufacturing Order', required=False)
    x_safety_stock_line_id = fields.Many2one(comodel_name='safety.stock.input', string='Safety Stock Line')

    @api.depends('x_deadline')
    def compute_remaining_days(self):
        for rec in self:
            if rec.x_deadline:
                rec.x_remaining_days = (rec.x_deadline - datetime.datetime.now()).days

    @api.model
    def calculate_remaining_days(self):
        demand_ids = self.env['component.list.demand.details'].search([])
        for rec in demand_ids:
            if rec.x_deadline:
                rec.x_remaining_days = (rec.x_deadline - datetime.datetime.now()).days


class ComponentListPurchaseHistory(models.Model):
    _name = "component.list.purchase.history"
    _description = "Component List Purchase History"
    _rec_name = "x_vendor_id"

    x_component_id = fields.Many2one(comodel_name='component.list', string='Component', required=False)

    x_relation = fields.Selection(selection=[
        ('orig', 'Original'), ('alt', 'Alternate'), ('comp', 'Compromised'),
    ], string='Relation', required=False, )

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_vendor_id = fields.Many2one(comodel_name='res.partner', string='Product', required=False)
    x_order_date = fields.Date(string='Order Date')
    x_purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', required=False)
    x_quantity = fields.Float(string='Quantity', required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=False)
    x_unit_price = fields.Float(string='Unit Price', required=False)
    x_subtotal = fields.Float(string='Subtotal', required=False)


class ComponentListConsumption(models.Model):
    _name = "component.list.consumption"
    _description = "Component List Consumption"
    _rec_name = "x_product_id"

    x_component_id = fields.Many2one(comodel_name='component.list', string='Component', required=False)

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_quantity = fields.Float(string='Quantity', required=False)
    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)


class OrderList(models.Model):
    _name = "order.list"
    _description = "Order List"


class OrderListNumber(models.Model):
    _name = "order.list.number"
    _description = "Order List Number"
