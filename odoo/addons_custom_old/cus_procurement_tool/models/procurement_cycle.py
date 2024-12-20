from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ProcurementCycle(models.Model):
    _name = "procurement.cycle"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Procurement Cycle"
    _rec_name = "x_name"
    _order = "create_date desc"

    state = fields.Selection(selection=[
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled')],
        string="Status", required=True, readonly=True, copy=False, tracking=True, default='new')

    x_name = fields.Char(
        string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    
    x_demand_batch_ids = fields.Many2many(comodel_name='mrp.procurement.batch', string='Demand Batches')
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')
    x_company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                   required=True, default=lambda self: self.env.company)

    x_manufacturing_ids = fields.Many2many(comodel_name='mrp.production', string='Manufacturing Orders')

    x_manual_proc_demand_lines_ids = fields.One2many(
        comodel_name='manual.proc.demand.lines',
        inverse_name='x_procurement_cycle_id',
        string='Manual Procurement Demand Lines (RM)',)

    x_safety_stock_total_price = fields.Float(
        string='Total Price',
        compute='_compute_safety_stock_total_price',
        store=True,)

    x_safety_stock_input_ids = fields.One2many(
        comodel_name='safety.stock.input',
        inverse_name='x_procurement_cycle_id',
        string='Safety Stock Inputs',)

    x_short_component_ids = fields.One2many(
        comodel_name='component.list', inverse_name='x_proc_cycle_id', string='Short Components', required=False)

    x_cart_ids = fields.One2many(
        comodel_name='procurement.cycle.cart.details',
        inverse_name='x_proc_cycle_id',
        string='Carts',
        readonly=False)

    x_budget_ids = fields.One2many(
        comodel_name='procurement.cycle.budget.details',
        inverse_name='x_proc_cycle_id',
        string='Budgets',
        compute="_compute_budget_ids",
        store=True,
        readonly=False)

    x_planned_start_date = fields.Datetime(string='Planned Start Date', tracking=True)
    x_planned_finish_date = fields.Datetime(string='Planned Finish Date', tracking=True)

    @api.depends('x_cart_ids', 'x_cart_ids.x_journal_id')
    def _compute_budget_ids(self):
        for rec in self:
            rec.x_budget_ids = [(2, line.id) for line in rec.x_budget_ids
                                if line.x_journal_id.id not in rec.x_cart_ids.mapped('x_journal_id').ids]
            budget_ids = []
            for line in rec.x_cart_ids.mapped('x_journal_id'):
                cart_ids = rec.x_cart_ids.filtered(lambda l: l.x_journal_id.id == line.id)
                budget_id = rec.x_budget_ids.filtered(lambda l: l.x_journal_id.id == line.id)
                if budget_id:
                    budget_id.x_cart_ids = cart_ids.ids
                else:
                    budget_ids.append((0, 0, {
                        'x_proc_cycle_id': rec.id,
                        'x_journal_id': line.id,
                        'x_cart_ids': cart_ids.ids,
                    }))
            rec.x_budget_ids = budget_ids

    @api.depends('x_safety_stock_input_ids', 'x_safety_stock_input_ids.x_subtotal',)
    def _compute_safety_stock_total_price(self):
        for rec in self:
            rec.x_safety_stock_total_price = sum(rec.x_safety_stock_input_ids.mapped('x_subtotal'))

    def get_manual_proc_demand_lines(self):
        for rec in self:
            manual_proc_demand_lines = self.env['manual.proc.demand'].search([
                ('x_status', '=', 'draft'), ('x_product_qty', '!=', 0), ('x_company_id', '=', rec.x_company_id.id)
            ])
            rec.x_manual_proc_demand_lines_ids = [
                (2, line.id) for line in rec.x_manual_proc_demand_lines_ids.filtered(lambda l: l.x_status == 'draft')]
            manual_proc_demand_lines_ids = []
            for line in manual_proc_demand_lines:
                manual_proc_demand_lines_ids.append((0, 0, {
                    'x_manual_proc_demand_id': line.id,
                }))
            rec.x_manual_proc_demand_lines_ids = manual_proc_demand_lines_ids

    def get_safety_stock_input(self):
        taraz_part_ids = self.env['taraz.part.number'].search([('x_enable_safety_stock', '!=', False)])
        # for taraz_part_id in taraz_part_ids.filtered(lambda l: not l.x_safety_stock_calculated):
        for taraz_part_id in taraz_part_ids:
            taraz_part_id.compute_safety_stock()
        taraz_part_ids = taraz_part_ids.filtered(lambda l: l.x_qty_available < l.x_reorder_point)
        bom_line_ids = self.env['bom.tool'].search([
            ('x_enable_safety_stock', '!=', False)
        ]).mapped('x_base_bom_id').mapped('x_bom_line_ids')
        for rec in self:
            rec.x_safety_stock_input_ids = [(2, line.id) for line in rec.x_safety_stock_input_ids]
            safety_stock_input_ids = []
            for line in taraz_part_ids:
                product_ids = bom_line_ids.filtered(
                    lambda l: l.x_taraz_part_id.id == line.id).mapped('x_base_bom_id').mapped('x_product_id')
                safety_stock_input_ids.append((0, 0, {
                    'x_taraz_part_id': line.id,
                    'x_product_id': line.x_alternate_ids[0].x_product_id.product_variant_id.id,
                    'x_quantity': line.x_order_quantity or line.x_roq or line.x_reorder_point,
                    'x_product_ids': product_ids.ids
                }))
            rec.x_safety_stock_input_ids = safety_stock_input_ids

    def remove_safety_stock_input(self):
        for rec in self:
            rec.x_safety_stock_input_ids = [(2, line.id) for line in rec.x_safety_stock_input_ids]

    def export_safety_stock_input_xlsx(self):
        return self.env.ref('cus_procurement_tool.report_safety_stock_input_xlsx').report_action(self)

    @api.model
    def create(self, vals):
        if vals.get('x_name', _('New')) == _('New'):
            vals['x_name'] = self.env['ir.sequence'].next_by_code('procurement.cycle') or 'New'
        res = super(ProcurementCycle, self).create(vals)
        self.env['procurement.cycle.cart.details'].create({
            'x_name': 'Template Cart',
            'x_partner_id': 1781, # Anonymous Vendor
            'x_proc_cycle_id': res.id,
            'x_journal_id': 32, # Dummy Journal (USD)
            'x_currency_id': 2, # USD
        })
        return res

    def get_demand_batch_mos(self):
        for rec in self:
            order_ids = self.env['mrp.production'].search([
                ('x_demand_batch_id', 'in', rec.x_demand_batch_ids.ids),
                ('x_manufacturing_type', '=', 'proc'), ('state', 'not in', ('draft', 'done', 'cancel')),
            ]).ids
            rec.x_manufacturing_ids = [(6, 0, order_ids)]

    def action_view_demand_mos(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('id', 'in', self.x_manufacturing_ids.ids)]
        return action

    def action_view_component_list(self):
        action = self.env.ref('cus_procurement_tool.action_view_component_list').read()[0]
        action['context'] = {'default_x_proc_cycle_id': self.id}
        action['domain'] = [('x_proc_cycle_id', '=', self.id)]
        return action

    def action_procurement_cycle_cart_details(self):
        action = self.env.ref('cus_procurement_tool.action_procurement_cycle_cart_details').read()[0]
        action['context'] = {'default_x_proc_cycle_id': self.id}
        action['domain'] = [('x_proc_cycle_id', '=', self.id)]
        return action

    def component_list_quantities_action(self):
        action = self.env.ref('cus_procurement_tool.component_list_quantities_action').read()[0]
        action['context'] = {'search_default_component': True}
        action['domain'] = [('x_component_id.x_proc_cycle_id', '=', self.id)]
        return action

    def action_view_purchase_orders(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.x_cart_ids.mapped('x_purchase_id').ids)]
        return action

    def action_view_receipts(self):
        action = self.env.ref('customizations.action_picking_tree_receipts').read()[0]
        action['domain'] = [('purchase_id', 'in', self.x_cart_ids.mapped('x_purchase_id').ids)]
        return action

    def action_view_consolidations(self):
        action = self.env.ref('cus_logistics_tracking.action_consolidation_tracking').read()[0]
        action['domain'] = [('x_purchase_ids', 'in', self.x_cart_ids.mapped('x_purchase_id').ids)]
        return action

    # MO Demand
    def get_short_part_details(self):
        for rec in self:
            for order in rec.x_manufacturing_ids:
                for move in order.picking_ids.filtered(
                    lambda l: l.state in ('confirmed', 'assigned')
                ).mapped('move_lines').filtered(
                    lambda l: l.product_id.x_goods_type == 'rm' and l.product_uom_qty > l.reserved_availability
                ):
                    short_component_id = rec.x_short_component_ids.filtered(
                        lambda l: l.x_product_id.id == move.product_id.id
                    )
                    if short_component_id:
                        if order.id in short_component_id.x_demand_detail_ids.mapped('x_manufacturing_id').ids:
                            continue
                        short_component_id.x_required_qty += move.product_uom_qty
                        short_component_id.x_missing_qty += move.product_uom_qty - move.reserved_availability
                        if short_component_id.x_missing_qty > short_component_id.x_qty_available:
                            short_component_id.x_status = 'new_demand'
                        # Demand Details
                        for demand in order.x_mrp_demand_ids:
                            short_component_id.x_demand_detail_ids = [(0, 0, {
                                'x_product_id': order.product_id.id,
                                'x_type': demand.x_demand_type,
                                'x_sale_id': demand.x_sale_id.id if demand.x_demand_type == 'sale' else False,
                                'x_quantity': round(move.product_uom_qty * demand.x_quantity / order.product_qty, 2),
                                'x_uom_id': move.product_uom.id,
                                'x_manufacturing_id': order.id,
                            })]
                        continue

                    # Demand Details
                    demand_detail_ids = []
                    for demand in order.x_mrp_demand_ids:
                        demand_detail_ids.append((0, 0, {
                            'x_product_id': order.product_id.id,
                            'x_type': demand.x_demand_type,
                            'x_sale_id': demand.x_sale_id.id if demand.x_demand_type == 'sale' else False,
                            'x_quantity': round(move.product_uom_qty * demand.x_quantity / order.product_qty, 2),
                            'x_uom_id': move.product_uom.id,
                            'x_manufacturing_id': order.id,
                        }))

                    # Part Purchase History
                    purchase_history_ids = []
                    for history in move.product_id.x_purchase_history_ids.filtered(
                            lambda l: l.x_partner_id.id not in (30, 1992)
                    ):
                        purchase_history_ids.append((0, 0, {
                            'x_relation': 'orig',
                            'x_product_id': history.x_product_id.product_variant_id.id,
                            'x_vendor_id': history.x_partner_id.id,
                            'x_order_date': history.x_order_date,
                            'x_purchase_id': history.x_order_id.id,
                            'x_quantity': history.x_product_qty,
                            'x_uom_id': history.x_product_uom_id.id,
                            'x_currency_id': history.x_order_id.currency_id.id,
                            'x_unit_price': round(history.x_unit_price, 2),
                            'x_subtotal': round(history.x_subtotal, 2),
                        }))

                    # Alternates Purchase History
                    for line in move.product_id.x_taraz_part_number_id.x_alternate_ids:
                        if line.x_product_id.id != move.product_id.product_tmpl_id.id:
                            for history in line.x_product_id.x_purchase_history_ids.filtered(
                                    lambda l: l.x_partner_id.id not in (30, 1992)
                            ):
                                purchase_history_ids.append((0, 0, {
                                    'x_relation': 'alt',
                                    'x_product_id': history.x_product_id.product_variant_id.id,
                                    'x_vendor_id': history.x_partner_id.id,
                                    'x_order_date': history.x_order_date,
                                    'x_purchase_id': history.x_order_id.id,
                                    'x_quantity': history.x_product_qty,
                                    'x_uom_id': history.x_product_uom_id.id,
                                    'x_currency_id': history.x_order_id.currency_id.id,
                                    'x_unit_price': round(history.x_unit_price, 2),
                                    'x_subtotal': round(history.x_subtotal, 2),
                                }))

                    # Compromised Purchase History
                    for line in move.product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                            'x_compromised_id').mapped('x_alternate_ids'):
                        if line.x_product_id.id != move.product_id.product_tmpl_id.id:
                            for history in line.x_product_id.x_purchase_history_ids.filtered(
                                    lambda l: l.x_partner_id.id not in (30, 1992)
                            ):
                                purchase_history_ids.append((0, 0, {
                                    'x_relation': 'comp',
                                    'x_product_id': history.x_product_id.product_variant_id.id,
                                    'x_vendor_id': history.x_partner_id.id,
                                    'x_order_date': history.x_order_date,
                                    'x_purchase_id': history.x_order_id.id,
                                    'x_quantity': history.x_product_qty,
                                    'x_uom_id': history.x_product_uom_id.id,
                                    'x_currency_id': history.x_order_id.currency_id.id,
                                    'x_unit_price': round(history.x_unit_price, 2),
                                    'x_subtotal': round(history.x_subtotal, 2),
                                }))

                    quarterly_consumption = move.product_id.x_quarterly_consumption_ids.ids
                    quarterly_consumption += move.product_id.x_taraz_part_number_id.x_alternate_ids.mapped(
                        'x_product_id'
                    ).x_quarterly_consumption_ids.ids
                    quarterly_consumption += move.product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                        'x_compromised_id'
                    ).mapped('x_alternate_ids').mapped('x_product_id').x_quarterly_consumption_ids.ids

                    # Consumption
                    consumption_ids = []
                    input_bom_ids = self.env['bom.tool'].search([('state', '=', 'active')]).mapped('x_base_bom_id')
                    for bom in input_bom_ids.filtered(
                        lambda l: move.product_id.product_tmpl_id.id in l.x_bom_line_ids.filtered(
                            lambda bl: not bl.x_dnp and not bl.x_design_deleted and not bl.x_deleted
                        ).mapped('x_product_id').ids
                    ):
                        usage_count = sum(bom.x_bom_line_ids.filtered(
                            lambda l: l.x_product_id.id == move.product_id.product_tmpl_id.id
                        ).mapped('x_real_quantity'))

                        consumption_ids.append((0, 0, {
                            'x_product_id': bom.x_product_id.product_variant_id.id,
                            'x_quantity': usage_count,
                            'x_uom_id': bom.x_product_id.uom_id.id,
                        }))

                    rec.x_short_component_ids = [(0, 0, {
                        'x_product_id': move.product_id.id,
                        'x_required_qty': move.product_uom_qty,
                        'x_missing_qty': move.product_uom_qty - move.reserved_availability,

                        'x_demand_detail_ids': demand_detail_ids,
                        'x_purchase_history_ids': purchase_history_ids,
                        'x_quarterly_consumption_ids': quarterly_consumption,
                        'x_consumption_ids': consumption_ids,
                    })]

    # Internal Demand
    def get_short_part_details_im(self):
        for rec in self:
            for line in rec.x_manual_proc_demand_lines_ids.filtered(lambda l: l.x_product_qty > 0):
                short_component_id = rec.x_short_component_ids.filtered(
                    lambda l: l.x_product_id.id == line.x_product_id.id
                )
                if short_component_id:
                    if line.id in short_component_id.x_demand_detail_ids.mapped('x_internal_demand_id').ids:
                        continue
                    short_component_id.x_required_qty += line.x_product_qty
                    short_component_id.x_missing_qty += line.x_product_qty
                    if short_component_id.x_missing_qty < short_component_id.x_qty_available:
                        short_component_id.x_status = 'new_demand'
                    # Demand Details
                    short_component_id.x_demand_detail_ids = [(0, 0, {
                        'x_type': 'internal',
                        'x_internal_demand_id': line.id,
                        'x_deadline': line.x_date,
                        'x_quantity': round(line.x_product_qty, 2),
                        'x_uom_id': line.x_uom_id.id,
                    })]
                    line.x_manual_proc_demand_id.x_status = 'in_progress'
                    continue
                # Demand Details
                demand_detail_ids = [(0, 0, {
                    'x_type': 'internal',
                    'x_internal_demand_id': line.id,
                    'x_deadline': line.x_date,
                    'x_quantity': round(line.x_product_qty, 2),
                    'x_uom_id': line.x_uom_id.id,
                })]

                # Part Purchase History
                purchase_history_ids = []
                for history in line.x_product_id.x_purchase_history_ids.filtered(
                        lambda l: l.x_partner_id.id not in (30, 1992)
                ):
                    purchase_history_ids.append((0, 0, {
                        'x_relation': 'orig',
                        'x_product_id': history.x_product_id.product_variant_id.id,
                        'x_vendor_id': history.x_partner_id.id,
                        'x_order_date': history.x_order_date,
                        'x_purchase_id': history.x_order_id.id,
                        'x_quantity': history.x_product_qty,
                        'x_uom_id': history.x_product_uom_id.id,
                        'x_currency_id': history.x_order_id.currency_id.id,
                        'x_unit_price': round(history.x_unit_price, 2),
                        'x_subtotal': round(history.x_subtotal, 2),
                    }))

                # Alternates Purchase History
                for alternate in line.x_product_id.x_taraz_part_number_id.x_alternate_ids:
                    if alternate.x_product_id.id != line.x_product_id.product_tmpl_id.id:
                        for history in alternate.x_product_id.x_purchase_history_ids.filtered(
                                lambda l: l.x_partner_id.id not in (30, 1992)
                        ):
                            purchase_history_ids.append((0, 0, {
                                'x_relation': 'alt',
                                'x_product_id': history.x_product_id.product_variant_id.id,
                                'x_vendor_id': history.x_partner_id.id,
                                'x_order_date': history.x_order_date,
                                'x_purchase_id': history.x_order_id.id,
                                'x_quantity': history.x_product_qty,
                                'x_uom_id': history.x_product_uom_id.id,
                                'x_currency_id': history.x_order_id.currency_id.id,
                                'x_unit_price': round(history.x_unit_price, 2),
                                'x_subtotal': round(history.x_subtotal, 2),
                            }))

                # Compromised Purchase History
                for compromised in line.x_product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                        'x_compromised_id').mapped('x_alternate_ids'):
                    if compromised.x_product_id.id != line.x_product_id.product_tmpl_id.id:
                        for history in compromised.x_product_id.x_purchase_history_ids.filtered(
                                lambda l: l.x_partner_id.id not in (30, 1992)
                        ):
                            purchase_history_ids.append((0, 0, {
                                'x_relation': 'comp',
                                'x_product_id': history.x_product_id.product_variant_id.id,
                                'x_vendor_id': history.x_partner_id.id,
                                'x_order_date': history.x_order_date,
                                'x_purchase_id': history.x_order_id.id,
                                'x_quantity': history.x_product_qty,
                                'x_uom_id': history.x_product_uom_id.id,
                                'x_currency_id': history.x_order_id.currency_id.id,
                                'x_unit_price': round(history.x_unit_price, 2),
                                'x_subtotal': round(history.x_subtotal, 2),
                            }))

                quarterly_consumption = line.x_product_id.x_quarterly_consumption_ids.ids
                quarterly_consumption += line.x_product_id.x_taraz_part_number_id.x_alternate_ids.mapped(
                    'x_product_id'
                ).x_quarterly_consumption_ids.ids
                quarterly_consumption += line.x_product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                    'x_compromised_id'
                ).mapped('x_alternate_ids').mapped('x_product_id').x_quarterly_consumption_ids.ids

                # Consumption
                consumption_ids = []
                input_bom_ids = self.env['bom.tool'].search([('state', '=', 'active')]).mapped('x_base_bom_id')
                for bom in input_bom_ids.filtered(
                    lambda l: line.x_product_id.product_tmpl_id.id in l.x_bom_line_ids.filtered(
                        lambda bl: not bl.x_dnp and not bl.x_design_deleted and not bl.x_deleted
                    ).mapped('x_product_id').ids
                ):
                    usage_count = sum(bom.x_bom_line_ids.filtered(
                        lambda l: l.x_product_id.id == line.x_product_id.product_tmpl_id.id
                    ).mapped('x_real_quantity'))

                    consumption_ids.append((0, 0, {
                        'x_product_id': bom.x_product_id.product_variant_id.id,
                        'x_quantity': usage_count,
                        'x_uom_id': bom.x_product_id.uom_id.id,
                    }))

                rec.x_short_component_ids = [(0, 0, {
                    'x_product_id': line.x_product_id.id,
                    'x_required_qty': line.x_product_qty,
                    'x_missing_qty': line.x_product_qty,

                    'x_demand_detail_ids': demand_detail_ids,
                    'x_purchase_history_ids': purchase_history_ids,
                    'x_quarterly_consumption_ids': quarterly_consumption,
                    'x_consumption_ids': consumption_ids,
                })]
                line.x_manual_proc_demand_id.x_status = 'in_progress'

    # Safety Stock
    def get_short_part_details_ss(self):
        for rec in self:
            for line in rec.x_safety_stock_input_ids.filtered(lambda l: l.x_quantity > 0):
                short_component_id = rec.x_short_component_ids.filtered(
                    lambda l: l.x_product_id.id == line.x_product_id.id
                )
                if short_component_id:
                    safety_stock_demand_id = short_component_id.x_demand_detail_ids.filtered(
                        lambda l: l.x_type == 'safety_stock'
                    )
                    if len(safety_stock_demand_id) > 1:
                        if sum(safety_stock_demand_id.mapped('x_quantity')) != round(line.x_quantity, 2):
                            short_component_id.x_required_qty -= sum(safety_stock_demand_id.mapped('x_quantity'))
                            short_component_id.x_required_qty += line.x_quantity
                            short_component_id.x_status = 'new_demand'

                            safety_stock_demand_id[0].x_safety_stock_line_id = line.id
                            safety_stock_demand_id[0].x_quantity = round(line.x_quantity, 2)
                            safety_stock_demand_id[0].x_uom_id = line.x_uom_id.id

                            short_component_id.x_demand_detail_ids = [(2, stock.id) for stock in safety_stock_demand_id[1:]]
                            continue
                        else:
                            continue
                    elif (safety_stock_demand_id.x_quantity != round(line.x_quantity, 2)
                          or safety_stock_demand_id.x_uom_id.id != line.x_uom_id.id):
                        short_component_id.x_required_qty -= safety_stock_demand_id.x_quantity
                        short_component_id.x_required_qty += line.x_quantity
                        short_component_id.x_status = 'new_demand'

                        safety_stock_demand_id.x_safety_stock_line_id = line.id
                        safety_stock_demand_id.x_quantity = round(line.x_quantity, 2)
                        safety_stock_demand_id.x_uom_id = line.x_uom_id.id
                        continue
                    else:
                        # Demand Details
                        short_component_id.x_demand_detail_ids = [(0, 0, {
                            'x_type': 'safety_stock',
                            'x_safety_stock_line_id': line.id,
                            'x_deadline': False,
                            'x_quantity': round(line.x_quantity, 2),
                            'x_uom_id': line.x_uom_id.id,
                        })]
                        continue
                # Demand Details
                demand_detail_ids = [(0, 0, {
                    'x_type': 'safety_stock',
                    'x_safety_stock_line_id': line.id,
                    'x_deadline': False,
                    'x_quantity': round(line.x_quantity, 2),
                    'x_uom_id': line.x_uom_id.id,
                })]

                # Part Purchase History
                purchase_history_ids = []
                for history in line.x_product_id.x_purchase_history_ids.filtered(
                        lambda l: l.x_partner_id.id not in (30, 1992)
                ):
                    purchase_history_ids.append((0, 0, {
                        'x_relation': 'orig',
                        'x_product_id': history.x_product_id.product_variant_id.id,
                        'x_vendor_id': history.x_partner_id.id,
                        'x_order_date': history.x_order_date,
                        'x_purchase_id': history.x_order_id.id,
                        'x_quantity': history.x_product_qty,
                        'x_uom_id': history.x_product_uom_id.id,
                        'x_currency_id': history.x_order_id.currency_id.id,
                        'x_unit_price': round(history.x_unit_price, 2),
                        'x_subtotal': round(history.x_subtotal, 2),
                    }))

                # Alternates Purchase History
                for alternate in line.x_product_id.x_taraz_part_number_id.x_alternate_ids:
                    if alternate.x_product_id.id != line.x_product_id.product_tmpl_id.id:
                        for history in alternate.x_product_id.x_purchase_history_ids.filtered(
                                lambda l: l.x_partner_id.id not in (30, 1992)
                        ):
                            purchase_history_ids.append((0, 0, {
                                'x_relation': 'alt',
                                'x_product_id': history.x_product_id.product_variant_id.id,
                                'x_vendor_id': history.x_partner_id.id,
                                'x_order_date': history.x_order_date,
                                'x_purchase_id': history.x_order_id.id,
                                'x_quantity': history.x_product_qty,
                                'x_uom_id': history.x_product_uom_id.id,
                                'x_currency_id': history.x_order_id.currency_id.id,
                                'x_unit_price': round(history.x_unit_price, 2),
                                'x_subtotal': round(history.x_subtotal, 2),
                            }))

                # Compromised Purchase History
                for compromised in line.x_product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                        'x_compromised_id').mapped('x_alternate_ids'):
                    if compromised.x_product_id.id != line.x_product_id.product_tmpl_id.id:
                        for history in compromised.x_product_id.x_purchase_history_ids.filtered(
                                lambda l: l.x_partner_id.id not in (30, 1992)
                        ):
                            purchase_history_ids.append((0, 0, {
                                'x_relation': 'comp',
                                'x_product_id': history.x_product_id.product_variant_id.id,
                                'x_vendor_id': history.x_partner_id.id,
                                'x_order_date': history.x_order_date,
                                'x_purchase_id': history.x_order_id.id,
                                'x_quantity': history.x_product_qty,
                                'x_uom_id': history.x_product_uom_id.id,
                                'x_currency_id': history.x_order_id.currency_id.id,
                                'x_unit_price': round(history.x_unit_price, 2),
                                'x_subtotal': round(history.x_subtotal, 2),
                            }))

                quarterly_consumption = line.x_product_id.x_quarterly_consumption_ids.ids
                quarterly_consumption += line.x_product_id.x_taraz_part_number_id.x_alternate_ids.mapped(
                    'x_product_id'
                ).x_quarterly_consumption_ids.ids
                quarterly_consumption += line.x_product_id.x_taraz_part_number_id.x_compromised_ids.mapped(
                    'x_compromised_id'
                ).mapped('x_alternate_ids').mapped('x_product_id').x_quarterly_consumption_ids.ids

                # Consumption
                consumption_ids = []
                input_bom_ids = self.env['bom.tool'].search([('state', '=', 'active')]).mapped('x_base_bom_id')
                for bom in input_bom_ids.filtered(
                    lambda l: line.x_product_id.product_tmpl_id.id in l.x_bom_line_ids.filtered(
                        lambda bl: not bl.x_dnp and not bl.x_design_deleted and not bl.x_deleted
                    ).mapped('x_product_id').ids
                ):
                    usage_count = sum(bom.x_bom_line_ids.filtered(
                        lambda l: l.x_product_id.id == line.x_product_id.product_tmpl_id.id
                    ).mapped('x_real_quantity'))

                    consumption_ids.append((0, 0, {
                        'x_product_id': bom.x_product_id.product_variant_id.id,
                        'x_quantity': usage_count,
                        'x_uom_id': bom.x_product_id.uom_id.id,
                    }))

                rec.x_short_component_ids = [(0, 0, {
                    'x_product_id': line.x_product_id.id,
                    'x_required_qty': line.x_quantity,

                    'x_demand_detail_ids': demand_detail_ids,
                    'x_purchase_history_ids': purchase_history_ids,
                    'x_quarterly_consumption_ids': quarterly_consumption,
                    'x_consumption_ids': consumption_ids,
                })]

    def mark_as_done(self):
        for rec in self:
            rec.state = 'completed'

    def mark_as_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def mark_as_new(self):
        for rec in self:
            rec.state = 'new'

    def unlink(self):
        if self.state not in ('new', 'cancel'):
            raise UserError("If you want to delete Procurement Cycle then cancel it first!")
        self.x_safety_stock_input_ids.unlink()
        self.x_short_component_ids.unlink()
        self.x_cart_ids.unlink()
        self.x_budget_ids.unlink()
        return super(ProcurementCycle, self).unlink()


class ProcurementCycleCartDetails(models.Model):
    _name = 'procurement.cycle.cart.details'
    _description = 'Procurement Cycle Cart Details'
    _rec_name = "x_name"

    x_name = fields.Char(string='Cart #', required=True)
    x_proc_cycle_id = fields.Many2one(comodel_name='procurement.cycle', string='Procurement Cycle', required=True)
    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor', required=True,
                                   context="{'res_partner_search_mode': 'supplier'}",
                                   domain="[('supplier_rank', '>', 0)]")
    x_journal_id = fields.Many2one(comodel_name='account.journal', string='Payment Method', required=True)
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=True,
                                    default=lambda self: self.x_partner_id.property_product_pricelist.currency_id)
    x_route_id = fields.Many2one(comodel_name='logistics.route', string='Route')
    x_purchase_type = fields.Selection(selection=[
        ('Local', 'Local'),
        ('Clearing', 'Clearing'),
        ('Forwarding', 'Forwarding'),
        ('Imported Goods', 'Imported Goods'),
        ('Shipping (Export)', 'Shipping (Export)'),
        ('Shipping (Self Pickup)', 'Shipping (Self Pickup)'),
    ], string="Purchase Type", required=False, )
    x_item_type = fields.Selection(selection=[
        ('Asset', 'Asset'),
        ('Expense', 'Expense'),
        ('Inventory', 'Inventory'),
        ('Landed Cost', 'Landed Cost'),
        ('Inventory & Asset', 'Inventory & Asset'),
        ('Cost of Freight Sold', 'Cost of Freight Sold'),
    ], string="Item Type", required=False, )
    x_purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    x_amount = fields.Float(string='Octopart Value', compute="_compute_cart_total_price", store=True)
    x_actual_value = fields.Float(string='Actual Value', compute="_compute_cart_actual_value", store=True)
    x_other_charges = fields.Float(string='Misc. Expense', required=False)
    x_total_value = fields.Float(string='Total Value', compute="_compute_cart_total_value", store=True)

    x_consolidation_ids = fields.Many2many(comodel_name='consolidation.tracking', string='Consolidations')

    x_status = fields.Selection(selection=[
        ('cart_on_hold', 'Cart On Hold'),
        ('cart_updated', 'Cart Updated'),
        ('cart_ordered', 'Cart Ordered'),
        ('shipped', 'Shipped'),
        ('partially_shipped', 'Partially Shipped'),
        ('received', 'Received'),
    ], string='Status', )

    x_comment = fields.Char(string='Comment', required=False)
    x_line_count = fields.Integer(string='Line Count', compute="_compute_line_count", store=True)
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')

    x_cart_url = fields.Char(string='Cart URL', required=False)

    x_component_ids = fields.One2many(
        comodel_name='component.list.quantities',
        inverse_name="x_prc_cart_id",
        string='Cart Components')

    x_update_component_status = fields.Boolean(compute="_compute_component_status")

    x_budget_ids = fields.Many2many(
        comodel_name='procurement.cycle.budget.details',
        relation="cycle_cart_details_budget_details_rel",
        column1="cart_details_id",
        column2="budget_details_id",
        string='Budgets',
        compute="compute_budget_ids",
        store=True,
        readonly=False)

    @api.onchange('x_partner_id')
    def onchange_x_partner_id(self):
        for rec in self:
            rec.x_component_ids.update({'x_partner_id': rec.x_partner_id.id})

    def remove_cart_lines(self):
        for rec in self:
            rec.x_component_ids.update({'x_prc_cart_id': False})

    @api.depends('x_proc_cycle_id.x_budget_ids')
    def compute_budget_ids(self):
        for rec in self:
            rec.x_budget_ids = [(6, 0, rec.x_proc_cycle_id.x_budget_ids.ids)]

    @api.depends('x_component_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.x_line_count = len(rec.x_component_ids)

    @api.depends('x_status')
    def _compute_component_status(self):
        for rec in self:
            if rec.x_status:
                rec.x_component_ids.mapped('x_component_id').write({'x_status': rec.x_status})
            rec.x_update_component_status = True

    @api.depends('x_component_ids', 'x_component_ids.x_ext_price')
    def _compute_cart_total_price(self):
        for rec in self:
            rec.x_amount = sum(rec.x_component_ids.mapped('x_ext_price'))

    @api.depends('x_component_ids', 'x_component_ids.x_actual_ext_price')
    def _compute_cart_actual_value(self):
        for rec in self:
            rec.x_actual_value = sum(rec.x_component_ids.mapped('x_actual_ext_price'))

    @api.depends('x_actual_value', 'x_other_charges')
    def _compute_cart_total_value(self):
        for rec in self:
            rec.x_total_value = rec.x_actual_value + rec.x_other_charges

    def download_cart_xlsx(self):
        return self.env.ref('cus_procurement_tool.report_download_cart_xlsx').report_action(self)

    def create_purchase_order(self):
        for rec in self:
            if rec.x_purchase_id:
                raise UserError('Purchase Order already created for this cart!')
            elif not rec.x_component_ids:
                raise UserError('No components found in this cart!')

            vals = {
                'x_internal_ref': rec.x_name,
                'partner_id': rec.x_partner_id.id,
                'x_purchase_type': rec.x_purchase_type,
                'x_item_type': rec.x_item_type,
                'date_order': fields.datetime.now(),
                'company_id': self.env.company.id,
                'payment_term_id': self.env.ref('customizations.account_payment_100_percent_advance').id,
                'x_payment_method': rec.x_journal_id.id,
                'currency_id': rec.x_currency_id.id or rec.x_partner_id.property_product_pricelist.currency_id.id,
                'x_proc_cycle_id': rec.x_proc_cycle_id.id,
                'order_line': [],
                'x_demand_list_ids': rec.x_component_ids.mapped('x_component_id').mapped('x_demand_detail_ids').ids,
            }

            for line in rec.x_component_ids:
                vals['order_line'].append((0, 0, {
                    'product_id': line.x_product_id.id,
                    'name': line.x_product_id.x_short_description or line.x_product_id.name,
                    'date_planned': fields.datetime.now(),
                    'product_qty': line.x_eoq,
                    'product_uom': line.x_uom_id.id,
                    'price_unit': line.x_actual_unit_price,
                }))

            purchase_id = self.env['purchase.order'].create(vals)
            rec.x_purchase_id = purchase_id.id
            rec.x_status = 'cart_ordered'

    def unlink(self):
        if self.x_component_ids:
            raise UserError("You can't delete cart with components!")
        return super(ProcurementCycleCartDetails, self).unlink()


class ProcurementCycleBudgetDetails(models.Model):
    _name = 'procurement.cycle.budget.details'
    _description = 'Procurement Cycle Budget Details'
    _rec_name = "display_name"

    x_proc_cycle_id = fields.Many2one('procurement.cycle', string='Procurement Cycle')
    x_journal_id = fields.Many2one('account.journal', string='Payment Method')
    x_cart_ids = fields.Many2many(
        comodel_name='procurement.cycle.cart.details',
        relation="cycle_budget_details_cart_details_rel",
        column1="budget_details_id",
        column2="cart_details_id",
        string='Carts')
    x_budget = fields.Float(string='Budget', required=False)
    x_consumed = fields.Float(string='Consumed', compute="_compute_consumed", store=True, required=False)
    x_balance = fields.Float(string='Balance', compute="_compute_balance", store=True, required=False)

    @api.depends('x_cart_ids', 'x_cart_ids.x_actual_value', 'x_cart_ids.x_other_charges')
    def _compute_consumed(self):
        for rec in self:
            rec.x_consumed = sum(rec.x_cart_ids.mapped('x_actual_value')) + sum(rec.x_cart_ids.mapped('x_other_charges'))

    @api.depends('x_budget', 'x_consumed')
    def _compute_balance(self):
        for rec in self:
            rec.x_balance = rec.x_budget - rec.x_consumed

