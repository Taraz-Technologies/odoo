from odoo import api, fields, models, _
from odoo.exceptions import UserError

import datetime
import pytz

from datetime import timedelta
import logging

_logger = logging.getLogger("*__addons_custom__*")


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    x_show_recommended_locations = fields.Boolean(string='Show Recommended Locations', required=False)


class StockMoveLineMerged(models.Model):
    _name = 'stock.move.line.merged'
    _description = 'Merged Stock Moves and Move Lines Without Package'

    x_picking_id = fields.Many2one('stock.picking', string='Picking', required=True, ondelete='cascade')
    x_product_id = fields.Many2one('product.product', string='Product', required=True)
    x_location_id = fields.Many2one('stock.location', string='Source Location', required=True)

    x_move_id = fields.Many2one('stock.move', string="Stock Moves")
    x_move_line_id = fields.Many2one('stock.move.line', string='Operations')

    x_product_uom_quantity = fields.Float(string='Initial Demand', required=True)
    x_reserved_availability = fields.Float(string='Reserved', required=True)
    x_qty_done = fields.Float(string='Done', required=True)
    x_product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')

    x_comment = fields.Text(string="Comment")
    x_custom_tag_ids = fields.Many2many('custom.tags', string='Tags')
    x_checkbox_done = fields.Boolean(string='Is Done')
    x_checkbox_bom_error = fields.Boolean(string="Is BOM Error")

    x_qty_picked = fields.Float(string="Picked", default=0, required=True)
    x_qty_error = fields.Float(string="Error", compute="_compute_qty_error", store=True)

    x_image_128 = fields.Image(related='x_product_id.image_128', string='Image')
    x_product_description = fields.Text(related='x_product_id.description', string='Description')

    @api.onchange('x_qty_picked', 'x_qty_error')
    def onchange_error_and_picked(self):
        for rec in self:
            if rec.x_qty_error == 0 and rec.x_qty_picked != 0:
                rec.x_checkbox_done = True

    @api.onchange('x_checkbox_done')
    def onchange_x_checkbox_done(self):
        for rec in self:
            if rec.x_checkbox_done:
                rec.x_qty_picked = rec.x_reserved_availability


    @api.depends('x_qty_picked', 'x_reserved_availability')
    def _compute_qty_error(self):
        for rec in self:
            rec.x_qty_error = rec.x_reserved_availability - rec.x_qty_picked


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_show_recommended_locations = fields.Boolean(
        related="picking_type_id.x_show_recommended_locations",
        store=True)
    
    x_invoice_payment_term_id = fields.Many2one(
        related="x_invoice_id.invoice_payment_term_id",
        string="Payment Terms",
        readonly=False,
        store=True,
    )

    x_payment_method = fields.Many2one(
        related="x_invoice_id.x_payment_method",
        readonly=False,
        store=True)

    x_transit_invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Dropship Invoice',
        domain="[('type', 'in', ('out_invoice', 'out_refund')), ('company_id', '=', company_id)]",
        required=False)

    x_show_transit_invoice_payment_terms = fields.Boolean(string='Payment Dropship Terms?', )
    x_transit_invoice_payment_term_id = fields.Many2one(
        related="x_transit_invoice_id.invoice_payment_term_id",
        string="Dropship Payment Terms",
        readonly=False,
        store=True,
    )

    x_show_transit_invoice_payment_method = fields.Boolean(string="Dropship Payment Method?", )
    x_transit_invoice_payment_method = fields.Many2one(
        related="x_transit_invoice_id.x_payment_method",
        string="Dropship Payment Method",
        readonly=False,
        store=True,
    )

    x_transit_bill_id = fields.Many2one(
        comodel_name='account.move',
        string='Dropship Bill',
        domain="[('type', 'in', ('in_invoice', 'in_refund')), ('company_id', '!=', company_id)]",
        required=False)
    
    x_deadline = fields.Datetime(string='Deadline', tracking=True,)
    x_expected_date = fields.Datetime(string='Expected Date', tracking=True, copy=False)
    x_compute_schedule_date = fields.Boolean(compute='_compute_schedule_date_deadline_date')

    x_deadline_days = fields.Integer(compute="_compute_days")
    x_expected_days = fields.Integer(compute="_compute_days")

    x_chat_url = fields.Char(string='Chat URL', required=False, tracking=True)

    x_order_value = fields.Float(string='Order Value', compute="_compute_order_value")

    x_shipping_date = fields.Date(related='x_tracking_id.x_shipping_date', store=True, readonly=False, tracking=True)

    x_sale_order_payment_method = fields.Many2one(related='x_sale_id.x_payment_method', store=True)
    x_sale_order_payment_terms = fields.Many2one(related='x_sale_id.payment_term_id', store=True)

    merged_moves_without_package = fields.One2many(
        'stock.move.line.merged',
        'x_picking_id',
        string='Merged Moves Without Package',
        compute='_compute_merged_moves_without_package',
        store=True,
    )


    def action_picking_move_tree_cus_stock(self):
        self._compute_merged_moves_without_package()
        action = self.env.ref('cus_stock.open_operations_action').read()[0]
        action['views'] = [
            (self.env.ref('cus_stock.stock_move_line_merged_tree_view_cus_stock').id, 'tree'),
        ]
        action['context'] = self.env.context
        action['domain'] = [
            ('x_picking_id', 'in', self.ids)
        ]
        return action

    @api.depends('move_ids_without_package', 'move_line_ids_without_package')
    def _compute_merged_moves_without_package(self):
        for picking in self:
            # Prepare a map of existing records to avoid duplicates
            existing_records_map = {
                (record.x_product_id.id, record.x_location_id.id, record.x_move_id.id if record.x_move_id else None,
                 record.x_move_line_id.id if record.x_move_line_id else None): record
                for record in picking.merged_moves_without_package
            }

            new_records_data = []

            # Process move_ids_without_package (from stock.move)
            for move in picking.move_ids_without_package.filtered(lambda m: not m.move_line_ids):
                key = (move.product_id.id, move.location_id.id, move.id, None)
                if key not in existing_records_map:
                    new_records_data.append({
                        'x_picking_id': picking.id,
                        'x_product_id': move.product_id.id,
                        'x_location_id': move.location_id.id,
                        'x_product_uom_quantity': move.product_uom_qty,
                        'x_reserved_availability': move.reserved_availability,
                        'x_qty_done': move.quantity_done,
                        'x_product_uom_id': move.product_uom.id,
                        'x_move_id': move.id,
                    })

            # Process move_line_ids_without_package (from stock.move.line)
            for move_line in picking.move_line_ids_without_package:
                key = (move_line.product_id.id, move_line.location_id.id, None, move_line.id)
                if key not in existing_records_map:
                    new_records_data.append({
                        'x_picking_id': picking.id,
                        'x_product_id': move_line.product_id.id,
                        'x_location_id': move_line.location_id.id,
                        'x_product_uom_quantity': move_line.product_uom_qty,
                        'x_reserved_availability': move_line.product_uom_qty,
                        'x_qty_done': move_line.qty_done,
                        'x_product_uom_id': move_line.product_uom_id.id,
                        'x_move_line_id': move_line.id,
                    })

            # Create only new records, keeping existing ones intact
            if new_records_data:
                picking.merged_moves_without_package = [(0, 0, data) for data in new_records_data]

    # @api.depends('move_ids_without_package', 'move_line_ids_without_package')
    # def _compute_merged_moves_without_package(self):
    #     StockMoveLineMerged = self.env['stock.move.line.merged']
    #     for picking in self:
    #         # Unlink existing records to recalculate
    #         picking.merged_moves_without_package = [(2, line.id) for line in picking.merged_moves_without_package]
    #
    #         merged_data = []
    #
    #         # Process move_ids_without_package (from stock.move)
    #         for move in picking.move_ids_without_package.filtered(lambda m: not m.move_line_ids):
    #             merged_data.append((0, 0, {
    #                 'x_picking_id': picking.id,
    #                 'x_product_id': move.product_id.id,
    #                 'x_location_id': move.location_id.id,
    #                 'x_product_uom_quantity': move.product_uom_qty,
    #                 'x_reserved_availability': move.reserved_availability,
    #                 'x_qty_done': move.quantity_done,
    #                 'x_product_uom_id': move.product_uom.id,
    #             }))
    #
    #         # Process move_line_ids_without_package (from stock.move.line)
    #         for move_line in picking.move_line_ids_without_package:
    #             merged_data.append((0, 0, {
    #                 'x_picking_id': picking.id,
    #                 'x_product_id': move_line.product_id.id,
    #                 'x_location_id': move_line.location_id.id,
    #                 'x_product_uom_quantity': move_line.product_uom_qty,
    #                 'x_reserved_availability': move_line.product_uom_qty,
    #                 'x_qty_done': move_line.qty_done,
    #                 'x_product_uom_id': move_line.product_uom_id.id,
    #             }))
    #
    #         # Create new records
    #         picking.merged_moves_without_package = merged_data

    def create_new_receipt(self):
        for rec in self:
            order_id = rec.move_lines.purchase_line_id.order_id
            for order in order_id:
                if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                    res = order._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date_expected):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    picking.message_post_with_view('mail.message_origin_link',
                        values={'self': picking, 'origin': order},
                        subtype_id=self.env.ref('mail.mt_note').id)
            return True

    @api.depends(
        'move_lines.purchase_line_id.order_id.amount_total',
        'move_ids_without_package.sale_line_id.order_id.amount_total',
    )
    def _compute_order_value(self):
        for rec in self:
            if rec.move_lines.purchase_line_id.order_id:
                rec.x_order_value = rec.move_lines.purchase_line_id.order_id.amount_total
                rec.x_currency_id = rec.move_lines.purchase_line_id.order_id.currency_id.id
            elif rec.move_ids_without_package.sale_line_id.order_id:
                rec.x_order_value = rec.move_lines.sale_line_id.order_id.amount_total
                rec.x_currency_id = rec.move_lines.sale_line_id.order_id.currency_id.id
            else:
                rec.x_order_value = 0


    def open_chat(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.x_chat_url,
            'target': 'new',
        }

    def _compute_days(self):
        current_data = datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz))
        for rec in self:
            rec.x_deadline_days = (rec.x_deadline.date() - current_data.date()).days if rec.x_deadline else 0
            rec.x_expected_days = (rec.x_expected_date.date() - current_data.date()).days if rec.x_expected_date else 0

    @api.depends('x_sale_id', 'x_sale_id.date_order', 'x_sale_id.x_lead_time')
    def _compute_schedule_date_deadline_date(self):
        for rec in self:
            if rec.x_sale_id and rec.state not in ('done', 'cancel'):
                lead_time = rec.x_sale_id.x_lead_time
                lead_time_to_days = {
                    "1": 1,
                    "2-3 days": 3,
                    "1 week": 7,
                    "2 weeks": 14,
                    "3 weeks": 21,
                    "4 weeks": 28,
                    "5 weeks": 35,
                    "6 weeks": 42,
                    "7 weeks": 49,
                    "8 weeks": 56,
                    "10 weeks": 70,
                    "12 weeks": 84,
                    "18 weeks": 126,
                    "6 months": 182,
                    "1 year": 365,
                    "2 years": 730,
                }
                if lead_time in lead_time_to_days:
                    rec.scheduled_date = rec.x_sale_id.date_order + timedelta(days=lead_time_to_days[lead_time])
                    rec.x_deadline = rec.x_sale_id.date_order + timedelta(days=lead_time_to_days[lead_time])
            rec.x_compute_schedule_date = True

    def run_transit_trade_operation(self):
        for rec in self:
            if rec.company_id.id != self.env.company.id:
                raise UserError(_("Odoo selected company is not same as the order company!"))

            if self.env['custom.tags'].search([('x_name', '=', 'Dropship')]):
                tag_id = [(4, self.env['custom.tags'].search([('x_name', '=', 'Dropship')]).id)]
            else:
                tag_id = [(4, self.env['custom.tags'].create({'x_name': 'Dropship', 'color': 4}).id)]

            rec.update({
                # 'x_partner_invoice_id': 15 if rec.picking_type_id.id == 39 else rec.x_customer_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id if rec.picking_type_id.id == 39 else 39,
                'location_id': self.env.ref('stock.stock_location_stock').id if rec.picking_type_id.id == 39 else 1297,
                'x_tag_ids': tag_id,
            })

            rec.onchange_picking_type()

            rec.x_sale_id.update({
                'x_sale_type_turkey': 'dropship_av' if rec.x_total_amount == rec.x_sale_id.amount_total else 'dropship_uv',
            })

            rec.move_ids_without_package.update({
                'company_id': rec.company_id.id,
                'picking_type_id': rec.picking_type_id.id,
                'location_id': rec.location_id.id,
                'rule_id': 1 if rec.picking_type_id.id == self.env.ref('stock.picking_type_out').id else 33,
            })

            rec.move_line_ids_without_package.update({
                'company_id': rec.company_id.id,
                'location_id': rec.location_id.id,
            })

            if not rec.x_transit_invoice_id:
                vals = {
                    'x_customer_id': rec.x_customer_id.id,
                    'partner_id': rec.x_partner_invoice_id.id,
                    'partner_shipping_id': rec.partner_id.id,
                    'x_end_user_id': rec.x_end_user_id.id,
                    'type': 'out_invoice',
                    'invoice_date': rec.scheduled_date.date(),
                    'invoice_payment_term_id': rec.x_invoice_id.invoice_payment_term_id.id,
                    'journal_id': self.env.ref('customizations.journal_customer_invoices').id,
                    'x_payment_method': self.env.ref('customizations.journal_bank_alfalah').id,
                    'x_sale_type': 'Export / WeBoc',
                    'x_export': 'Actual',
                    'invoice_origin': rec.name,
                    'invoice_line_ids': [],
                }

                for line in rec.move_ids_without_package:
                    vals['invoice_line_ids'].append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.sale_line_id.price_unit,
                        'discount': line.sale_line_id.discount,
                        'name': line.product_id.name,
                    }))

                rec.x_transit_invoice_id = self.env['account.move'].create(vals)

            if not rec.x_transit_bill_id:
                vals = {
                    'partner_id': rec.company_id.partner_id.id,
                    'partner_shipping_id': rec.company_id.partner_id.id,
                    'type': 'in_invoice',
                    'invoice_date': rec.scheduled_date.date(),
                    'invoice_payment_term_id': rec.x_invoice_id.invoice_payment_term_id.id,
                    'journal_id': 97,
                    'x_payment_method': 89,
                    'invoice_origin': rec.name,
                    'invoice_line_ids': [],
                }

                for line in rec.move_ids_without_package:
                    vals['invoice_line_ids'].append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.sale_line_id.price_unit,
                        'discount': line.sale_line_id.discount,
                        'account_id': line.product_id.categ_id.property_stock_account_output_categ_id.id,
                        'name': line.product_id.name,
                    }))

                rec.x_transit_bill_id = self.env['account.move'].create(vals)


class ShippingInvoiceLines(models.Model):
    _inherit = "shipping.invoice.lines"

    hs_code_id = fields.Many2one(comodel_name="hs.code.database", string="HS Code")
    country_id = fields.Many2one(comodel_name="res.country", string="COO")
    weight = fields.Float(string="Weight")
    accessories = fields.Boolean(string='Accessories?', default=True)


class ShippingPackage(models.Model):
    _inherit = "shipping.package"

    x_packing_list_ids = fields.One2many(
        comodel_name="packing.list", inverse_name="x_package", string="Packing List", readonly=False,
    )
    # x_compute_weights = fields.Boolean(compute="_compute_weights")
    x_compute_weights = fields.Boolean()

    # @api.depends('x_packing_list_ids')
    # def _compute_weights(self):
    #     pass
        # for rec in self:
            # rec.x_net_weight = sum(rec.x_packing_list_ids.mapped('x_net_weight'))
            # rec.x_gross_weight = sum(rec.x_packing_list_ids.mapped('x_gross_weight'))
            # rec.x_compute_weights = True


class PackingList(models.Model):
    _inherit = "packing.list"

    x_net_weight = fields.Float(string='Net Weight (kg)')
    x_gross_weight = fields.Float(string='Gross Weight (kg)')
    x_accessories = fields.Boolean(string='Accessories?', default=True)

    @api.onchange('x_product_id')
    def get_product_weights(self):
        for rec in self:
            rec.x_net_weight = rec.x_product_id.weight
            rec.x_gross_weight = rec.x_product_id.x_gross_weight

    @api.onchange('x_net_weight')
    def update_product_net_weights(self):
        for rec in self:
            rec.x_product_id.weight = rec.x_net_weight
            rec.x_package.x_net_weight = sum(rec.x_package.x_packing_list_ids.mapped('x_net_weight'))

    @api.onchange('x_gross_weight')
    def update_product_gross_weights(self):
        for rec in self:
            rec.x_product_id.x_gross_weight = rec.x_gross_weight
            rec.x_package.x_gross_weight = sum(rec.x_package.x_packing_list_ids.mapped('x_gross_weight'))




