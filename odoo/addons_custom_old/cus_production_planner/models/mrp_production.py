from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("*__addons_custom__*")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_bom_tool_id = fields.Many2one(related="product_id.x_bom_tool_id")

    x_bom_tool_status = fields.Selection(selection=[
        ('defined', 'BoM is Defined'),
        ('not_defined', 'BoM not Defined'),
        ('to_be_review', 'BoM to be review'),
    ], string="BoM Tool Status", tracking=True, compute="_compute_bom_tool_status", store=True, copy=False)

    x_bom_tool_days_not_defined = fields.Char(string="BoM not Defined Days", copy=False)
    x_bom_tool_days_to_be_review = fields.Char(string="BoM to be review Days", copy=False)
    x_bom_tool_days_defined = fields.Char(string="BoM Defined Days", copy=False)

    x_goods_type = fields.Selection(related="product_id.x_goods_type")
    x_manufacturing_type = fields.Selection(selection=[
        ('proc', 'Procurement'), ('mrp', 'Manufacturing'),
    ], string='Order Type', required=True, default='proc', tracking=True)

    # 'Proc. Required' or 'Can be Manufactured' On Sale Order Creation or Stock Build Rule Triggering
    # 'Proc. In Progress' when MO is called in Proc. Tool
    # 'Stock On Order' when stock order is Placed through Proc. Tool
    # 'In Production' When Picking is Validated
    # 'Manufactured' When MO is validated
    # 'In QC' When QC checkbox is True
    x_production_status = fields.Selection(selection=[
        ('new', 'New'),
        ('bom_tool_not_defined', 'BOM Tool not Defined'),
        ('bom_to_be_review', 'BOM to be review'),
        ('proc_required', 'Proc. Required'),
        ('proc_in_progress', 'Proc. In Progress'),
        ('stock_on_order', 'Stock On Order'),
        ('can_be_manufactured_partial', 'Can be Manufactured (Partial)'),
        ('can_be_manufactured_full', 'Can be Manufactured (Complete)'),
        ('in_production', 'In Production'),
        ('ready', 'Manufactured'),
        ('in_quality_control', 'In QC'),
        ('done', 'Complete'),
    ], string='Production Status', default='new', tracking=True)

    x_manufacture_components = fields.Boolean(string='Manufacture Components',
                                              compute="_compute_manufacture_components", store=False)

    x_demand_batch_id = fields.Many2one(comodel_name='mrp.procurement.batch', string='Demand Batch', required=False)
    x_master_order_id = fields.Many2one(comodel_name='mrp.production', string='Master Order #', required=False)

    x_mrp_demand_ids = fields.One2many(
        comodel_name='mrp.source.details', inverse_name='x_manufacturing_id', string='Source Details', required=False
    )

    x_compute_serial_numbers = fields.Boolean(compute="compute_serial_numbers")

    x_type = fields.Selection(related="bom_id.type")
    x_bom_line_ids = fields.One2many(related="bom_id.bom_line_ids", readonly=False)

    x_compute_bom_line_status = fields.Boolean(compute="compute_bom_line_status")

    x_folder_name = fields.Char(string='Folder Name', compute="_compute_folder_name", store=True, copy=False)

    x_planned_start_date = fields.Datetime(string='Planned Start Date', tracking=True)
    x_planned_finish_date = fields.Datetime(string='Planned Finish Date', tracking=True)

    x_compute_date_deadline = fields.Boolean(compute='_compute_date_deadline')
    x_compute_date_planned_start = fields.Boolean(compute='_compute_master_date_planned_start')

    @api.onchange('x_planned_start_date')
    def update_picking_planned_start_date(self):
        for rec in self:
            if rec.x_planned_start_date and rec.x_planned_finish_date:
                if rec.x_planned_finish_date < rec.x_planned_start_date:
                    rec.x_planned_finish_date = rec.x_planned_start_date

    @api.onchange('x_planned_finish_date')
    def update_picking_planned_start_date(self):
        for rec in self:
            if rec.x_planned_start_date and rec.x_planned_finish_date:
                if rec.x_planned_finish_date < rec.x_planned_start_date:
                    rec.x_planned_start_date = rec.x_planned_finish_date

    @api.onchange('x_manufacturing_type')
    def update_picking_manufacturing_type(self):
        for rec in self:
            self.env['stock.picking'].search([
                ('origin', 'ilike', rec.name), ('state', 'not in', ('done', 'cancel')),
            ]).write({
                'x_manufacturing_type': rec.x_manufacturing_type,
            })

    def button_plan(self):
        for rec in self:
            if rec.x_manufacturing_type == 'proc':
                rec.x_manufacturing_type = 'mrp'
            self.env['stock.picking'].search([
                ('origin', 'ilike', rec.name), ('state', 'not in', ('done', 'cancel')),
            ]).write({
                'x_manufacturing_type': rec.x_manufacturing_type,
            })
        return super(MrpProduction, self).button_plan()

    def action_view_manufacturing_raw_material(self):
        self.ensure_one()
        manufacturing_ids = self.x_child_ids.mapped('child_manufacturing_id')
        manufacturing_ids |= manufacturing_ids.mapped('x_child_ids').mapped('child_manufacturing_id')
        manufacturing_ids |= manufacturing_ids.mapped('x_child_ids').mapped('child_manufacturing_id')
        manufacturing_ids |= manufacturing_ids.mapped('x_child_ids').mapped('child_manufacturing_id')
        manufacturing_ids |= manufacturing_ids.mapped('x_child_ids').mapped('child_manufacturing_id')

        action = self.env.ref('cus_production_planner.action_manufacturing_raw_material_cus_production_planner').read()[
            0]
        move_raw_ids = self.move_raw_ids.filtered(lambda l: 'Raw Material' in l.product_id.categ_id.name)
        move_raw_ids |= manufacturing_ids.mapped('move_raw_ids').filtered(
            lambda l: 'Raw Material' in l.product_id.categ_id.name)
        action['domain'] = [('id', 'in', move_raw_ids.ids)]
        return action

    @api.depends('product_id', 'product_id.x_bom_tool_id', 'product_id.x_bom_tool_id.state')
    def _compute_bom_tool_status(self):
        for rec in self:
            if rec.state == 'draft':
                if not rec.product_id.x_bom_tool_id:
                    rec.x_bom_tool_status = 'not_defined'
                elif rec.product_id.x_bom_tool_id.state != 'active':
                    rec.x_bom_tool_status = 'to_be_review'
                else:
                    rec.x_bom_tool_status = 'defined'

    @api.model
    def compute_bom_tool_days(self):
        recs = self.env['mrp.production'].search([('state', '=', 'draft')])
        for rec in recs:
            if rec.state != 'draft':
                continue
            days_not_defined = int(
                rec.x_bom_tool_days_not_defined.replace('d', '')) if rec.x_bom_tool_days_not_defined else 0
            days_to_be_review = int(
                rec.x_bom_tool_days_to_be_review.replace('d', '')) if rec.x_bom_tool_days_to_be_review else 0
            days_defined = 0
            if rec.create_date and rec.x_bom_tool_status == 'not_defined':
                days_not_defined = (fields.Datetime.now() - rec.create_date).days
            elif rec.create_date and rec.x_bom_tool_status == 'to_be_review':
                days_to_be_review = int((fields.Datetime.now() - rec.create_date).days) - days_not_defined
            elif rec.create_date and rec.x_bom_tool_status == 'defined':
                days_defined = int(
                    (fields.Datetime.now() - rec.create_date).days) - days_not_defined - days_to_be_review
            rec.x_bom_tool_days_not_defined = '%sd' % days_not_defined
            rec.x_bom_tool_days_to_be_review = '%sd' % days_to_be_review
            rec.x_bom_tool_days_defined = '%sd' % days_defined

    @api.depends('x_planned_finish_date')
    def _compute_master_date_planned_start(self):
        for rec in self:
            rec.x_mrp_demand_ids.mapped('x_master_order_id').compute_date_planned_start()
            rec.x_compute_date_planned_start = True

    def compute_date_planned_start(self):
        for rec in self:
            child_demand_ids = self.env['mrp.source.details'].search([
                ('x_master_order_id', '=', rec.id)
            ]).mapped('x_manufacturing_id').search([
                ('state', 'not in', ('done', 'cancel')), ('x_planned_finish_date', '!=', False)
            ]).mapped('x_planned_finish_date')
            if len(child_demand_ids) > 1:
                rec.x_planned_start_date = max(child_demand_ids)
            elif len(child_demand_ids) == 1:
                rec.x_planned_start_date = child_demand_ids[0]

    def action_view_picking_lines(self):
        self.ensure_one()
        self.env['stock.move'].search([
            ('product_uom_qty', '>', 0),
            '|', ('picking_id.name', 'ilike', 'WH/PC/'), ('picking_id.name', 'ilike', 'WTR/PC/'),
            ('state', 'in', ('confirmed', 'partially_available')),
        ]).get_prc_details()
        action = self.env.ref('cus_production_planner.short_parts_manufacturing_stock_move_action').read()[0]
        action['context'] = {
            'search_default_raw_material': 1,
            'search_default_origin': self.name,
        }
        return action

    @api.depends(
        'x_mrp_demand_ids',
        'x_mrp_demand_ids.x_picking_id',
        'x_mrp_demand_ids.x_picking_id.state',
        'x_mrp_demand_ids.x_picking_id.x_deadline',
    )
    def _compute_date_deadline(self):
        for rec in self:
            date_deadline = [
                deadline for deadline in rec.x_mrp_demand_ids.mapped('x_picking_id').filtered(
                    lambda p: p.state not in ('done', 'cancel')
                ).mapped('x_deadline') if deadline
            ]
            if len(date_deadline) > 1:
                rec.date_deadline = min(date_deadline)
            elif len(date_deadline) == 1:
                rec.date_deadline = date_deadline[0]
            else:
                rec.date_deadline = False
            rec.x_compute_date_deadline = True

    @api.depends('name', 'product_id', 'product_qty', 'x_bom_tool_id', 'company_id')
    def _compute_folder_name(self):
        for rec in self:
            company = 'TarazPK' if rec.company_id.id == 1 else 'TarazTR'
            rec.x_folder_name = '%s - %s - %s - Qty:%s - %s' % (
                rec.name, company, rec.product_id.name, rec.product_qty, rec.x_bom_tool_id.x_name
            )

    @api.depends('move_raw_ids', 'move_raw_ids.state')
    def compute_bom_line_status(self):
        for rec in self:
            for move in rec.move_raw_ids:
                if move.state in ('waiting', 'partially_available', 'assigned', 'done'):
                    move.bom_line_id.x_part_status = move.state
            rec.x_compute_bom_line_status = True

    @api.onchange('product_qty')
    def update_demand_details(self):
        for rec in self:
            source_qty = sum(rec.x_mrp_demand_ids.filtered(
                lambda l: l.x_sale_id or l.x_demand_type == 'internal'
            ).mapped('x_quantity'))
            stock_qty = rec.product_qty - source_qty

            free_qty = rec.product_id.free_qty - sum(rec.x_mrp_demand_ids.filtered(
                lambda l: l.x_child_product_id.id == rec.product_id.id
            ).mapped('x_reserved'))
            free_qty = free_qty if free_qty > 0 else 0

            required_qty = stock_qty if not free_qty else stock_qty - free_qty if stock_qty > free_qty else 0

            stock_id = rec.x_mrp_demand_ids.filtered(lambda l: l.x_demand_type == 'stock' and not l.x_master_order_id)
            if stock_id and stock_qty >= 0:
                stock_id.write({
                    'x_demand': stock_qty,
                    'x_reserved': free_qty if stock_qty > free_qty else stock_qty,
                    'x_quantity': required_qty,
                })
            elif not stock_id and stock_qty >= 0:

                rec.x_mrp_demand_ids = [(0, 0, {
                    'x_child_product_id': rec.product_id.id,
                    'x_demand_type': 'stock',
                    'x_demand': stock_qty,
                    'x_reserved': free_qty if stock_qty > free_qty else stock_qty,
                    'x_quantity': required_qty,
                })]
            elif stock_qty < 0:
                raise UserError("Quantity must be equal or greater than demand quantity!")

    @api.depends('move_raw_ids')
    def _compute_manufacture_components(self):
        for rec in self:
            if rec.move_raw_ids.filtered(lambda l: l.product_id.x_goods_type in ('fg', 'sfg')):
                rec.x_manufacture_components = True
            else:
                rec.x_manufacture_components = False

    @api.depends('x_mrp_demand_ids', 'x_mrp_demand_ids.x_quantity')
    def compute_serial_numbers(self):
        for rec in self:
            rec.x_serial_numbers = [(2, line.id) for line in rec.x_serial_numbers]

            counter = 0
            serial_numbers = []
            for line in rec.x_mrp_demand_ids:
                for x in range(int(line.x_quantity)):
                    counter += 1
                    product_number = '0000%s' % counter
                    serial_number = '%s-%s' % ('MO%s' % rec.name[-5:], product_number[-4:])
                    serial_numbers.append((0, 0, {
                        'x_serial_number': serial_number,
                        'x_mega_mo_number': line.x_master_order_id.id,
                        'x_sale_order_number': line.x_sale_id.id,
                    }))
            rec.x_serial_numbers = serial_numbers
            rec.x_compute_serial_numbers = True

    def action_cancel_manufacturing_orders(self):
        picking_state = self.filtered(lambda order: order.state == 'confirmed').mapped('picking_ids').mapped('state')
        if 'done' in picking_state:
            raise UserError("You cannot cancel Production Order once it's Picking in Done")

        self.filtered(lambda order: order.state == 'confirmed').action_cancel()

    def action_cancel_manufacturing_orders_and_reserve_stock(self):
        self.action_cancel_manufacturing_orders()
        self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'internal'),
            ('origin', 'ilike', 'WH/MO/'), ('state', 'not in', ('draft', 'cancel', 'done'))
        ]).action_assign()

    def action_merge_manufacturing_orders(self):
        orders_to_merge = self.filtered(lambda order: order.state == 'confirmed')
        if not orders_to_merge:
            raise UserError("You can only merge Manufacturing Orders in Confirmed state!")

        if len(orders_to_merge.mapped('product_id')) > 1:
            raise UserError("You can only merge Manufacturing Orders with same product!")
        else:
            product_id = orders_to_merge.mapped('product_id')

        orders_to_merge.action_cancel()

        if len(orders_to_merge.mapped('x_demand_batch_id')) > 1:
            demand_batch_id = orders_to_merge.mapped('x_demand_batch_id')[0]
        else:
            demand_batch_id = orders_to_merge.mapped('x_demand_batch_id')

        demand_qty = sum(orders_to_merge.mapped('product_qty'))
        demand_details = orders_to_merge.mapped('x_mrp_demand_ids')

        bom_id = self.env['mrp.bom'].create({
            'product_tmpl_id': product_id.product_tmpl_id.id, 'product_qty': demand_qty, 'code': 'New',
        })
        bom_line_ids = orders_to_merge.mapped('bom_id').mapped('bom_line_ids').filtered(lambda l: l.product_qty)
        bom_lines = self.env['mrp.bom.line'].read_group(
            domain=[('id', 'in', bom_line_ids.ids)],
            fields=['product_id', 'x_ref_des', 'product_qty'],
            groupby=['product_id', 'x_ref_des'],
            lazy=False
        )
        for line in bom_lines:
            line_ids = bom_line_ids.filtered(
                lambda l: l.product_id.id == line['product_id'][0] and l.x_ref_des == line['x_ref_des']
            )

            line_ids[0].copy({
                'bom_id': bom_id.id,
                'product_qty': line['product_qty'],
            })

        operation_id = self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'), ('company_id', '=', self.env.company.id),
        ], limit=1)

        order_id = self.env['mrp.production'].create({
            'product_id': product_id.id,
            'product_qty': demand_qty,
            'product_uom_id': product_id.uom_id.id,
            'bom_id': bom_id.id,
            'x_demand_batch_id': demand_batch_id.id,
            'picking_type_id': operation_id.id,
            'location_src_id': operation_id.default_location_src_id.id,
            'location_dest_id': operation_id.default_location_dest_id.id,
        })

        for demand_detail in demand_details:
            demand_detail.copy({'x_manufacturing_id': order_id.id})

        bom_id.code = order_id.name
        order_id._onchange_bom_id()
        order_id._onchange_move_raw()
        order_id.action_confirm()
        order_id.picking_ids.action_assign()
        return orders_to_merge, order_id

    def compute_bom_lines(self):
        for rec in self:
            if not rec.x_bom_tool_id:
                raise UserError("BoM Tool of '%s' is not defined!" % rec.product_id.name)
            elif rec.x_bom_tool_id.state != 'active':
                raise UserError("BoM Tool of '%s' is not active!" % rec.product_id.name)
            elif not rec.x_bom_tool_id.x_routing_id:
                raise UserError("Routing is not defined in BoM Tool!")
            # Variant BoM 'Undefined' check
            variant_id = self.env['product.variant'].search([
                ('x_product_id', '=', rec.product_tmpl_id.id)
            ], limit=1, order="id desc")
            if variant_id.x_status != 'defined' and variant_id:
                raise UserError("Variant BoM status of '%s' is 'Undefined'!" % rec.product_tmpl_id.name)
            # BoM line products 'Archived' check
            bom_line_ids = rec.x_bom_tool_id.mapped('x_bom_line_ids').filtered(
                lambda bl: not bl.x_dnp and not bl.x_move_to_tool_id and not bl.x_design_deleted and not bl.x_deleted
            ) + variant_id.mapped('x_bom_id').mapped('x_bom_line_ids').filtered(
                lambda bl: not bl.x_dnp and not bl.x_move_to_tool_id and not bl.x_design_deleted and not bl.x_deleted
            )
            error_message = {"%s in %s (%s) is Archived." % (
                bl.x_product_id.name, bl.x_bom_tool_id.x_name, bl.x_base_product_id.name
            ) for bl in bom_line_ids.filtered(lambda p: not p.x_product_id.active)}

            if error_message:
                raise UserError("\n".join(error_message))

            # Delete BoM Lines Parts
            rec.move_raw_ids = [(2, move.id) for move in rec.move_raw_ids]
            # Delete MO BoMs
            self.env['mrp.bom'].search([
                ('product_tmpl_id', '!=', rec.product_id.product_tmpl_id.id),
                ('code', '=', rec.name),
                ('company_id', '=', rec.company_id.id),
            ]).unlink()
            bom_id = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                ('code', 'in', (rec.name, 'New')),
                ('company_id', '=', rec.company_id.id),
            ], limit=1, order="id desc")
            if not bom_id:
                # Create MO BoM
                bom_id = self.env['mrp.bom'].create({
                    'product_tmpl_id': rec.product_id.product_tmpl_id.id,
                    'product_id': rec.product_id.id,
                    'product_qty': rec.product_qty,
                    'code': rec.name,
                    'routing_id': rec.x_bom_tool_id.with_context(company_id=rec.company_id.id).x_routing_id.id,
                    'company_id': rec.company_id.id,
                })
            else:
                # Update BoM
                bom_id.write({
                    'product_qty': rec.product_qty,
                    'code': rec.name,
                    'routing_id': rec.x_bom_tool_id.with_context(company_id=rec.company_id.id).x_routing_id.id,
                })
            # Update BoM & MO Lines
            rec.x_bom_tool_id.state = 'active'
            bom_id.compute_bom_lines()
            rec.bom_id = bom_id.id
            rec._onchange_move_raw()

    def _get_move_raw_values(self, bom_line, line_data):
        data = super(MrpProduction, self)._get_move_raw_values(bom_line, line_data)
        data['x_ref_des'] = bom_line.x_ref_des
        return data

    def update_move_raw_ids(self):
        if self.state not in ('done', 'cancel'):
            self.action_toggle_is_locked()
            if self.bom_id and self.product_qty > 0:
                list_move_raw = []
                moves_raw_values = self._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in
                                 self.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                for move_raw_values in moves_raw_values:
                    if move_raw_values['bom_line_id'] in move_raw_dict:
                        # update existing entries
                        list_move_raw += [(1, move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                    else:
                        # add new entries
                        list_move_raw += [(0, 0, move_raw_values)]
                self.move_raw_ids = list_move_raw
            else:
                self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]

            for move in self.move_raw_ids:
                if move.state not in ('done', 'cancel'):
                    move_ids = self.move_raw_ids.filtered(
                        lambda m: m.state == 'done' and m.product_id.id == move.product_id.id)
                    move.product_uom_qty -= sum(move_ids.mapped('product_uom_qty'))

            for rec in self:
                for move in rec.move_raw_ids:
                    move.write({'unit_factor': move.product_uom_qty / rec.product_qty})
                rec.move_raw_ids._adjust_procure_method()
                (rec.move_raw_ids | rec.move_finished_ids)._action_confirm()
                rec.move_raw_ids._recompute_state()
            self.action_toggle_is_locked()
            self.action_assign()

            move_orig_ids = self.move_raw_ids.mapped('move_orig_ids').filtered(
                lambda m: m.state not in ('done', 'cancel')
            )
            for move_orig_id in move_orig_ids:
                product_uom_qty = sum(move_orig_id.mapped('move_dest_ids').filtered(
                    lambda m: m.state not in ('done', 'cancel')
                ).mapped('product_uom_qty'))
                reserved_availability = sum(move_orig_id.mapped('move_dest_ids').filtered(
                    lambda m: m.state not in ('done', 'cancel')
                ).mapped('reserved_availability'))
                move_orig_id.write({'product_uom_qty': product_uom_qty - reserved_availability})

            if self.picking_ids.filtered(lambda l: l.state == 'assigned'):
                self.picking_ids.filtered(lambda l: l.state == 'assigned').action_assign()

        return True

        # for rec in self:
        #     for move in rec.move_raw_ids:
        #         workorder_id = rec.workorder_ids.filtered(
        #             lambda wo: wo.operation_id.id == move.bom_line_id.operation_id.id
        #         )
        #         if workorder_id:
        #             workorder_id = workorder_id[0].id
        #         elif rec.workorder_ids:
        #             workorder_id = max(rec.workorder_ids.ids)
        #
        #         move.write({
        #             'unit_factor': move.product_uom_qty / rec.product_qty,
        #             'workorder_id': workorder_id,
        #         })
        #         move.mapped('move_line_ids').write({
        #             'workorder_id': workorder_id,
        #         })
        #
        #     rec.workorder_ids.filtered(
        #         lambda l: l.state not in ('done', 'cancel')
        #     ).mapped('raw_workorder_line_ids').unlink()
        #
        #     rec.move_raw_ids._adjust_procure_method()
        #     (rec.move_raw_ids | rec.move_finished_ids)._action_confirm()
        #     rec.move_raw_ids._recompute_state()
        #     rec.action_assign()
        #
        #     for workorder in rec.workorder_ids:
        #         raw_moves = workorder.move_raw_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
        #         for move in raw_moves:
        #             workorder_lines = workorder.raw_workorder_line_ids.filtered(lambda w: w.move_id == move)
        #             qty_to_consume = workorder._prepare_component_quantity(move, workorder.qty_producing)
        #             qty_to_consume = workorder._get_real_uom_qty(qty_to_consume, True)
        #             for wl in workorder_lines:
        #                 wl.qty_to_consume = qty_to_consume
        #                 wl.qty_reserved = move.reserved_availability
        #                 wl.qty_done = move.quantity_done

    def action_compute_child_manufacturing_orders(self):
        for rec in self:
            if not rec.x_bom_tool_id:
                raise UserError("BoM Tool of '%s' is not defined!" % rec.product_id.name)
            elif rec.x_bom_tool_id.state != 'active':
                raise UserError("BoM Tool of '%s' is not active!" % rec.product_id.name)
            # Variant BoM 'Undefined' check
            variant_id = self.env['product.variant'].search([
                ('x_product_id', '=', rec.product_tmpl_id.id)
            ], limit=1, order="id desc")
            if variant_id.x_status != 'defined' and variant_id:
                raise UserError("Variant BoM status of '%s' is 'Undefined'!" % rec.product_tmpl_id.name)
            # BoM line products 'Archived' check
            bom_line_ids = rec.x_bom_tool_id.mapped('x_bom_line_ids').filtered(
                lambda bl: not bl.x_dnp and not bl.x_move_to_tool_id and not bl.x_design_deleted and not bl.x_deleted
            )
            error_message = {"%s in %s (%s) is Archived." % (
                bl.x_product_id.name, bl.x_bom_tool_id.x_name, bl.x_base_product_id.name
            ) for bl in bom_line_ids.filtered(lambda p: not p.x_product_id.active)}

            if error_message:
                raise UserError("\n".join(error_message))

            if rec.state == 'draft':
                rec.action_confirm()
                rec.picking_ids.action_assign()

            move_ids = rec.picking_ids.filtered(
                lambda p: p.state in ('assigned', 'confirmed')
            ).mapped('move_lines').filtered(
                lambda m: m.product_id.x_goods_type in ('fg', 'sfg') and m.reserved_availability < m.product_uom_qty
            )

            if not move_ids:
                continue
            # Child BoM 'Active' check
            if any(not x for x in move_ids.mapped('product_id.x_bom_tool_id')):
                raise UserError("BoM Tool not defined! %s" % ', '.join(move_ids.mapped('product_id').filtered(
                    lambda p: not p.x_bom_tool_id
                ).mapped('name')))
            elif any(x != 'active' for x in move_ids.mapped('product_id.x_bom_tool_id.state')):
                raise UserError("BoM Tool not active! %s" % ', '.join(move_ids.mapped('product_id').filtered(
                    lambda p: p.x_bom_tool_id.state != 'active'
                ).mapped('name')))
            # Child Variant BoM 'Undefined' check
            error_message = []
            variant_ids = self.env['product.variant'].search([
                ('x_product_id', 'in', move_ids.mapped('product_id.product_tmpl_id').ids)
            ], limit=1, order="id desc")
            if variant_ids:
                for product in move_ids.mapped('product_id.product_tmpl_id'):
                    variant_id = variant_ids.search([
                        ('x_product_id', '=', product.id)
                    ], limit=1, order="id desc")
                    if variant_id.x_status != 'defined' and variant_id:
                        error_message.append("Variant BoM status of '%s' is 'Undefined'!" % product.name)

            if error_message:
                raise UserError("\n".join(error_message))
            # Child BoM line products 'Archived' check
            bom_line_ids = move_ids.mapped('product_id.product_tmpl_id').mapped('x_bom_tool_id').mapped(
                'x_bom_line_ids'
            ).filtered(
                lambda bl: not bl.x_dnp and not bl.x_move_to_tool_id and not bl.x_design_deleted and not bl.x_deleted
            ) + variant_ids.mapped('x_bom_id').mapped('x_bom_line_ids').filtered(
                lambda bl: not bl.x_dnp and not bl.x_move_to_tool_id and not bl.x_design_deleted and not bl.x_deleted
            )

            error_message = {"%s in %s (%s) is Archived." % (
                bl.x_product_id.name, bl.x_bom_tool_id.x_name, bl.x_base_product_id.name
            ) for bl in bom_line_ids.filtered(lambda p: not p.x_product_id.active)}

            if error_message:
                raise UserError("\n".join(error_message))

            for move in move_ids:
                picking_reserved = move.reserved_availability

                demand_list = []
                demand_list_qty = 0
                for line in rec.x_mrp_demand_ids:
                    demand_qty = move.product_uom_qty * line.x_quantity / rec.product_qty
                    reserved_qty = picking_reserved if demand_qty > picking_reserved else demand_qty
                    picking_reserved = 0 if demand_qty > picking_reserved else picking_reserved - demand_qty

                    required_qty = demand_qty - reserved_qty

                    demand_list.append((0, 0, {
                        'x_child_product_id': move.product_id.id,
                        'x_demand_type': line.x_demand_type,
                        'x_master_order_id': rec.id,
                        'x_sale_id': line.x_sale_id.id,
                        'x_demand': demand_qty,
                        'x_reserved': reserved_qty,
                        'x_quantity': required_qty,
                    }))
                    demand_list_qty += required_qty

                order_id = self.env['mrp.production'].search([
                    ('product_id', '=', move.product_id.id),
                    ('x_demand_batch_id', '=', rec.x_demand_batch_id.id),
                    ('x_master_order_id', '=', rec.id),
                    ('state', 'in', ('draft', 'confirmed')),
                ], limit=1, order="id desc")

                if not order_id and demand_list_qty > 0:
                    bom_id = self.env['mrp.bom'].create({
                        'product_tmpl_id': move.product_id.product_tmpl_id.id,
                        'product_qty': demand_list_qty,
                        'code': 'New',
                    })
                    operation_id = self.env['stock.picking.type'].search([
                        ('code', '=', 'mrp_operation'),
                        ('company_id', '=', rec.company_id.id),
                    ], limit=1)
                    order_id = self.env['mrp.production'].create({
                        'product_id': move.product_id.id,
                        'product_qty': demand_list_qty,
                        'product_uom_id': move.product_id.uom_id.id,
                        'bom_id': bom_id.id,
                        'x_demand_batch_id': rec.x_demand_batch_id.id,
                        'x_master_order_id': rec.id,
                        'x_mrp_demand_ids': demand_list,
                        'picking_type_id': operation_id.id,
                        'location_src_id': operation_id.default_location_src_id.id,
                        'location_dest_id': operation_id.default_location_dest_id.id,
                        'x_tag_ids': rec.x_tag_ids.ids,
                    })
                    order_id.compute_bom_lines()
                    order_id.action_compute_child_manufacturing_orders()
                elif order_id and demand_list_qty > 0:
                    mrp_demand_ids = order_id.x_mrp_demand_ids.filtered(lambda o: o.x_master_order_id.id == rec.id).ids
                    order_id.x_mrp_demand_ids = [(2, demand_id) for demand_id in mrp_demand_ids]
                    order_id.update({
                        'product_qty': demand_list_qty,
                        'x_demand_batch_id': rec.x_demand_batch_id.id,
                        'x_mrp_demand_ids': demand_list,
                        'x_tag_ids': rec.x_tag_ids.ids,
                    })
                    order_id.update_move_raw_ids()
                    order_id.action_compute_child_manufacturing_orders()


class MrpSourceDetails(models.Model):
    _name = 'mrp.source.details'
    _description = "Mrp Source Details"
    _rec_name = "display_name"
    _order = "x_deadline"

    x_manufacturing_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing", required=False, )
    x_mo_state = fields.Selection(related="x_manufacturing_id.state", string="MO Status")
    x_date_planned_start = fields.Datetime(related="x_manufacturing_id.x_planned_start_date", store=True)
    x_date_planned_finished = fields.Datetime(related="x_manufacturing_id.x_planned_finish_date", store=True)

    x_demand_type = fields.Selection(selection=[
        ('sale', 'Sale Order'), ('stock', 'Stock Build'), ('internal', 'Internal Demand'),
    ], string='Demand Type', required=True, )

    x_master_order_id = fields.Many2one(comodel_name="mrp.production", string="Master Order", required=False)
    x_product_id = fields.Many2one(related='x_master_order_id.product_id', string="Master Product")
    x_product_qty = fields.Float(related='x_master_order_id.product_qty', string="Master Product Qty")
    x_product_category = fields.Char(related='x_master_order_id.product_id.categ_id.name')

    x_child_product_id = fields.Many2one(related='x_manufacturing_id.product_id')
    x_child_product_qty = fields.Float(related='x_manufacturing_id.product_qty', string="Product Qty")
    x_free_qty = fields.Float(related='x_manufacturing_id.product_id.free_qty')

    x_sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False,
                                domain="[('state', 'in', ('sale', 'done'))]")
    x_folder_name = fields.Char(related="x_sale_id.x_folder_name")

    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Delivery Order', required=False,
                                   compute="_compute_picking_id", store=True, copy=False)
    x_do_state = fields.Selection(related="x_picking_id.state", string="DO Status", store=True)
    x_deadline = fields.Datetime(related="x_picking_id.x_deadline", store=True)

    x_demand = fields.Float(string="Initial Demand", digits='Product Unit of Measure', required=False)
    x_reserved = fields.Float(string="Reserved", digits='Product Unit of Measure', required=False)
    x_quantity = fields.Float(string="Required", digits='Product Unit of Measure', required=True)

    display_name = fields.Char(string='Display Name', compute="_compute_display_name", store=True, copy=False)

    def update_child_orders(self):
        for rec in self:
            rec.x_master_order_id.x_child_ids = [(2, line.id) for line in rec.x_master_order_id.x_child_ids]

            manufacturing_ids = self.env['mrp.source.details'].search([
                ('x_master_order_id', '=', rec.x_master_order_id.id)
            ]).mapped('x_manufacturing_id').filtered(lambda m: m.state not in ('cancel'))

            rec.x_master_order_id.x_child_ids = [
                (0, 0, {'child_manufacturing_id': line.id}) for line in manufacturing_ids
            ]

    @api.depends('x_sale_id')
    def _compute_picking_id(self):
        for rec in self:
            picking_ids = rec.x_sale_id.picking_ids.filtered(
                lambda l: l.state not in ('done', 'cancel') and l.move_lines.filtered(
                    lambda m: m.product_id.id == rec.x_product_id.id or rec.x_manufacturing_id.product_id.id
                )
            )
            rec.x_picking_id = picking_ids[0].id if picking_ids else False

    @api.depends(
        'x_demand_type', 'x_sale_id', 'x_master_order_id', 'x_quantity',
        # 'x_picking_id', 'x_picking_id.x_deadline',
    )
    def _compute_display_name(self):
        for rec in self:
            # SOXXX : WH/OUT/XXX : QTYXX : DL2024-12-10 : Parent MO#
            rec.display_name = '%s%s%s' % (
                '%s' % rec.x_sale_id.name if rec.x_sale_id else 'SB' if rec.x_demand_type == 'stock' else 'ID',
                # ' %s :' % rec.x_picking_id.name if rec.x_picking_id else '',
                ' : QTY%s' % rec.x_quantity,
                # ' DL%s :' % rec.x_picking_id.x_deadline.date() if rec.x_picking_id.x_deadline else '',
                ' : %s' % rec.x_master_order_id.name if rec.x_master_order_id else '',
            )


class MrpProcurementBatch(models.Model):
    _name = 'mrp.procurement.batch'
    _description = "Mrp Procurement Batch"
    _rec_name = "x_name"

    x_name = fields.Char(string='Name', required=False)


class StockBuildRuleList(models.Model):
    _name = 'stock.build.rule.list'
    _description = "Stock Build Rule List"


class CustomDemandLines(models.Model):
    _name = "custom.demand.lines"
    _description = "Custom Demand Lines"
