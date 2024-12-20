from odoo import fields, models, api, _

import datetime
import pytz


class Consolidations(models.Model):
    _name = "consolidation.tracking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Consolidations"
    _rec_name = 'x_internal_ref'

    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Consolidated'),
    ], string='Status', default="draft", required=True, tracking=True)

    x_bill_ids = fields.Many2many(comodel_name='account.move', string='Bills')

    x_name = fields.Char(string='Name', default="New", copy=False, index=True, readonly=True)

    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Forwarder',
                                   domain="[('x_is_forwarder', '=', True)]", required=True, tracking=True)

    x_internal_ref = fields.Char(string='Internal Reference', required=True, tracking=True)
    x_vendor_code = fields.Char(related="x_partner_id.x_vendor_code", store=True)
    x_vendor_counter = fields.Integer(related="x_partner_id.x_vendor_counter", store=True, readonly=False)

    x_forwarder_ref = fields.Char(string='Forwarder Reference', tracking=True)

    x_purchase_ids = fields.Many2many(comodel_name='purchase.order', string='Purchase Orders')
    x_consolidation_ids = fields.Many2many(comodel_name='consolidation.tracking', string='Consolidations',
                                           relation="consolidation_tracking_consolidation_tracking_rel_1",
                                           column1="consolidation_tracking_1", column2="consolidation_tracking_2",
                                           domain="[('id', '!=', id)]")

    x_tracking_id = fields.Many2one(comodel_name='logistics.tracking', string='Tracking Reference', tracking=True)
    x_route_id = fields.Many2one(related="x_tracking_id.x_route_id", store=True, tracking=True)
    x_sub_route_id = fields.Many2one(related="x_tracking_id.x_sub_route_id", store=True, tracking=True)
    x_length = fields.Float(related="x_tracking_id.x_length", readonly=False, store=True, tracking=True)
    x_width = fields.Float(related="x_tracking_id.x_width", readonly=False, store=True, tracking=True)
    x_height = fields.Float(related="x_tracking_id.x_height", readonly=False, store=True, tracking=True)

    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')
    x_currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=2)
    x_company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)

    x_receipt_ids = fields.One2many('consolidation.receipts', inverse_name='x_consolidation_id', string='Receipts')

    x_product_ids = fields.One2many('consolidation.products', inverse_name='x_consolidation_id', string='Products')

    x_uv_percentage = fields.Float(string='U.V.', default=1)

    x_rule_id = fields.Many2one(comodel_name='country.of.origin.rules', string='COO Rule')
    x_country_ids = fields.Many2many(related="x_rule_id.x_country_ids")
    x_country_id = fields.Many2one(related="x_rule_id.x_country_id")

    x_consolidation_ref = fields.Char(string='Consolidation Ref.', compute="compute_consolidation_ref", store=True)

    x_shipping_invoice_name = fields.Char(string='Shipping Invoice Name', required=False)
    x_shipping_invoice = fields.Binary(string="Shipping Invoice", )

    @api.depends('x_name', 'x_internal_ref', 'x_forwarder_ref')
    def compute_consolidation_ref(self):
        for rec in self:
            rec.x_consolidation_ref = '%s - %s - %s' % (rec.x_name, rec.x_internal_ref, rec.x_forwarder_ref)

    @api.onchange('x_partner_id', 'x_vendor_counter')
    def onchange_vendor_counter(self):
        for rec in self:
            if rec.x_vendor_code and rec.x_vendor_counter:
                rec.x_internal_ref = '%s%s' % (rec.x_vendor_code, rec.x_vendor_counter)
            else:
                rec.x_internal_ref = 'New'

    @api.model
    def create(self, vals_list):
        vals_list['x_name'] = self.env['ir.sequence'].next_by_code('consolidation.tracking') or _('New')
        return super(Consolidations, self).create(vals_list)

    @api.onchange('x_tracking_id')
    def update_forwarder_tracking(self):
        for rec in self:
            if rec.x_tracking_id:
                rec.x_receipt_ids.mapped('x_picking_id').write({'x_forwarder_tracking_id': rec.x_tracking_id.id})

    def open_url(self):
        for rec in self:
            if rec.x_tracking_id.x_carrier_id.x_tracking_url and rec.x_tracking_id.x_tracking_ref:
                return {
                    'type': 'ir.actions.act_url',
                    'url': rec.x_tracking_id.x_carrier_id.x_tracking_url.replace('{Tracking Ref}', rec.x_tracking_id.x_tracking_ref),
                    'target': 'new',
                }

    def change_state_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def change_state_to_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def change_state_to_done(self):
        for rec in self:
            rec.state = 'done'

    def update_receipt_list(self):
        for rec in self:
            # rec.x_receipt_ids.mapped('x_purchase_id').update({'x_consolidation_id': False})
            # self.env['account.move'].search([('purchase_id', 'in', rec.x_purchase_ids.ids)]).update({
            #     'x_consolidation_id': False
            # })

            rec.x_receipt_ids = [(2, receipt.id) for receipt in rec.x_receipt_ids.filtered(
                lambda l: l.x_purchase_id.id not in rec.x_purchase_ids.ids
                and l.x_source_consolidation_id.id not in rec.x_consolidation_ids.ids
            )]

            receipt_list = []

            consolidation_receipt_ids = self.env['consolidation.receipts'].search([
                ('x_consolidation_id.x_partner_id', '=', rec.x_partner_id.id)
            ]).mapped('x_picking_id').ids
            purchase_receipt_ids = self.env['stock.picking'].search([
                ('purchase_id', 'in', rec.x_purchase_ids.ids), ('state', '!=', 'cancel')
            ])
            purchase_receipt_ids = purchase_receipt_ids.filtered(lambda l: l.id not in consolidation_receipt_ids).ids

            for receipt in purchase_receipt_ids:
                receipt_list.append((0, 0, {'x_picking_id': receipt}))

            consolidation_receipt_ids = self.env['consolidation.receipts'].search([
                ('x_consolidation_id', 'in', rec.x_consolidation_ids.ids),
            ])
            consolidation_receipt_ids = consolidation_receipt_ids.filtered(
                lambda l: l.x_picking_id.id not in rec.x_receipt_ids.mapped('x_picking_id').ids
            )

            for receipt in consolidation_receipt_ids:
                receipt_list.append((0, 0, {
                    'x_picking_id': receipt.x_picking_id.id,
                    'x_source_consolidation_id': receipt.x_consolidation_id.id,
                }))
            rec.x_receipt_ids = receipt_list

            # rec.x_receipt_ids.mapped('x_purchase_id').update({'x_consolidation_id': rec.id})
            # self.env['account.move'].search([('purchase_id', 'in', rec.x_purchase_ids.ids)]).update({
            #     'x_consolidation_id': rec.id
            # })

    def update_product_list(self):
        for rec in self:
            consolidation_receipt_ids = rec.x_receipt_ids.mapped('x_picking_id')
            rec.x_product_ids.filtered(lambda l: l.x_picking_id.id not in consolidation_receipt_ids.ids).unlink()

            consolidation_product_ids = rec.x_product_ids.mapped('x_product_id').ids
            receipts_move_ids = consolidation_receipt_ids.mapped('move_ids_without_package')
            move_ids = receipts_move_ids.filtered(
                lambda l: l.product_id.id not in consolidation_product_ids and l.quantity_done != 0
            )
            product_list = []
            for move in move_ids:
                product_list.append((0, 0, {
                    'x_picking_id': move.picking_id.id,
                    'x_product_id': move.product_id.id,
                    'x_uom_id': move.product_uom.id,
                    'x_quantity': move.quantity_done,
                    'x_unit_price': move.purchase_line_id.currency_id._convert(move.purchase_line_id.price_unit, rec.x_currency_id, self.env.company, move.purchase_line_id.date_order),
                    'x_uv_quantity': move.quantity_done,
                }))
            rec.x_product_ids = product_list

    def compute_uv(self):
        for rec in self:
            for product_id in rec.x_product_ids:
                product_id.write({'x_uv_subtotal': product_id.x_subtotal * rec.x_uv_percentage})

    def export_products_data(self):
        return self.env.ref('cus_logistics_tracking.consolidation_products_xlsx').report_action(self)

    def action_create_landed_cost_bill(self):
        for rec in self:
            bill_id = self.env['account.move'].create({
                'type': 'in_invoice',
                # 'partner_id': rec.x_partner_id.id,
                # 'partner_shipping_id': rec.x_partner_id.id,
                # 'ref': '%s - %s' % (rec.x_forwarder_ref, len(rec.x_bill_ids) + 1),
                'invoice_date': datetime.datetime.now(pytz.timezone(self.env.company.resource_calendar_id.tz)).date(),
                'journal_id': 1 if rec.x_company_id.id == 1 else 97,
                'invoice_incoterm_id': False,
                'x_purchase_type': 'Forwarding',
                'x_item_type': 'Landed Cost',
                'x_related_po_s': rec.x_receipt_ids.mapped('x_purchase_id').ids,
                'x_picking_ids': rec.x_receipt_ids.mapped('x_picking_id').ids,
                'x_consolidation_id': rec.id,
            })
            rec.x_bill_ids = [(4, bill_id.id)]
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            return dict(action, view_mode='form', res_id=bill_id.id, views=[(False, 'form')])

    def action_view_bills(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        domain = [('id', 'in', self.x_bill_ids.ids)]
        context = dict(self.env.context, default_x_consolidation_id=self.id)
        views = [(self.env.ref('account.view_invoice_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)

    def action_view_landed_costs(self):
        self.ensure_one()
        action = self.env.ref('stock_landed_costs.action_stock_landed_cost').read()[0]
        domain = [('id', 'in', self.x_bill_ids.mapped('landed_costs_ids').ids)]
        context = dict(self.env.context)
        views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', self.x_receipt_ids.mapped('x_picking_id').ids)]
        return action

    def unlink(self):
        for rec in self:
            rec.x_receipt_ids.unlink()
            rec.x_product_ids.unlink()
        return super(Consolidations, self).unlink()


class ConsolidationReceipts(models.Model):
    _name = "consolidation.receipts"
    _description = "Consolidation Receipts"
    _rec_name = 'x_picking_id'

    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', required=False)
    x_currency_id = fields.Many2one(related="x_consolidation_id.x_currency_id")
    x_source_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', readonly=True)

    x_package = fields.Char(string='Package #', required=False)
    x_value = fields.Float(string='Value', compute="_compute_value", store=True)

    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Receipt', required=False)
    x_purchase_id = fields.Many2one(related="x_picking_id.purchase_id")
    x_tracking_id = fields.Many2one(related="x_picking_id.x_tracking_id", readonly=False, store=True)
    x_volume = fields.Float(related="x_tracking_id.x_volume", store=True)
    x_weight = fields.Float(related="x_tracking_id.x_weight", readonly=False, store=True)
    x_priority = fields.Selection(related="x_picking_id.priority", readonly=False, store=True)
    x_status = fields.Selection(related="x_picking_id.state")

    @api.model
    def create(self, vals_list):
        res = super(ConsolidationReceipts, self).create(vals_list)
        picking_id = self.env['stock.picking'].browse(vals_list['x_picking_id'])
        picking_id.x_consolidation_ids = [(4, vals_list['x_consolidation_id'])]
        return res

    @api.depends('x_consolidation_id.x_product_ids.x_uv_subtotal')
    def _compute_value(self):
        for rec in self:
            products = rec.x_consolidation_id.x_product_ids.filtered(lambda l: l.x_picking_id.id == rec.x_picking_id.id)
            rec.x_value = sum(products.mapped('x_uv_subtotal'))

    def open_url(self):
        for rec in self:
            if rec.x_tracking_id.x_carrier_id.x_tracking_url and rec.x_tracking_id.x_tracking_ref:
                return {
                    'type': 'ir.actions.act_url',
                    'url': rec.x_tracking_id.x_carrier_id.x_tracking_url.replace('{Tracking Ref}', rec.x_tracking_id.x_tracking_ref),
                    'target': 'new',
                }

    def unlink(self):
        for rec in self:
            rec.x_picking_id.x_consolidation_ids = [(3, rec.x_consolidation_id.id)]
        return super(ConsolidationReceipts, self).unlink()


class ConsolidationProducts(models.Model):
    _name = "consolidation.products"
    _description = "Consolidation Products"
    _rec_name = 'x_product_id'

    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', required=False)
    x_currency_id = fields.Many2one(related="x_consolidation_id.x_currency_id")

    x_picking_id = fields.Many2one(comodel_name='stock.picking', string='Receipt', required=False)

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    x_description = fields.Text(related="x_product_id.description", readonly=False, store=True)
    x_dk_hs_code = fields.Many2one(related="x_product_id.dk_hs_code", readonly=False, store=True)
    x_country_id = fields.Many2one(related="x_product_id.x_country_id", readonly=False, store=True)
    x_unit_weight = fields.Float(related="x_product_id.x_unit_weight", readonly=False, store=True)

    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', required=False)

    x_quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    x_unit_price = fields.Float(string='Unit Price', required=False)
    x_subtotal = fields.Float(string='Subtotal', compute="_compute_subtotal", store=True)

    x_uv_quantity = fields.Float(string='Quantity (UV)', digits='Product Unit of Measure')
    x_uv_unit_price = fields.Float(string='Unit Price (UV)', compute="_compute_uv_unit_price", store=True)
    x_uv_subtotal = fields.Float(string='Subtotal (UV)', required=False)

    @api.depends('x_quantity', 'x_unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.x_subtotal = rec.x_quantity * rec.x_unit_price

    @api.depends('x_uv_quantity', 'x_uv_subtotal')
    def _compute_uv_unit_price(self):
        for rec in self:
            rec.x_uv_unit_price = rec.x_uv_subtotal / rec.x_uv_quantity if rec.x_uv_quantity != 0 else 0



















