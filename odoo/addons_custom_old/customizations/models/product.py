from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_available_qty = fields.Float(
        string='Available', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')
    x_to_consume_qty = fields.Float(
        string='To Consume', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')
    x_tray_out_qty = fields.Float(
        string='Tray Out', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')
    x_incoming_qty = fields.Float(
        string='Incoming (Actual)', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')
    x_backorder_qty = fields.Float(
        string='Backorder', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        compute_sudo=False, digits='Product Unit of Measure')

    x_taraz_part_number = fields.Char(string="Taraz Part Number", required=False, )
    x_short_description = fields.Char(string="Short Description", required=False, translate=True)
    x_short_name = fields.Char(string="Short Name", required=False, )
    x_packaging_info = fields.Char(string="Packaging Info", required=False, )
    x_package_weight = fields.Char(string="Package Weight", required=False, )
    x_package_volume = fields.Char(string="Package Volume", required=False, )
    x_hs_code_category = fields.Char(string="HS Code Category", required=False, )
    x_hs_code_description = fields.Char(string="HS Code Description", required=False, )
    x_hs_code_vendor = fields.Char(string="HS Code (Vendor)", required=False, )
    x_country_of_origin = fields.Char(string="COO", required=False, )
    x_country_id = fields.Many2one(comodel_name='res.country', string='Country of Origin', tracking=True)
    x_source = fields.Char(string="Source", required=False, )
    x_custom_duty = fields.Float(string="Custom Duty (%)", required=False, )
    x_additional_custom_duty = fields.Float(string="Additional CD (%)", required=False, )
    x_regulatory_duty = fields.Float(string="Regulatory Duty (%)", required=False, )
    x_lc_factor = fields.Float(string="LC Factor", required=False, )
    x_split_method = fields.Selection(selection=[
        ('equal', 'Equal'),
        ('by_quantity', 'By Quantity'),
        ('by_current_cost_price', 'By Current Cost'),
        ('by_weight', 'By Weight'),
        ('by_volume', 'By Volume'),
        ('custom_duty', 'Custom Duty'),
        ('additional_custom_duty', 'Additional Custom Duty'),
        ('regulatory_duty', 'Regulatory Duty'),
    ], required=False, string="Split Method", )
    x_wh_rules = fields.Text(string="WH Rules", required=False, )
    x_qc_checklist = fields.Text(string="QC Checklist", required=False, )
    x_packing_list = fields.Text(string="Packing List", required=False, )
    x_route = fields.Text(string="Route", required=False, )
    x_ao_mo_instructions = fields.Text(string="AO/MO Instructions", required=False, )
    x_part_level_comments = fields.Text(string="Part Level Comments", required=False, )
    x_description_on_undertaking = fields.Text(string="Description on Undertaking", required=False, )
    x_description_for_distributor = fields.Text(string="Description for Distributor", required=False, )
    x_delivery_order_checklist = fields.Text(string="Delivery Order Checklist", required=False, )
    x_product_group = fields.Many2one(comodel_name="product.group", string="Product Group", required=False, )
    x_product_series = fields.Many2one(comodel_name="product.series", string="Product Series", required=False, )
    x_product_division = fields.Many2one(comodel_name="product.division", string="Product Division", required=False, )
    x_add_in_landed_cost = fields.Boolean(string="Add in Landed Cost", default=True)
    x_product_tag = fields.Many2many(comodel_name="product.tags", relation="product_template_product_tags_rel",
                                     column1="product_template_id", column2="product_tags_id", string="Product Tags", )
    x_bos_product = fields.Boolean(string="BOS Product?", )
    x_main_product_id = fields.Many2one(comodel_name="product.product", string="Main Product", required=False, )
    x_critical = fields.Boolean(string='Critical Product', required=False)

    @api.depends(
        'product_variant_ids',
        'product_variant_ids.stock_move_ids.product_qty',
        'product_variant_ids.stock_move_ids.state',
    )
    @api.depends_context('company_owned', 'force_company')
    def _compute_custom_quantities(self):
        res_custom = self._compute_custom_quantities_dict()
        for template in self:
            template.x_available_qty = res_custom[template.id]['x_available_qty']
            template.x_to_consume_qty = res_custom[template.id]['x_to_consume_qty']
            template.x_tray_out_qty = res_custom[template.id]['x_tray_out_qty']
            template.x_incoming_qty = res_custom[template.id]['x_incoming_qty']
            template.x_backorder_qty = res_custom[template.id]['x_backorder_qty']

    def _compute_custom_quantities_dict(self):
        variants_available = self.mapped('product_variant_ids')._product_available()
        variants_custom_available = self.mapped('product_variant_ids')._product_custom_available()
        prod_available = {}
        for template in self:
            available_qty = 0
            to_consume_qty = 0
            tray_out_qty = 0
            incoming_qty = 0
            backorder_qty = 0
            for p in template.product_variant_ids:
                available_qty += variants_available[p.id]["free_qty"]
                to_consume_qty += variants_custom_available[p.id]["x_to_consume_qty"]
                tray_out_qty += variants_custom_available[p.id]["x_tray_out_qty"]
                incoming_qty += variants_custom_available[p.id]["x_incoming_qty"]
                backorder_qty += variants_custom_available[p.id]["x_backorder_qty"]
            prod_available[template.id] = {
                "x_available_qty": available_qty,
                "x_to_consume_qty": to_consume_qty,
                "x_tray_out_qty": tray_out_qty,
                "x_incoming_qty": incoming_qty,
                "x_backorder_qty": backorder_qty,
            }
        return prod_available

    # @api.depends('product_variant_ids.stock_move_ids.product_qty', 'product_variant_ids.stock_move_ids.state')
    # def _compute_custom_quantities(self):
    #     for rec in self:
    #         rec.product_variant_ids._compute_custom_quantities()
    #         rec.x_available_qty = sum(rec.product_variant_ids.mapped('free_qty'))
    #         rec.x_to_consume_qty = sum(rec.product_variant_ids.mapped('x_to_consume_qty'))
    #         rec.x_tray_out_qty = sum(rec.product_variant_ids.mapped('x_tray_out_qty'))
    #         rec.x_incoming_qty = sum(rec.product_variant_ids.mapped('x_incoming_qty'))
    #         rec.x_backorder_qty = sum(rec.product_variant_ids.mapped('x_backorder_qty'))

    def action_view_product_tmpl_receipts(self):
        return self.product_variant_id.action_view_product_receipts()

    def action_view_product_tmpl_incoming_receipts(self):
        return self.product_variant_id.action_view_product_incoming_receipts()

    def action_view_product_tmpl_backorder_receipts(self):
        return self.product_variant_id.action_view_product_backorder_receipts()

    def action_view_product_tmpl_manufacturing_delivery(self):
        return self.product_variant_id.action_view_product_manufacturing_delivery()

    def action_view_product_tmpl_manufacturing_to_consume(self):
        return self.product_variant_id.action_view_product_manufacturing_to_consume()

    def action_view_product_tmpl_manufacturing_tray_out(self):
        return self.product_variant_id.action_view_product_manufacturing_tray_out()

    @api.onchange('x_bos_product')
    def update_main_product(self):
        for rec in self:
            if not rec.x_bos_product: rec.x_main_product_id = False

    @api.onchange('x_product_series')
    def update_hs_code(self):
        for rec in self:
            if rec.x_product_series:
                rec.hs_code = 'HS' + rec.x_product_series.x_hs_code_id.x_hs_code if rec.x_product_series.x_hs_code_id else rec.hs_code

    @api.onchange('categ_id')
    def update_coo(self):
        for rec in self:
            if '[FG]' in rec.categ_id.name:
                rec.x_country_of_origin = 'Pakistan'

    @api.onchange('x_product_group')
    def update_product_series(self):
        for record in self:
            record.x_product_series = record.x_product_group.series.id

    @api.onchange('x_product_series')
    def update_product_division(self):
        for record in self:
            record.x_product_division = record.x_product_series.division.id


class ProductProduct(models.Model):
    _inherit = "product.product"

    x_to_consume_qty = fields.Float(
        string='To Consume', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")
    x_tray_out_qty = fields.Float(
        string='Tray Out', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")
    x_incoming_qty = fields.Float(
        string='Incoming (Actual)', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")
    x_backorder_qty = fields.Float(
        string='Backorder', compute='_compute_custom_quantities', search='_search_outgoing_qty',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'company_owned', 'force_company',
    )
    def _compute_custom_quantities(self):
        products = self.filtered(lambda p: p.type != 'service')
        res = products._compute_custom_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in products:
            product.x_to_consume_qty = res[product.id]['x_to_consume_qty']
            product.x_tray_out_qty = res[product.id]['x_tray_out_qty']
            product.x_incoming_qty = res[product.id]['x_incoming_qty']
            product.x_backorder_qty = res[product.id]['x_backorder_qty']
        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.x_to_consume_qty = 0.0
        services.x_tray_out_qty = 0.0
        services.x_incoming_qty = 0.0
        services.x_backorder_qty = 0.0

    def _product_custom_available(self, field_names=None, arg=False):
        """ Compatibility method """
        return self._compute_custom_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))

    def _compute_custom_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if from_date:
            date_date_expected_domain_from = [
                '|',
                    '&',
                        ('state', '=', 'done'),
                        ('date', '<=', from_date),
                    '&',
                        ('state', '!=', 'done'),
                        ('date_expected', '<=', from_date),
            ]
            domain_move_in += date_date_expected_domain_from
            domain_move_out += date_date_expected_domain_from
        if to_date:
            date_date_expected_domain_to = [
                '|',
                    '&',
                        ('state', '=', 'done'),
                        ('date', '<=', to_date),
                    '&',
                        ('state', '!=', 'done'),
                        ('date_expected', '<=', to_date),
            ]
            domain_move_in += date_date_expected_domain_to
            domain_move_out += date_date_expected_domain_to

        move = self.env['stock.move']
        quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_in_todo_backorder = ['|', ('picking_id.backorder_id', '!=', False), ('picking_id.x_backorder_products', '!=', False)] + domain_move_in_todo
        pbm_loc_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1).pbm_loc_id
        domain_quant_try_out = [('location_id', '=', pbm_loc_id.id)] + domain_quant
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_in_res_backorder = dict((item['product_id'][0], item['product_qty']) for item in move.read_group(domain_move_in_todo_backorder, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        quants_res = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in quant.read_group(domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
        quants_res_try_out = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in quant.read_group(domain_quant_try_out, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
        res = dict()
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            if not product_id:
                res[product_id] = dict.fromkeys(
                    ['x_to_consume_qty', 'x_tray_out_qty', 'x_incoming_qty', 'x_backorder_qty'],
                    0.0,
                )
                continue
            rounding = product.uom_id.rounding
            res[product_id] = {}
            reserved_quantity = quants_res.get(product_id, [False, 0.0])[1]
            tray_out_qty_reserved = quants_res_try_out.get(product_id, [False, 0.0])[1]
            incoming_qty = moves_in_res.get(product_id, 0.0)
            backorder_qty = moves_in_res_backorder.get(product_id, 0.0)
            res[product_id]['x_to_consume_qty'] = float_round(reserved_quantity - tray_out_qty_reserved, precision_rounding=rounding)
            res[product_id]['x_tray_out_qty'] = float_round(quants_res_try_out.get(product_id, [0.0])[0], precision_rounding=rounding)
            res[product_id]['x_incoming_qty'] = float_round(incoming_qty - backorder_qty, precision_rounding=rounding)
            res[product_id]['x_backorder_qty'] = float_round(backorder_qty, precision_rounding=rounding)

        return res

    # @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    # def _compute_quantities(self):
    #     for rec in self:
    #         domain_quant_loc, domain_move_in_loc, domain_move_out_loc = rec._get_domain_locations()
    #         domain_quant = [('product_id', 'in', rec.ids)] + domain_quant_loc
    #         quant = self.env['stock.quant']
    #
    #         quants_res = dict(
    #             (item['location_id'][0], (item['quantity'], item['reserved_quantity']))
    #             for item in quant.read_group(
    #                 domain_quant, ['location_id', 'quantity', 'reserved_quantity'], ['location_id'], orderby='id'
    #             )
    #         )
    #
    #         warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
    #         pbm_loc_id = warehouse_id.pbm_loc_id.id
    #         rec.x_tray_out_qty = quants_res.get(pbm_loc_id, [0.0])[0]
    #         try_out_reserved = quants_res.get(pbm_loc_id, [False, 0.0])[1]
    #
    #         quants_res = dict(
    #             (item['product_id'][0], (item['quantity'], item['reserved_quantity']))
    #             for item in quant.read_group(
    #                 domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'
    #             )
    #         )
    #
    #         qty_available = quants_res.get(rec.id, [0.0])[0]
    #         reserved_quantity = quants_res.get(rec.id, [False, 0.0])[1]
    #         rec.x_to_consume_qty = reserved_quantity - try_out_reserved
    #
    #         move_ids = rec.stock_move_ids.filtered(
    #             lambda l: l.picking_code == 'incoming'
    #             and l.picking_id.state in ['draft', 'waiting', 'assigned', 'confirmed']
    #             and (l.picking_id.backorder_id or l.picking_id.x_backorder_products)
    #         )
    #
    #         # move_ids = rec.stock_move_ids.search([
    #         #     ('picking_code', '=', 'incoming'),
    #         #     ('picking_id.state', 'in', ('draft', 'waiting', 'assigned', 'confirmed')),
    #         #     '|', ('picking_id.backorder_id', '!=', False),
    #         #     ('picking_id.x_backorder_products', '!=', False),
    #         # ])
    #
    #         backorder_qty = sum(move_ids.mapped('product_qty'))
    #
    #         rec.x_incoming_qty = rec.incoming_qty - backorder_qty
    #         rec.x_backorder_qty = backorder_qty

    def action_view_product_receipts(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')),
                  ('product_id', '=', self.id)] + domain_move_in_loc
        action_picking = self.env.ref('stock.action_receipt_picking_move')
        action = action_picking.read()[0]
        action['domain'] = domain
        return action

    def action_view_product_incoming_receipts(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')),
                  ('product_id', '=', self.id), ('quantity_done', '!=', 0)] + domain_move_in_loc
        action_picking = self.env.ref('stock.action_receipt_picking_move')
        action = action_picking.read()[0]
        action['domain'] = domain
        return action

    def action_view_product_backorder_receipts(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')),
                  '|', ('picking_id.backorder_id', '!=', False), ('picking_id.x_backorder_products', '!=', False),
                  ('product_id', '=', self.id)] + domain_move_in_loc
        action_picking = self.env.ref('stock.action_receipt_picking_move')
        action = action_picking.read()[0]
        action['domain'] = domain
        return action

    def action_view_product_manufacturing_delivery(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')),
                  ('product_id', '=', self.id)] + domain_move_out_loc
        action_picking = self.env.ref('customizations.act_product_stock_move_reserved')
        action = action_picking.read()[0]
        action['domain'] = domain
        return action

    def action_view_product_manufacturing_to_consume(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('product_id', '=', self.id), ('state', '=', 'waiting'),
                  ('move_orig_ids.state', 'in', ['assigned', 'partially_available'])] + domain_move_out_loc
        move_ids = self.env['stock.move'].search(domain).mapped('move_orig_ids')
        action_picking = self.env.ref('customizations.act_product_stock_move_reserved')
        action = action_picking.read()[0]
        action['domain'] = [('id', 'in', move_ids.ids)]
        return action

    def action_view_product_manufacturing_tray_out(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain = [('product_id', '=', self.id), ('raw_material_production_id', '!=', False),
                  ('state', 'in', ['assigned', 'partially_available']),
                  ('move_orig_ids.state', '=', 'done')] + domain_move_out_loc
        action_picking = self.env.ref('customizations.act_product_stock_move_reserved')
        action = action_picking.read()[0]
        action['domain'] = domain
        return action

    @api.onchange('x_product_group')
    def update_product_series(self):
        for record in self:
            record.x_product_series = record.x_product_group.series.id

    @api.onchange('x_product_series')
    def update_product_division(self):
        for record in self:
            record.x_product_division = record.x_product_series.division.id

    @api.onchange('x_bos_product')
    def update_main_product(self):
        for rec in self:
            if not rec.x_bos_product: rec.x_main_product_id = False
