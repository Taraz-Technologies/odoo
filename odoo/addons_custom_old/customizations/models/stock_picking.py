from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

import time
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_backorder_products = fields.Boolean(string='Backorder Products?', required=False)

    x_customer_id = fields.Many2one('res.partner', string='Customer',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    help="Delivery address for current invoice.")
    x_partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address',
                                           domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                           help="Delivery address for current invoice.")
    x_end_user_id = fields.Many2one('res.partner', string='End user',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    help="Delivery address for current invoice.")
    x_update_partner_data = fields.Boolean(compute="_compute_partner_products_and_status")
    x_related_landed_cost_bill = fields.Many2one(comodel_name="account.move", string="Related LC Bill",
                                                 domain=[('type', '=', 'in_invoice')],
                                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                                 required=False, )
    x_attachment = fields.Binary(string="Attachment")
    x_task_id = fields.Many2one(comodel_name='project.task', string='Task')

    x_purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', required=False)
    # -------------------------------------- Certificates --------------------------------------
    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False, store=True,
                                      compute="get_sale_order")
    x_description_of_goods = fields.Selection(selection=[
        ('Power Electronic Development Kit', 'Power Electronic Development Kit'),
        ('Gate Driver Module', 'Gate Driver Module'),
        ('Isolated Voltage & Current Measurement Module', 'Isolated Voltage & Current Measurement Module'),
    ], string="Description of Goods", required=False, default='Power Electronic Development Kit', )
    x_application = fields.Selection(selection=[('R&D', 'R&D'), ('Educational', 'Educational'), ], string="Application",
                                     required=False, default='R&D', )
    x_awb = fields.Char(string="AWB#", required=False)
    x_number_of_boxes = fields.Integer(string="# of Boxes", required=False, default=1, )
    x_date_certificate = fields.Date(string="Date Certificate", required=False, readonly=False, )
    x_signatory_certificate = fields.Many2one(comodel_name="hr.employee", string="Signatory (Certificate)", required=False, )
    x_designation = fields.Char(string="Designation", required=False, store=True, compute='update_signatory_info', )
    x_cnic = fields.Char(string="CNIC#", required=False, store=True, compute='update_signatory_info', )
    x_body_letter_to_customs = fields.Text(string="Letter to Customs Body", required=False, store=True,
                                           compute='update_letter_to_customs_body', )
    x_body_undertaking = fields.Text(string="Undertaking Body", required=False, store=True,
                                     compute='update_undertaking_body', )
    # Quality Certificate
    x_date_certificate_quality = fields.Date(string="Date (Quality)", required=False)
    x_signatory_quality = fields.Many2one(comodel_name="hr.employee", string="Signatory (Quality)", required=False, )
    x_body_quality = fields.Text(string="Quality Certificate Body", required=False,
                                 default="This is to certify to the best of our knowledge and belief that following "
                                         "products have duly been inspected with the relevant specification and "
                                         "quantity, and confirmed that they have complied with the applicable "
                                         "requirements of your purchase order, our manufacturing standards and "
                                         "other pertinent criteria therewith: ", )
    # Warranty Certificate
    x_date_certificate_warranty = fields.Date(string="Date (Warranty)", required=False)
    x_signatory_warranty = fields.Many2one(comodel_name="hr.employee", string="Signatory (Warranty)", required=False, )
    x_body_warranty = fields.Text(string="Warranty Certificate Body", required=False,
                                  default="This is to certify that the item(s) described below shall be free from "
                                          "defects in material and workmanship per the attached Taraz Technologies "
                                          "Pvt. Ltd. warranty policy.", )
    # Request Letter
    x_date_certificate_rl = fields.Date(string="Date (Request Letter)", required=False)
    x_signatory_rl = fields.Many2one(comodel_name="hr.employee", string="Signatory (Request Letter)", required=False, )
    x_body_rl = fields.Text(string="Body (Request Letter)", compute="_compute_request_letter_body", store=True, readonly=False)
    # Shipper Undertaking
    x_date_certificate_su = fields.Date(string="Date (Shipper Undertaking)", required=False)
    x_signatory_su = fields.Many2one(comodel_name="hr.employee", string="Signatory (Shipper Undertaking)", required=False, )
    x_ups_account_no_su = fields.Char(string='UPS Account No. (Shipper Undertaking)', default="1AV998")
    x_body_su = fields.Html(string="Body (Shipper Undertaking)", compute="_compute_shipper_undertaking")
    # Routing Order Form
    x_date_certificate_rof = fields.Date(string="Date (Routing Order Form)", required=False)
    x_signatory_rof = fields.Many2one(comodel_name="hr.employee", string="Signatory (Routing Order Form)", required=False, )
    x_ups_account_no_rof = fields.Char(string='UPS Account No. (Routing Order Form)', default="1AV998")
    x_weight_rof = fields.Float(string='Weight (Routing Order Form)', required=False)
    x_body_rof = fields.Text(
        string="Body (Routing Order Form)",
        default="This is to inform you that we have chosen UPS as our transportation carrier. Please forward all UPS "
                "compatible package freight shipments to us through this carrier or their agents. The payment of "
                "freight of the shipments to UPS is guaranteed by account Holder. "
                "\nSee below for more service details. This form is valid for ______________ from the date of issuance."
    )

    # ---------------------------- Note Tab ----------------------------
    x_delivery_remarks = fields.Text(string="Delivery Remarks", required=False, )
    x_appear_delivery_remarks_on_report = fields.Boolean(string="Appear on Report", )

    # ---------------------------- Packaging Tab ----------------------------
    x_show_total_weights = fields.Boolean(string="Show Total Weights", )
    x_package_ids = fields.One2many(comodel_name="shipping.package", inverse_name="x_picking_id",
                                    string="Shipping Packages", required=False, )
    x_packing_list_ids = fields.One2many(
        comodel_name="packing.list", inverse_name="x_picking_id", string="Packing List", readonly=False,
    )

    # ---------------------------- Shipping Invoice Tab ----------------------------
    x_show_bill_to = fields.Boolean(string="Show Bill To?", default=True)
    x_show_customer = fields.Boolean(string="Show Customer?", )
    x_invoice_id = fields.Many2one(comodel_name="account.move", string="Payment Invoice",
                                   domain="["
                                          "('type', 'in', ('out_invoice', 'out_refund')), "
                                          "('company_id', '=', company_id)"
                                          "]", )
    x_shipping_invoice_number = fields.Char(string="Shipping Invoice#", required=False, )
    x_shipping_date = fields.Date(string="Shipping Date", required=False,)
    x_down_factor = fields.Float(string="Down Factor", required=False, default=1, )
    x_coo_value = fields.Float(string="COO Value", required=False, )
    x_sample_unit = fields.Boolean(string="Sample Unit Tag?", default=True, )

    x_hide_discount = fields.Boolean(string="Hide Discount?", )
    x_show_ship_to = fields.Boolean(string="Show Ship To", default=True)
    x_show_end_user = fields.Boolean(string="Show End-User", )
    x_show_freight = fields.Boolean(string="Show Freight?", )
    x_letter_head_report = fields.Boolean(string="Letter Head Report?", )
    x_hide_customer = fields.Boolean(string="Hide Customer?", )
    x_hide_product = fields.Boolean(string="Hide Product?", )
    x_distributor_order = fields.Boolean(string="Distributor Desc.?", )
    x_show_payment_terms = fields.Boolean(string='Payment Terms?', )
    x_show_payment_method = fields.Boolean(string="Payment Method?", )
    x_appear_shipping_remarks = fields.Boolean(string="Appear Remarks?", )
    x_shipping_remarks = fields.Text(string="Shipping Remarks", required=False, )

    x_picking_id = fields.Many2one(comodel_name="stock.picking", string="Shipped With", required=False)

    x_picking_ids = fields.Many2many(comodel_name="stock.picking", relation="stock_picking_stock_picking_rel_1",
                                     column1="stock_picking_id_1", column2="stock_picking_id_2", string="Add other DOs",
                                     domain="[('picking_type_code','=','outgoing')]")

    x_shipping_invoice_lines = fields.One2many(
        comodel_name='shipping.invoice.lines', inverse_name='picking_id',
        string='Shipping Invoice Lines', readonly=False,
    )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, )
    x_total_amount = fields.Monetary(string="Total", required=False, readonly=False, compute="_compute_shipping_total",
                                     store=True, )

    # ---------------------------- Journal Entries Tab ----------------------------
    x_journal_entries = fields.Many2many(
        comodel_name="account.move", relation="account_move_stock_picking_rel",
        column1="stock_picking_id", column2="account_move_id", string="Product Journal Entries",
        compute="_get_journal_entries",
    )

    # ---------------------------- Product Details Tab ----------------------------
    x_product_ids = fields.Many2many(comodel_name='product.product', string='Products')
    x_compute_products = fields.Boolean(compute="_compute_products", store=True)

    x_reason_of_export = fields.Char(string="Reason of Export")

    def compute_packing_list_data(self):
        self.x_packing_list_ids = [(2, line.id) for line in self.x_packing_list_ids]
        if self.x_shipping_invoice_lines:
            for rec in self.x_shipping_invoice_lines:
                self.x_packing_list_ids = [(0, 0, {
                        'x_product_id': rec.product_id.id,
                        'x_quantity': rec.quantity,
                    })]

    def button_validate(self):
        for rec in self:
            rec.x_backorder_products = False
        return super(Picking, self).button_validate()

    def write(self, vals):
        old_picking_ids = self.x_picking_ids.ids

        res = super(Picking, self).write(vals)

        if vals.get('x_picking_ids') is not None:
            remove_ids = [picking for picking in old_picking_ids if picking not in self.x_picking_ids.ids]
            picking_ids = self.env['stock.picking'].browse(remove_ids)
            picking_ids.write({'x_picking_id': False})
        return res

    def unlink(self):
        self.x_task_id.unlink()
        return super(Picking, self).unlink()

    def action_view_task(self):
        action = self.env.ref('customizations.act_purchase_order_project_task_all').read()[0]
        form_view = [(self.env.ref('project.view_task_form2').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_task_id.id
        return action

    def action_view_note(self):
        action = self.env.ref('cus_letters.action_res_help').read()[0]
        form_view = [(self.env.ref('cus_letters.res_help_view_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        model_id = self.env['ir.model']._get(self._name).id
        note_id = self.env['res.help'].search([('x_model_id', '=', model_id)], limit=1)
        action['res_id'] = note_id.id
        return action

    def _update_so_cgs_lines(self):
        for rec in self:
            if rec.origin:
                sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)])
                rec.x_sale_order_id = sale_order_id.id if sale_order_id else False
            if rec.x_sale_order_id:
                rec.x_sale_order_id.get_settings()

    def send_email(self):
        self._send_confirmation_email()

    @api.constrains('name')
    def get_addresses(self):
        for rec in self:
            if not rec.x_sale_order_id and rec.origin:
                sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)])
                rec.x_sale_order_id = sale_order_id.id if sale_order_id else False
            if rec.x_sale_order_id:
                rec.x_customer_id = rec.x_sale_order_id.partner_id.id
                rec.x_partner_invoice_id = rec.x_sale_order_id.partner_invoice_id.id
                rec.partner_id = rec.x_sale_order_id.partner_shipping_id.id
                rec.x_end_user_id = rec.x_sale_order_id.x_end_user.id

    # ---------------------------- ON CHANGE ----------------------------
    @api.onchange('x_backorder_products')
    def update_done_quantity(self):
        for rec in self:
            if rec.state not in ['done', 'cancel']:
                for line in rec.move_ids_without_package:
                    line.quantity_done = line.product_uom_qty

    # ---------------------------- DEPENDS ----------------------------
    @api.depends('move_ids_without_package', 'state')
    def _compute_products(self):
        for rec in self:
            product_ids = rec.move_ids_without_package.mapped('product_id')
            rec.x_product_ids = [(6, 0, product_ids.ids)]

    # @api.depends('origin', 'name', 'partner_id')
    # def _compute_task(self):
    #     for rec in self:
    #         if rec.picking_type_code in ['incoming'] and rec.name != 'New':
    #             if rec.picking_type_code == 'incoming':
    #                 name = 'Receipt'
    #                 project_id = 3
    #             else:
    #                 name = 'Delivery'
    #                 project_id = 2
    #
    #             name += ' - ' + str(rec.origin) if rec.origin else ''
    #             name += ' - ' + str(rec.name) if rec.name else ''
    #             name += ' - ' + str(rec.carrier_tracking_ref) if rec.carrier_tracking_ref else ''
    #
    #             order_id = self.env['purchase.order'].search([('name', '=', rec.origin)])
    #             if order_id:
    #                 name += ' - ' + str(order_id.x_forwarder_ref) if order_id.x_forwarder_ref else ''
    #
    #             name += ' - Backordered' if rec.backorder_id else ''
    #
    #             vals = {
    #                 'name': name,
    #                 'x_start_task_on': rec.scheduled_date.date() if rec.scheduled_date else False,
    #                 'project_id': project_id,
    #                 'x_picking_id': rec._origin.id,
    #             }
    #             task_id = self.env['project.task'].search([('x_picking_id', '=', rec._origin.id)])
    #             if not task_id:
    #                 task_id = self.env['project.task'].create(vals)
    #                 rec.x_task_id = task_id.id
    #             elif len(task_id) == 1:
    #                 task_id.write(vals)
    #                 rec.x_task_id = task_id.id

    @api.depends(
        'move_ids_without_package', 'state', 'x_customer_id', 'x_partner_invoice_id', 'partner_id', 'x_end_user_id'
    )
    def _compute_partner_products_and_status(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)], limit=1)
                if rec.picking_type_id.id == 2 and sale_order_id:
                    if rec.x_customer_id.id == rec.x_partner_invoice_id.id == rec.partner_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_partner_invoice_id.id == rec.partner_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_end_user_id)
                        sale_order_id.update_partner(rec.x_end_user_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_partner_invoice_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                    elif rec.x_customer_id.id == rec.partner_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                    elif rec.x_partner_invoice_id.id == rec.partner_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_partner_invoice_id.id and rec.partner_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                    elif rec.x_customer_id.id == rec.partner_id.id and rec.x_partner_invoice_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_end_user_id.id and rec.partner_id.id == rec.x_partner_invoice_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_partner_invoice_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                        sale_order_id.update_partner(rec.x_end_user_id)
                        sale_order_id.update_partner(rec.x_end_user_id.parent_id)
                    elif rec.x_customer_id.id == rec.partner_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                        sale_order_id.update_partner(rec.x_end_user_id)
                        sale_order_id.update_partner(rec.x_end_user_id.parent_id)
                    elif rec.x_customer_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                    elif rec.x_partner_invoice_id.id == rec.partner_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                        sale_order_id.update_partner(rec.x_end_user_id)
                        sale_order_id.update_partner(rec.x_end_user_id.parent_id)
                    elif rec.x_partner_invoice_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                    elif rec.partner_id.id == rec.x_end_user_id.id:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                    else:
                        sale_order_id.update_partner(rec.x_customer_id)
                        sale_order_id.update_partner(rec.x_customer_id.parent_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id)
                        sale_order_id.update_partner(rec.x_partner_invoice_id.parent_id)
                        sale_order_id.update_partner(rec.partner_id)
                        sale_order_id.update_partner(rec.partner_id.parent_id)
                        sale_order_id.update_partner(rec.x_end_user_id)
                        sale_order_id.update_partner(rec.x_end_user_id.parent_id)
            rec.x_update_partner_data = True

    x_apply_freight = fields.Selection(selection=[
        ('adjust', 'Adjust in Shipping Lines'),
        ('new_line', 'Create Freight Line'),
    ], string='Apply Freight',
        help=" * Adjust in Shipping Lines: Add freight amount in shipping lines by Subtotal.\n\
            * Create Freight Line: Create Separate Freight Line")

    def compute_shipping_invoice_data(self):
        for rec in self:
            rec.x_shipping_invoice_lines = [(2, line.id) for line in rec.x_shipping_invoice_lines]
            if rec.picking_type_code == 'outgoing':
                rec.x_shipping_invoice_number = ''
                if rec.x_down_factor != 0 and rec.x_down_factor and not rec.x_picking_id:
                    sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)], limit=1)
                    if not sale_order_id:
                        continue
                    rec.x_currency_id = sale_order_id.currency_id.id
                    multi_delivery = False
                    picking_ids = self.env['stock.picking'].browse(rec.x_picking_ids.ids)
                    picking_ids.write({'x_picking_id': rec._origin.id})
                    line_ids = rec.move_ids_without_package + picking_ids.mapped('move_ids_without_package')
                    shipping_invoice_lines = []
                    for line in line_ids:
                        shipping_invoice_lines.append((0, 0, {
                            'picking_id': rec._origin.id,
                            'product_id': line.product_id.id,
                            'name': line.product_id.x_short_description,
                            'hs_code_id': line.product_id.dk_hs_code.id if rec.company_id.id == 1 else line.product_id.x_hs_code_tr_id.id,
                            'country_id': line.product_id.x_country_id.id,
                            'weight': line.product_id.weight,
                            'quantity': line.product_uom_qty,
                            'product_uom_id': line.product_uom.id,
                            'unit_price': round(line.sale_line_id.price_unit / rec.x_down_factor, 2),
                            'discount': line.sale_line_id.discount,
                            'currency_id': sale_order_id.currency_id.id,
                            'amount': round(line.sale_line_id.price_unit
                                            * (1 - line.sale_line_id.discount / 100)
                                            * line.product_uom_qty / rec.x_down_factor, 2),
                        }))
                        if line.quantity_done != line.sale_line_id.product_uom_qty:
                            multi_delivery = True
                    rec.x_shipping_invoice_lines = shipping_invoice_lines
                    shipping_lines_total = sum(rec.x_shipping_invoice_lines.mapped('amount'))
                    value_diff = sale_order_id.amount_total - shipping_lines_total
                    if rec.x_apply_freight == 'adjust':
                        for line in rec.x_shipping_invoice_lines:
                            line.amount += round(line.amount / shipping_lines_total * value_diff, 2)
                    elif rec.x_apply_freight == 'new_line':
                        product_id = self.env['product.product'].browse(13813)
                        rec.x_shipping_invoice_lines = [(0, 0, {
                            'picking_id': rec._origin.id,
                            'product_id': product_id.id,
                            'name': 'Freight Charges',
                            'hs_code_id': False,
                            'country_id': False,
                            'weight': 0,
                            'quantity': 1,
                            'product_uom_id': product_id.uom_id.id,
                            'unit_price': round(value_diff, 2),
                            'discount': 0,
                            'currency_id': sale_order_id.currency_id.id,
                            'amount': round(value_diff, 2),
                        })]
                    rec._compute_shipping_total()

                    invoice = self.env['account.move'].search([
                        ('x_sale_order', '=', sale_order_id.id), ('state', '!=', 'cancel'),
                    ], limit=1)
                    if not invoice:
                        continue

                    rec.x_invoice_id = invoice.id
                    if rec.x_transit_invoice_id.x_old_number:
                        rec.x_shipping_invoice_number = rec.x_transit_invoice_id.x_old_number
                    elif (rec.x_transit_invoice_id.x_sale_tax_invoice_number
                          or rec.x_transit_invoice_id.x_appear_taraz_invoice_number):
                        rec.x_shipping_invoice_number = rec.x_transit_invoice_id.x_sale_tax_invoice_number
                    elif rec.x_transit_invoice_id:
                        rec.x_shipping_invoice_number = rec.x_transit_invoice_id.name
                    elif rec.x_invoice_id.x_old_number:
                        rec.x_shipping_invoice_number = rec.x_invoice_id.x_old_number
                    elif rec.x_invoice_id.x_sale_tax_invoice_number or rec.x_invoice_id.x_appear_taraz_invoice_number:
                        rec.x_shipping_invoice_number = rec.x_invoice_id.x_sale_tax_invoice_number
                    else:
                        rec.x_shipping_invoice_number = rec.x_invoice_id.name

                    for line in sale_order_id.order_line:
                        if line.product_id.type != 'service' and line.product_id not in rec.move_ids_without_package.mapped(
                                'product_id'):
                            multi_delivery = True
                            break

                    if multi_delivery and rec.x_shipping_invoice_number:
                        delivery_shipping_invoice_numbers = self.env['stock.picking'].search([
                            ('x_shipping_invoice_number', 'ilike', rec.x_shipping_invoice_number)
                        ]).mapped('x_shipping_invoice_number')
                        if rec.x_shipping_invoice_number + '-A' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-A'
                        elif rec.x_shipping_invoice_number + '-B' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-B'
                        elif rec.x_shipping_invoice_number + '-C' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-C'
                        elif rec.x_shipping_invoice_number + '-D' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-D'
                        elif rec.x_shipping_invoice_number + '-E' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-E'
                        elif rec.x_shipping_invoice_number + '-F' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-F'
                        elif rec.x_shipping_invoice_number + '-G' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-G'
                        elif rec.x_shipping_invoice_number + '-H' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-H'
                        elif rec.x_shipping_invoice_number + '-I' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-I'
                        elif rec.x_shipping_invoice_number + '-J' not in delivery_shipping_invoice_numbers:
                            rec.x_shipping_invoice_number += '-J'

    @api.depends('x_shipping_invoice_lines.amount')
    def _compute_shipping_total(self):
        for rec in self:
            rec.x_total_amount = sum(rec.x_shipping_invoice_lines.mapped('amount'))

    @api.depends('state')
    def _get_journal_entries(self):
        for rec in self:
            if rec.picking_type_code in ['outgoing', 'incoming'] and rec.state == 'done':
                rec.x_journal_entries = [(6, 0, rec.move_lines.mapped('account_move_ids').ids)]
            else:
                rec.x_journal_entries = False

    @api.constrains('origin')
    @api.depends('x_date_certificate', 'origin')
    def get_sale_order(self):
        for rec in self:
            if rec.origin:
                sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)])
                rec.x_sale_order_id = sale_order_id.id if sale_order_id else False

    @api.depends('x_signatory_certificate')
    def update_signatory_info(self):
        for record in self:
            record.x_designation = record.x_signatory_certificate.job_id.name
            record.x_cnic = record.x_signatory_certificate.identification_id

    @api.depends('x_description_of_goods', 'x_application')
    def update_letter_to_customs_body(self):
        for record in self:
            record.x_body_letter_to_customs = "Taraz Technologies is a power electronics Research and Development Company " \
                                              "based in Pakistan. Our product portfolio includes AC/DC Current & Voltage " \
                                              "Probes, Data Acquisition Systems, DC-DC Converters, IGBT/MOSFET Gate " \
                                              "Drivers and Inverter modules. Product being shipped is " + \
                                              record.x_description_of_goods + " to be used for " + \
                                              record.x_application + " purpose. Kindly allow us to export following:"

    @api.depends('x_signatory_certificate', 'x_cnic', 'x_awb', 'carrier_id')
    def update_undertaking_body(self):
        for record in self:
            record.x_body_undertaking = "I, " + str(record.x_signatory_certificate.name).upper() + " HOLDING CNIC # " \
                                        + str(record.x_cnic) + " HEREBY DECLARE THAT THE CONTENTS OF THE SHIPMENT " \
                                                               "UNDER AWB # " + str(
                record.x_awb) + " CONTAINS NO CONTRABAND COMMODITY INCLUSIVE " \
                                "OF CASH, JEWELLERY, CASH EQUIVALENT, PAKISTANI, AFGHANI, & INDIAN PASSPORTS, " \
                                "NORCOTICS, EXPLOSIVE, ANTIQUES OR ANYOTHER CONTRABAND ITEMS ACCORDING TO THE IATA " \
                                "RULES AND REGULATIONS.\n\n" + str(
                record.carrier_id.name).upper() + " RESERVES THE RIGHT TO INVOLVE LOCAL AUTHORITIES " \
                                                  "IF SHIPMENT CONTAINS SUCH ITEMS."

    @api.depends('partner_id', 'x_date_certificate_rl', 'x_signatory_rl')
    def _compute_request_letter_body(self):
        for rec in self:
            rec.x_body_rl = (
                "I need to attest the following document:"
                "\n"
                "\nCertificate of Origin"
                "\nCustomer: %s"
                "\n"
                "\nThe document provided is true and correct to the best of my knowledge. "
                "\nAll financial and legal obligations pertaining to this document fall on company's part."
                % rec.partner_id.commercial_partner_id.name
            )

    @api.depends('partner_id', 'x_date_certificate_su', 'x_signatory_su', 'x_ups_account_no_su', 'x_awb')
    def _compute_shipper_undertaking(self):
        for rec in self:
            rec.x_body_su = (
                "<p>"
                    "<b>"
                        "SUBJECT: <span style='text-decoration: underline;'>UNDERTAKING FOR FREIGHT COLLECT SHIPMENT</span>"
                    "</b>"
                "</p>"
                "<p style='text-align:justify;'>"
                    "WE " + str(rec.company_id.name).upper() + " HEREBY UNDERTAKES TO INDEMNIFY UNIVERSAL LOGISTICS "
                    "SERVICES (PVT.) LTD; AUTHORISED SERVICE CONTRACTOR FOR UPS, AND TO SETTLE ALL PAYMENTS INCLUDING "
                    "SURCHARGES IN RESPECT OF EXPRESS PARCEL / DOCUMENTS SENT THROUGH ULS UNDER UPS AWB# " + str(rec.x_awb) +
                    " IN CASE OF NON-PAYMENT BY OUR CONSIGNEE " + str(rec.partner_id.commercial_partner_id.name).upper() +
                "</p>"
                "<p>""<b>TERM & CONDITIONS</b>""</p>"
                "<ol style='text-align:justify;list-style-type: decimal; margin-left: 50px'>"
                    "<li>"
                        "WE WILL BEAR THE LIABILITY OF CHARGES COLLECT / REVERSAL CHARGES PAYMENT INCLUDING ANY "
                        "SURCHARGE RETURN FREIGHT, DUTY, TAXES, GODOWN RENT AND ANY OTHER CHARGES INCURRED."
                    "</li>"
                    "<li>"
                         + str(rec.x_ups_account_no_su) + " ACCOUNT NUMBER WITH UPS DOES NOT GUARANTEE PAYMENT TO ULS/UPS "
                        "PK AND LIABILITY REMAINS WITH US."
                    "</li>"
                    "<li>"
                        "IN CASE OF REVERSAL CHARGES CONSIGNEE WILL NOT BE CONTACTED REPEATEDLY AND WE WILL PAY TO UNIVERSAL "
                        "LOGISTICS SERVICES (PVT.) LTD WHATEVER THE CHARGES DEBITED BY UPS INTERNATIONAL TO ULS PLUS 15% "
                        "REVERSAL SURCHARGES WITHIN 7 DAYS OF INTIMATION IN WRITING BY UNIVERSAL LOGISTICS SERVICES (PVT.) LTD. "
                        "FAILURE TO MAKE REVERSAL PAYMENT WITHIN 7 DAYS OF DELIVERY OF BILL WILL RESULT IN LEVY OF 0.10% PER "
                        "DAY FINANCIAL CHARGES."
                    "</li>"
                    "<li>"
                        "ULS RESERVES THE RIGHT TO CLAIM FREIGHT AMOUNT PLUS 15% REVERSAL SURCHARGES AND EXPENSES AS MENTIONED "
                        "IN PARA 1 FROM US, IF THE AMOUNT IS NOT PAID BY OUR CONSIGNEE, IRRESPECTIVE OF WHATEVER THE REASONS "
                        "I.E. MARKING ERRORS IN AIRWAY BILL’S PRE-PAID COLUMN INSTEAD OF COLLECT, REFUSAL TO ACCEPT DELIVERY "
                        "OR REQUEST TO ABANDON SHIPMENT, NON PAYMENT OF DUTY AND TAXES ETC."
                    "</li>"
                    "<li>"
                        "WE ARE RESPONSIBLE FOR PAYMENT TO ULS/UPS PK ON BEHALF OF OUR CLIENT IN TERMS OF ABOVE CONDITIONS. "
                        "AGAINST IRRESPECTIVE OF HIS BUSINESS HAS BEEN CLOSE WITH OUR CONSIGNEE OR NOT."
                    "</li>"
                "</ol>"
                "<p style='margin-top: 50px'>"
                    "<table style='width: 100%;'>"
                        "<tbody>"
                            "<tr style='height: 75px'>"
                                "<td style='width: 50%;'>"
                                    "Name:<br/>" + str(rec.x_signatory_su.name) +
                                "</td>"
                                "<td style='width: 50%;'>"
                                    "Signature:"
                                "</td>"
                            "</tr>"
                            "<tr style='height: 75px'>"
                                "<td>"
                                    "Company Name:<br/>" + str(rec.company_id.name) +
                                "</td>"
                                "<td>"
                                    "Company Stamp:"
                                "</td>"
                            "</tr>"
                        "</tbody>"
                    "</table>"
                    "Date: " + str(rec.x_date_certificate_su) +
                "</p>"
            )


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Display Name', required=True)
    x_type = fields.Selection(selection=[
        ('n/a', 'N/A'),
        ('direct', 'Direct'),
        ('forwarder', 'Forwarder'), ], string='Type', required=True, )
    x_contact_id = fields.Many2one(comodel_name='res.partner', string='Contact', required=False)

    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        res = super(StockPickingType, self)._compute_picking_count()
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                   ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': ['|', ('x_backorder_products', '!=', False), ('backorder_id', '!=', False),
                                         ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                                                        [('state', 'not in', ('done', 'cancel')),
                                                         ('picking_type_id', 'in', self.ids)],
                                                        ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0

        return res


class ShippingInvoiceLines(models.Model):
    _name = "shipping.invoice.lines"
    _description = "Shipping Invoice Lines"
    _rec_name = "display_name"

    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice ID", )
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Delivery Order", )

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    name = fields.Text(string="Description", required=False, )
    quantity = fields.Float(string="Quantity", required=False, )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", required=False, )
    unit_price = fields.Float(string="Unit Price", required=False, )
    discount = fields.Float(string="Disc (%)", required=False, )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, )
    amount = fields.Monetary(string="Subtotal", compute="compute_subtotal", store=True, )

    @api.depends('quantity', 'unit_price', 'discount')
    def compute_subtotal(self):
        for rec in self:
            rec.amount = round(rec.quantity * rec.unit_price * (1 - rec.discount / 100), 2)




