from odoo import api, fields, models

import datetime
import logging

_logger = logging.getLogger("*__addons_custom__*")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_end_user = fields.Many2one(comodel_name="res.partner", string="End-User", tracking=True)
    x_update_partner_data = fields.Boolean(
        string="Update Partner Data",
        compute="_compute_partner_products_and_status",
        store=True, tracking=True,
    )
    x_customer_po = fields.Binary(string="Customer PO", tracking=True)
    x_web_order_number = fields.Char(string="WEB Order#", tracking=True)
    x_lead_time = fields.Selection(selection=[('1', '1 day'),
                                              ('2-3 days', '2-3 days'),
                                              ('1 week', '1 week'),
                                              ('2 weeks', '2 weeks'),
                                              ('3 weeks', '3 weeks'),
                                              ('4 weeks', '4 weeks'),
                                              ('5 weeks', '5 weeks'),
                                              ('6 weeks', '6 weeks'),
                                              ('7 weeks', '7 weeks'),
                                              ('8 weeks', '8 weeks'),
                                              ('10 weeks', '10 weeks'),
                                              ('12 weeks', '12 weeks'),
                                              ('18 weeks', '18 weeks'),
                                              ('6 months', '6 months'),
                                              ('1 year', '1 year'),
                                              ('2 years', '2 years'), ], string="Lead Time", tracking=True)
    x_folder_name = fields.Char(string="Folder Name", required=False, readonly=True, compute="update_folder_name",
                                store=True, tracking=True)
    x_sale_type = fields.Selection(selection=[
        ('Investment', 'Investment'),
        ('Export / WeBoc', 'Export / WeBoc [EG]'),
        ('Export / Speedy', 'Export / Speedy [ES]'),
        ('Export / Services', 'Export / Services [ES]'),
        ('Domestic / Unofficial', 'Domestic / Unofficial [DU]'),
        ('Domestic Goods / Official', 'Domestic Goods / Official [DG]'),
        ('Domestic Services / Official', 'Domestic Services / Official [DS]'),
        ('Internal / Employee', 'Internal / Employee [IE]'),
    ], string="Sale Type", tracking=True)
    x_sale_type_turkey = fields.Selection(selection=[
        ('export', 'Export'),
        ('domestic', 'Domestic'),
        ('dropship_av', 'Dropship AV'),
        ('dropship_uv', 'Dropship UV'),
        ('cbm_av', 'CBM AV'),
        ('cbm_uv', 'CBM UV'),
    ], default="export", string="Sale Type (TR)", tracking=True)
    x_payment_method = fields.Many2one(comodel_name="account.journal", string="Payment Method", tracking=True)
    x_tracking_reference = fields.Char(string="Tracking Reference", required=False, compute="_compute_tracking_ref",
                                       store=True, tracking=True)
    x_internal_notes = fields.Text(string="Internal Notes", tracking=True)
    x_contain_pelab = fields.Boolean(string="Contain PELab", compute="_compute_contain_pelab", store=True,
                                     tracking=True)
    x_upcoming = fields.Boolean(string="Upcoming", default=True, copy=False, tracking=True)

    x_deadline = fields.Datetime(string="Deadline", required=False, store=True, compute="update_deadline", readonly=False)
    x_production_deadline = fields.Datetime(string="Prd. Deadline", required=False, store=True, compute="update_deadline", readonly=False)
    # -------------------------------------- Order Lines --------------------------------------
    x_ui_value = fields.Monetary(string="UI Value", tracking=True)
    x_total_without_discount = fields.Monetary(string="Total without Discount", required=False,
                                               compute="_compute_total", store=True, tracking=True)
    x_total_discount = fields.Monetary(string="Total Discount", required=False, compute="_compute_total",
                                       store=True, tracking=True)
    x_total_cgs = fields.Monetary(string="Total Cost", required=False, readonly=True, compute="compute_sale_order_cost",
                                  store=True, tracking=True)
    x_total_profit = fields.Monetary(string="Total Profit", required=False, readonly=True,
                                     compute="compute_sale_order_cost", store=True)
    x_estimated_profit = fields.Monetary(string="Estimated Profit", required=False, readonly=True,
                                         compute="compute_sale_order_cost", store=True)
    x_profit_margin = fields.Float(string="Profit Margin", required=False, readonly=True,
                                   compute="compute_sale_order_cost", store=True)
    x_estimated_profit_margin = fields.Float(string="Estimated Profit Margin", required=False, readonly=True,
                                             compute="compute_sale_order_cost", store=True)
    # -------------------------------------- Report Data --------------------------------------
    x_show_bill_to = fields.Boolean(string="Show Bill To", default=True)
    x_show_customer = fields.Boolean(string="Show Customer", )
    x_letter_head_report = fields.Boolean(string="Letter Head Report?", )
    x_hs_code_and_coo = fields.Boolean(string="HS Code & COO?", )
    x_distributor_order = fields.Boolean(string="Distributor Desc.?", )
    x_hide_customer = fields.Boolean(string="Hide Customer?", )
    x_hide_product = fields.Boolean(string="Hide Product?", )
    x_hide_discount = fields.Boolean(string="Hide Disc. Column?", )
    x_hide_discount_description = fields.Boolean(string="Hide Disc. Desc.?", )
    x_hide_gst = fields.Boolean(string="Hide GST?", )
    x_show_sale_person = fields.Boolean(string="Show Sales Person?", )
    x_remove_proforma = fields.Boolean(string="Remove Pro-Forma", )
    x_date_docs = fields.Date(string="Docs Date", required=False, readonly=False, )

    x_show_ship_to = fields.Boolean(string="Show Ship To", default=True)
    x_show_end_user = fields.Boolean(string="Show End-User", )
    x_appear_payment_method = fields.Boolean(string="Payment Method?", )
    x_appear_pt_table = fields.Boolean(string="Payment Terms Table?", )
    x_attach_short_terms = fields.Boolean(string="Show T&C Remark?", )
    x_attach_long_terms = fields.Boolean(string="Attach T&C?", )
    x_appear_gst_withheld = fields.Boolean(string="Show GST Withheld?", )
    x_appear_it_withheld = fields.Boolean(string="Show IT Withheld?", )
    x_appear_paypal_link = fields.Boolean(string="Show Paypal Link?", )
    x_appear_banking_details = fields.Boolean(string="Show Banking Details?", )
    x_bank = fields.Many2one(comodel_name="payment.acquirer", string="Payment Acquirer",
                             compute="_update_payment_acquirer", store=True, tracking=True)
    # -------------------------------------- Freight Calculation --------------------------------------
    x_sale_order_product_ids = fields.One2many(comodel_name="sale.order.products", inverse_name="x_sale_order_id",
                                               string="Products", required=False, readonly=False,
                                               compute="compute_shipment_product", store=True, )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2, )

    x_shipment_weight = fields.Float(string="Shipment Weight", required=False, readonly=False,
                                     compute="compute_shipment_weight", store=True, )
    x_dhl_export_zone = fields.Many2one(comodel_name="shipping.zone", string="DHL Export Zone", required=False,
                                        related="x_delivery_country.x_dhl_export_zone")
    x_dhl_weight_from = fields.Float(string="Weight from", required=False, compute="shipment_freight_calculation",
                                     store=True, )
    x_dhl_weight_to = fields.Float(string="Weight to", required=False, compute="shipment_freight_calculation",
                                   store=True, )
    x_dhl_shipping_rate = fields.Float(string="DHL Shipping Rate", required=False,
                                       compute="shipment_freight_calculation", store=True, )

    x_delivery_country = fields.Many2one(comodel_name="res.country", string="Destination Country", required=False,
                                         related="partner_shipping_id.country_id")
    x_ups_export_zone = fields.Many2one(comodel_name="shipping.zone", string="UPS Export Zone", required=False,
                                        related="x_delivery_country.x_ups_export_zone")
    x_ups_weight_from = fields.Float(string="Weight from", required=False, compute="shipment_freight_calculation",
                                     store=True, )
    x_ups_weight_to = fields.Float(string="Weight to", required=False, compute="shipment_freight_calculation",
                                   store=True, )
    x_ups_shipping_rate = fields.Float(string="UPS Shipping Rate", required=False,
                                       compute="shipment_freight_calculation", store=True, )

    x_dhl_charges = fields.One2many(comodel_name="dhl.additional.charges", inverse_name="x_sale_order_id",
                                    string="DHL Charges", required=False, )
    x_total_dhl = fields.Float(string="Total", required=False, compute="shipment_freight_calculation", store=True, )
    x_ups_charges = fields.One2many(comodel_name="ups.additional.charges", inverse_name="x_sale_order_id",
                                    string="UPS Charges", required=False, )
    x_total_ups = fields.Float(string="Total", required=False, compute="shipment_freight_calculation", store=True, )
    # -------------------------------------- Cost of Goods Sold --------------------------------------
    x_costing_complete = fields.Boolean(string="Costing is Complete", store=True, compute="_check_costing", )
    x_inclusive_of_bonus = fields.Boolean(string="Consider Bonus", )
    x_inclusive_of_investor_profit = fields.Boolean(string="Consider Inv. Share", )
    x_inclusive_of_currency = fields.Boolean(string="Consider Currency", )
    x_inclusive_of_other_costs = fields.Boolean(string="Consider Other Costs", )

    x_price = fields.Float(string="Price", required=False, compute="_compute_amounts", store=True, )
    x_cost = fields.Float(string="Cost", required=False, compute="_compute_amounts", store=True, )
    x_profit = fields.Float(string="Profit", required=False, compute="_compute_amounts", store=True, )
    x_cost_percentage = fields.Float(string="Cost (%)", required=False, compute="_compute_amounts", store=True, )
    x_profit_percentage = fields.Float(string="Profit (%)", required=False, compute="_compute_amounts", store=True, )
    x_cost_multiplier = fields.Float(string="Cost Multiplier", required=False, compute="_compute_amounts", store=True, )
    x_markup = fields.Float(string="Markup (%)", required=False, compute="_compute_amounts", store=True, )

    x_product = fields.Boolean(string="Product", default=True, )
    x_freight = fields.Boolean(string="Freight", default=True, )
    x_discount = fields.Boolean(string="Discount", default=True, )
    x_fees = fields.Boolean(string="Fees", default=True, )
    x_other_real = fields.Boolean(string="Other Real", default=True, )
    x_other_estimated = fields.Boolean(string="Other Estimated", )
    x_bonus = fields.Boolean(string="Bonus", )
    x_investor_share = fields.Boolean(string="Investor Share", )
    x_currency = fields.Boolean(string="Currency", )

    x_product_price = fields.Char(string="Product Price", compute="_compute_amounts", store=True, )
    x_freight_price = fields.Char(string="Freight Price", compute="_compute_amounts", store=True, )
    x_discount_price = fields.Char(string="Discount Price", compute="_compute_amounts", store=True, )
    x_fees_price = fields.Char(string="Fees Price", compute="_compute_amounts", store=True, )
    x_other_real_price = fields.Char(string="Other Real Price", compute="_compute_amounts", store=True, )
    x_other_estimated_price = fields.Char(string="Other Estimated Price", compute="_compute_amounts", store=True, )
    x_bonus_price = fields.Char(string="Bonus Price", compute="_compute_amounts", store=True, )
    x_investor_share_price = fields.Char(string="Investor Share Price", compute="_compute_amounts", store=True, )
    x_currency_price = fields.Char(string="Currency Price", compute="_compute_amounts", store=True, )

    x_product_cost = fields.Char(string="Product Cost", compute="_compute_amounts", store=True, )
    x_freight_cost = fields.Char(string="Freight Cost", compute="_compute_amounts", store=True, )
    x_discount_cost = fields.Char(string="Discount Cost", compute="_compute_amounts", store=True, )
    x_fees_cost = fields.Char(string="Fees Cost", compute="_compute_amounts", store=True, )
    x_other_real_cost = fields.Char(string="Other Real Cost", compute="_compute_amounts", store=True, )
    x_other_estimated_cost = fields.Char(string="Other Estimated Cost", compute="_compute_amounts", store=True, )
    x_bonus_cost = fields.Char(string="Bonus Cost", compute="_compute_amounts", store=True, )
    x_investor_share_cost = fields.Char(string="Investor Share Cost", compute="_compute_amounts", store=True, )
    x_currency_cost = fields.Char(string="Currency Cost", compute="_compute_amounts", store=True, )

    x_product_profit = fields.Char(string="Product Profit", compute="_compute_amounts", store=True, )
    x_freight_profit = fields.Char(string="Freight Profit", compute="_compute_amounts", store=True, )
    x_discount_profit = fields.Char(string="Discount Profit", compute="_compute_amounts", store=True, )
    x_fees_profit = fields.Char(string="Fees Profit", compute="_compute_amounts", store=True, )
    x_other_real_profit = fields.Char(string="Other Real Profit", compute="_compute_amounts", store=True, )
    x_other_estimated_profit = fields.Char(string="Other Estimated Profit", compute="_compute_amounts", store=True, )
    x_bonus_profit = fields.Char(string="Bonus Profit", compute="_compute_amounts", store=True, )
    x_investor_share_profit = fields.Char(string="Investor Share Profit", compute="_compute_amounts", store=True, )
    x_currency_profit = fields.Char(string="Currency Profit", compute="_compute_amounts", store=True, )

    x_cgs_line_ids = fields.One2many(comodel_name="sale.order.cgs", inverse_name="x_sale_order_id", string="CGS Lines",
                                     required=False, )
    # -------------------------------------- Other Info --------------------------------------
    x_team_member_ids = fields.Many2many(comodel_name="res.partner", relation="sale_order_res_partner_rel",
                                         column1="sale_order_id", column2="res_partner_id", string="Team Members", )
    x_sale_tax_invoice_number = fields.Char(string="Taraz Invoice#", required=False, )
    x_update_freight = fields.Boolean(string="Update Freight", )
    x_total_freight = fields.Float(string="Total Freight", required=False, compute="freight_calculation", store=True, )
    x_total_weight = fields.Float(string="Total Weight", required=False, compute="freight_calculation", store=True, )
    x_freight_per_kg = fields.Float(string="Freight per KG", required=False, compute="freight_calculation", store=True, )
    x_exclude_from_dashboard = fields.Selection(string="Exclude From DSHBD?", selection=[('Yes', 'Yes'), ('No', 'No'), ], required=False, )
    x_date_dashboard = fields.Date(string='Dashboard Date', required=False)
    x_so_payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
    ], required=False, string='Payment', default='not_paid')

    @api.onchange('x_exclude_from_dashboard')
    def update_invoice_exclude_from_dashboard(self):
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
            invoices.update({'x_exclude_from_dashboard': order.x_exclude_from_dashboard})

    # -------------------------------------- Stock Level --------------------------------------
    x_stock_status = fields.Selection(string="Stock Status",
                                      selection=[('In Stock', 'In Stock'), ('Out of Stock', 'Out of Stock')],
                                      required=False, )
    x_packing_type = fields.Selection(string="Packing Type", selection=[('Wooden Packing', 'Wooden Packing'), ],
                                      required=False, )
    x_stock_level = fields.Many2many(comodel_name="product.product", relation="product_product_sale_order_rel_1",
                                     column1="sale_order_id", column2="product_product_id",
                                     string="Items stock level", )
    # -------------------------------------- Sale Order Task --------------------------------------
    x_task_id = fields.Many2one(comodel_name="project.task", string="Task", required=False, store=True, copy=False, )
    x_task_stage_id = fields.Many2one(comodel_name="project.task.type", string="Task Stage", readonly=False,
                                      related="x_task_id.stage_id", )
    x_task_name = fields.Char(string="Name", required=False, store=True, compute="update_task_name", )
    x_user_responsible = fields.Many2one(comodel_name="res.users", string="Responsible User", required=False,
                                         default=28, )
    x_user_participants = fields.Many2many(comodel_name="res.users", relation="res_users_sale_order_rel_1",
                                           column1="sale_order_id", column2="res_users_id", string="Participants", )
    x_user_observers = fields.Many2many(comodel_name="res.users", relation="res_users_sale_order_rel_2",
                                        column1="sale_order_id", column2="res_users_id", string="Observers")
    x_start_task_on = fields.Datetime(string="Start task on", required=False, store=True,
                                      compute="update_start_task_on")
    x_processes = fields.Many2many(comodel_name="processes", relation="sale_order_processes_rel",
                                   column1="sale_order_id", column2="processes_id", string="Processes",
                                   domain="[('x_models', 'ilike', active_model)]", default=[5, 6, 7], )
    x_notes = fields.Text(string="Notes", required=False, )
    x_tag_ids = fields.Many2many('project.tags', string='Tags', compute="_compute_tags", store=True, tracking=True)
    x_tasks = fields.Many2many(comodel_name="tasks", relation="sale_order_tasks_rel", store=True,
                               column1="sale_order_id", column2="tasks_id", string="Task", compute="update_task_list")
    x_content_title = fields.Char(string='Content Title', required=False)
    x_content_text = fields.Html(string='Content Text', required=False)
    x_content_show = fields.Boolean(string='Show Content?', required=False)
    x_update_tags = fields.Boolean(string='Update Tags', compute="_compute_task_tags", store=True)

    x_is_commented = fields.Boolean(string="Has Notes", compute="_compute_is_commented")

    @api.depends('x_internal_notes')
    def _compute_is_commented(self):
        for record in self:
            record.x_is_commented = bool(record.x_internal_notes)

    def action_show_notes(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.id,
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            if rec.date_order:
                rec.x_date_dashboard = rec.date_order.date()
        self.update_so_task_on_confirmation()
        return res

    # -----------------------------------------FUNCTIONS-------------------------------------------
    def add_bos_products(self):
        for rec in self:
            for line in rec.order_line:
                bos_product_ids = self.env['product.product'].search([('x_main_product_id', '=', line.product_id.id)])
                for bos_product in bos_product_ids:
                    if bos_product.id not in rec.order_line.mapped('product_id').ids:
                        rec.order_line = [(0, 0, {
                            'product_id': bos_product.id,
                            'product_uom_qty': line.product_uom_qty,
                        })]

    def get_settings(self):
        for rec in self:
            rec.x_inclusive_of_bonus = self.env['ir.config_parameter'].sudo().get_param('sale.x_inclusive_of_bonus')
            rec.x_inclusive_of_investor_profit = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_investor_profit')
            rec.x_inclusive_of_currency = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_currency')
            rec.x_inclusive_of_other_costs = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_other_costs')
            rec.update_cgs_lines()
            rec._compute_amounts()

    def upcoming_order(self):
        for rec in self:
            upcoming_tag_id = self.env['project.tags'].search([('name', '=', 'Upcoming')], limit=1).id
            rec.x_tag_ids = [upcoming_tag_id]
            rec.x_upcoming = False
            if rec.company_id.id == 2:
                continue
            if not rec.x_task_id:
                rec.create_project_task()
            else:
                rec.update_project_task()

    def create_project_task(self):
        for rec in self:
            if not rec.x_user_responsible:
                rec.x_user_responsible = 28

            vals = {
                'name': rec.x_task_name,
                'project_id': 2,
                'stage_id': 26,
                'user_id': rec.x_user_responsible.id,
                'x_user_participants': rec.x_user_participants,
                'x_user_observers': rec.x_user_observers,
                'x_start_task_on': rec.x_start_task_on,
                'date_deadline': rec.x_deadline if rec.state not in ['draft', 'sent'] else False,
                'x_notes': rec.x_notes,
                'tag_ids': rec.x_tag_ids.ids,
                'x_sale_order_id': rec._origin.id,
                'x_subtask_list': [(0, 0, {
                    'x_name': task.x_name,
                    'x_user_id': task.x_user_responsible.id,
                    'x_user_participants': task.x_user_participants.ids,
                    'x_user_observers': task.x_user_observers.ids,
                    'x_notes': task.x_description,
                    'x_checklist_items': task.x_checklist_items.ids,
                    'x_project_id': task.x_project_id.id,
                    'x_project_stage_id': task.x_project_stage_id.id,
                    'x_deadline': rec.x_deadline if rec.state not in ['draft', 'sent'] else False,
                }) for task in rec.x_tasks],
            }
            task = self.env['project.task'].create(vals)
            rec.x_task_id = task.id
            if rec.x_task_id.x_subtask_list:
                rec.x_task_id.x_subtask_list_hide = False

    def update_so_task_on_confirmation(self):
        for rec in self:
            confirmation_tag_id = self.env['project.tags'].search([('name', '=', 'Payment Pending')], limit=1).id
            rec.x_tag_ids = [confirmation_tag_id]
            if rec.company_id.id == 2:
                continue
            if not rec.x_task_id:
                rec.create_project_task()
            else:
                rec.update_project_task()
            rec.x_task_id.stage_id = 4

    def delete_so_task_on_cancel(self):
        for rec in self:
            if rec.company_id.id == 2:
                continue
            if rec.x_task_id:
                rec.update_project_task()
                rec.x_task_id.stage_id = 258

    def create_delivery(self):
        for rec in self:
            if rec.state == 'done':
                rec.action_unlock()
            rec.action_confirm()

    def action_view_task(self):
        action = self.env.ref('customizations.act_sale_order_project_task_all').read()[0]
        form_view = [(self.env.ref('project.view_task_form2').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.x_task_id.id
        return action

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        for record in self:
            invoice_vals['journal_id'] = record.company_id.x_payment_invoice_journal_id.id
            invoice_vals['invoice_date'] = record.date_order.date()
            invoice_vals['x_customer_id'] = record.partner_id.id
            invoice_vals['x_end_user_id'] = record.x_end_user.id
            invoice_vals['invoice_incoterm_id'] = record.incoterm.id
            invoice_vals['x_payment_method'] = record.x_payment_method.id
            invoice_vals['x_sale_order'] = record.id
            invoice_vals['x_web_order_number'] = record.x_web_order_number
            invoice_vals['x_sale_type_turkey'] = record.x_sale_type_turkey
            invoice_vals['x_sale_type'] = record.x_sale_type
            invoice_vals['x_tracking_reference'] = record.x_tracking_reference
            invoice_vals['x_delivery_method'] = record.carrier_id.id
            invoice_vals['narration'] = record.x_internal_notes
            invoice_vals['x_exclude_from_dashboard'] = record.x_exclude_from_dashboard

            invoice_vals['x_show_bill_to'] = record.x_show_bill_to
            invoice_vals['x_show_customer'] = record.x_show_customer
            invoice_vals['x_letter_head_report'] = record.x_letter_head_report
            invoice_vals['x_hs_code_and_coo'] = record.x_hs_code_and_coo
            invoice_vals['x_distributor_order'] = record.x_distributor_order
            invoice_vals['x_hide_customer'] = record.x_hide_customer
            invoice_vals['x_hide_product'] = record.x_hide_product
            invoice_vals['x_hide_discount'] = record.x_hide_discount
            invoice_vals['x_hide_gst'] = record.x_hide_gst

            invoice_vals['x_show_ship_to'] = record.x_show_ship_to
            invoice_vals['x_show_end_user'] = record.x_show_end_user
            invoice_vals['x_appear_payment_method'] = record.x_appear_payment_method
            invoice_vals['x_appear_pt_table'] = record.x_appear_pt_table
            invoice_vals['x_appear_gst_withheld'] = record.x_appear_gst_withheld
            invoice_vals['x_appear_it_withheld'] = record.x_appear_it_withheld
            invoice_vals['x_appear_paypal_link'] = record.x_appear_paypal_link
            invoice_vals['x_appear_banking_details'] = record.x_appear_banking_details
            invoice_vals['x_remarks'] = record.note
            invoice_vals['x_bank'] = record.x_bank.id
        return invoice_vals

    def update_partner(self, partner_id):
        sale_order_ids = self.env['sale.order'].search([
            '|', '|', '|', '|', '|', '|', '|', '|', '|',
            ('partner_id', '=', partner_id.id),
            ('partner_invoice_id', '=', partner_id.id),
            ('partner_shipping_id', '=', partner_id.id),
            ('x_end_user', '=', partner_id.id),
            ('x_team_member_ids', 'ilike', partner_id.id),
            ('partner_id', 'in', partner_id.child_ids.ids),
            ('partner_invoice_id', 'in', partner_id.child_ids.ids),
            ('partner_shipping_id', 'in', partner_id.child_ids.ids),
            ('x_end_user', 'in', partner_id.child_ids.ids),
            ('x_team_member_ids', 'ilike', partner_id.child_ids.ids),
        ]).filtered(lambda so: so.state != 'cancel')

        confirmed_sale_order_ids = sale_order_ids.filtered(lambda so: so.state in ('sale', 'done'))

        interested_product_ids = sale_order_ids.mapped('order_line.product_id.x_product_group.id')
        purchased_product_ids = confirmed_sale_order_ids.mapped('order_line.product_id.x_product_group.id')
        customer_ids = sale_order_ids.mapped('partner_id.id')
        customer_ids += sale_order_ids.mapped('partner_invoice_id.id')
        customer_ids += sale_order_ids.mapped('partner_shipping_id.id')
        customer_ids += sale_order_ids.mapped('x_end_user.id')
        customer_status = 'Customer' if confirmed_sale_order_ids else 'Enquirer'

        partner_id.update({
            'x_interested_product_ids': interested_product_ids,
            'x_purchased_product_ids': purchased_product_ids,
            'x_customer_ids': customer_ids,
            'x_customer_status': customer_status,
            'x_customer_status_comp': customer_status,
        })

    # -----------------------------------------CONSTRAINS-------------------------------------------
    def update_cgs_lines(self):
        for rec in self:
            new_codes_list = []
            total_cgs = 0
            estimated_cost = 0
            usd = self.env['res.currency'].search([('name', '=', 'USD')])
            pkr = self.env['res.currency'].search([('name', '=', 'PKR')])
            order_date = rec.date_order.date()
            total_amount = rec.amount_total
            for line in rec.order_line:
                if 'Freight' in line.product_id.name:
                    total_amount -= line.price_subtotal
            total_amount = round(rec.currency_id._convert(total_amount, usd, self.env.company, order_date), 2)

            total_pkr = 0
            for invoice in rec.invoice_ids:
                move_line_ids = self.env['account.move.line'].search([
                    '&', ('account_id', '=', self.env.ref('customizations.account_account_receivable').id),
                    '|', ('name', '=', 'Customer Payment: ' + invoice.name), ('name', '=', invoice.name)])
                if move_line_ids:
                    for move_line in move_line_ids:
                        total_pkr += -move_line.amount_currency if move_line.amount_currency < 0 else 0
                else:
                    for payment in invoice._get_reconciled_info_JSON_values():
                        total_pkr += invoice.currency_id._convert(payment['amount'], pkr,
                                                                  self.env.company, payment['date'])
            # Products
            for line in rec.order_line:
                if 'BOS-' not in line.product_id.name \
                        and line.product_id.name not in ['Down Payment', 'Freight'] \
                        and line.product_uom_qty != 0:
                    quantity = 0
                    cgs_subtotal = 0
                    cgs_subtotal_pkr = 0
                    move_line_ids = []
                    # Cost & Quantity
                    for picking in rec.picking_ids:
                        if picking.state == 'done':
                            for move in picking.move_ids_without_package:
                                if line.product_id.id == move.product_id.id:
                                    stock_valuation_id = self.env['stock.valuation.layer'].search([
                                        ('stock_move_id', '=', move.id),
                                        ('stock_landed_cost_id', '=', False),
                                    ])
                                    for stock_valuation in stock_valuation_id:
                                        if 'WH/OUT/' in picking.name:
                                            quantity += - stock_valuation.quantity
                                            move_amount = - stock_valuation.value
                                            move_date = stock_valuation.create_date.date()
                                            cgs_subtotal += move_amount
                                            cgs_subtotal_pkr += usd._convert(move_amount, pkr,
                                                                             self.env.company, move_date)
                                            total_cgs += usd._convert(move_amount, rec.currency_id,
                                                                      self.env.company, move_date)
                                            estimated_cost += usd._convert(move_amount, rec.currency_id,
                                                                           self.env.company, move_date)
                                        elif 'WH/IN/' in picking.name:
                                            quantity -= stock_valuation.quantity
                                            move_amount = stock_valuation.value
                                            move_date = stock_valuation.create_date.date()
                                            cgs_subtotal -= move_amount
                                            cgs_subtotal_pkr -= usd._convert(move_amount, pkr,
                                                                             self.env.company, move_date)
                                            total_cgs -= usd._convert(move_amount, rec.currency_id,
                                                                      self.env.company, move_date)
                                            estimated_cost -= usd._convert(move_amount, rec.currency_id,
                                                                           self.env.company, move_date)
                                        for move_line in stock_valuation.account_move_id.line_ids:
                                            if 'CGS' in move_line.account_id.name:
                                                move_line_ids.append(move_line.id)
                            entries = self.env['account.move'].search([
                                ('type', '=', 'entry'),
                                ('ref', 'in', ['%s - BOS-%s' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(0,0)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(0,1)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(0,3)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(0,5)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(5,0)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(5,1)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(5,3)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(5,5)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(10,0)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(10,1)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(10,3)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(10,5)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(20,0)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(20,1)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(20,3)' % (picking.name, line.product_id.name),
                                               '%s - BOS-%s-(20,5)' % (picking.name, line.product_id.name),
                                               ]),
                            ])
                            if entries:
                                if 'WH/OUT/' in picking.name:
                                    for entry in entries:
                                        move_amount = entry.amount_total_signed
                                        move_date = entry.date
                                        cgs_subtotal += move_amount
                                        cgs_subtotal_pkr += usd._convert(move_amount, pkr,
                                                                         self.env.company, move_date)
                                        total_cgs += usd._convert(move_amount, rec.currency_id,
                                                                  self.env.company, move_date)
                                        estimated_cost += usd._convert(move_amount, rec.currency_id,
                                                                       self.env.company, move_date)
                                if 'WH/IN/' in picking.name:
                                    for entry in entries:
                                        move_amount = entry.amount_total_signed
                                        move_date = entry.date
                                        cgs_subtotal -= move_amount
                                        cgs_subtotal_pkr -= usd._convert(move_amount, pkr,
                                                                         self.env.company, move_date)
                                        total_cgs -= usd._convert(move_amount, rec.currency_id,
                                                                  self.env.company, move_date)
                                        estimated_cost -= usd._convert(move_amount, rec.currency_id,
                                                                       self.env.company, move_date)
                                for entry in entries:
                                    for move_line in entry.line_ids:
                                        if 'CGS' in move_line.account_id.name:
                                            move_line_ids.append(move_line.id)
                    if quantity == 0 and line.product_id.type == 'service':
                        quantity = line.product_uom_qty
                    if quantity != 0:
                        discount_price = 0
                        price_subtotal = 0
                        product_line_ids = rec.order_line.filtered(lambda l: l.product_id.id == line.product_id.id)
                        for product_line in product_line_ids:
                            discount = product_line.discount
                            price_unit = product_line.price_unit
                            price_unit = rec.currency_id._convert(price_unit, usd, self.env.company, order_date)
                            price_unit = round(price_unit, 2)
                            discount_price += round(price_unit * product_line.product_uom_qty * discount / 100, 2)
                            price_subtotal += round(price_unit * product_line.product_uom_qty * (1 - discount / 100), 2)

                        discount = round(discount_price / price_subtotal, 2) if price_subtotal != 0 else 0
                        price_unit = round(price_subtotal / quantity, 2) if quantity != 0 else 0

                        cgs_unit = round(cgs_subtotal / quantity, 2) if quantity != 0 else 0

                        price_subtotal_pkr = price_subtotal / total_amount * total_pkr if total_amount != 0 else 0
                        price_subtotal_pkr = round(price_subtotal_pkr, 2)
                        unit_price_pkr = round(price_subtotal_pkr / quantity, 2) if quantity != 0 else 0
                        cgs_unit_pkr = round(cgs_subtotal_pkr / quantity, 2) if quantity != 0 else 0

                        profit = price_subtotal - cgs_subtotal
                        line_type = 'profit' if profit > 0 else 'loss'
                        profit = profit if profit > 0 else -profit

                        bonus = 0
                        if '5%)' in line.product_id.categ_id.name:
                            bonus = round(cgs_subtotal * 0.05, 2)
                        elif '3%)' in line.product_id.categ_id.name:
                            bonus = round(cgs_subtotal * 0.03, 2)
                        elif '1%)' in line.product_id.categ_id.name:
                            bonus = round(cgs_subtotal * 0.01, 2)
                        inv_profit = 0
                        if '(20%' in line.product_id.categ_id.name:
                            inv_profit = round(cgs_subtotal * 0.20, 2)
                        elif '(10%' in line.product_id.categ_id.name:
                            inv_profit = round(cgs_subtotal * 0.10, 2)
                        elif '(5%' in line.product_id.categ_id.name:
                            inv_profit = round(cgs_subtotal * 0.05, 2)
                        # Price
                        line_code = rec.name + '_' + line.product_id.name + '_' + 'real' + '_' + 'price' + '_' + 'products'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_quantity = quantity
                            old_cgs_line.x_price_unit = price_unit
                            old_cgs_line.x_discount = discount
                            old_cgs_line.x_price_subtotal = price_subtotal
                            old_cgs_line.x_cgs_unit_pkr = unit_price_pkr
                            old_cgs_line.x_cgs_subtotal_pkr = price_subtotal_pkr
                            old_cgs_line.x_description = line.name
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': line.product_id.id,
                                'x_quantity': quantity,
                                'x_uom_id': line.product_uom.id,
                                'x_price_unit': price_unit,
                                'x_discount': discount,
                                'x_price_subtotal': price_subtotal,
                                'x_calculation_type': 'real',
                                'x_type': 'price',
                                'x_product_type': 'products',
                                'x_line_code': line_code,
                                'x_description': line.name,

                                'x_cgs_unit_pkr': unit_price_pkr,
                                'x_cgs_subtotal_pkr': price_subtotal_pkr,
                            })]
                        new_codes_list.append(line_code)
                        # Cost
                        line_code = rec.name + '_' + line.product_id.name + '_' + 'real' + '_' + 'cost' + '_' + 'products'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_quantity = quantity
                            old_cgs_line.x_price_unit = cgs_unit
                            old_cgs_line.x_price_subtotal = cgs_subtotal
                            old_cgs_line.x_move_line_ids = move_line_ids
                            old_cgs_line.x_cost_multiplier = round(price_subtotal / cgs_subtotal,
                                                                   2) if cgs_subtotal != 0 else 0
                            old_cgs_line.x_cgs_unit_pkr = cgs_unit_pkr
                            old_cgs_line.x_cgs_subtotal_pkr = cgs_subtotal_pkr
                            old_cgs_line.x_description = line.name
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': line.product_id.id,
                                'x_quantity': quantity,
                                'x_uom_id': line.product_uom.id,
                                'x_price_unit': cgs_unit,
                                'x_price_subtotal': cgs_subtotal,
                                'x_calculation_type': 'real',
                                'x_type': 'cost',
                                'x_product_type': 'products',
                                'x_line_code': line_code,
                                'x_move_line_ids': move_line_ids,
                                'x_description': line.name,

                                'x_cost_multiplier': round(price_subtotal / cgs_subtotal,
                                                           2) if cgs_subtotal != 0 else 0,
                                'x_cgs_unit_pkr': cgs_unit_pkr,
                                'x_cgs_subtotal_pkr': cgs_subtotal_pkr,
                            })]
                        new_codes_list.append(line_code)
                        # Profit/Loss
                        line_code = rec.name + '_' + line.product_id.name + '_' + 'real' + '_' + 'profit_loss' + '_' + 'products'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_quantity = quantity
                            old_cgs_line.x_price_unit = round(profit / quantity, 2) if quantity != 0 else 0
                            old_cgs_line.x_price_subtotal = profit
                            old_cgs_line.x_profit_margin = round(profit / price_subtotal,
                                                                 2) if price_subtotal != 0 else 0
                            old_cgs_line.x_markup = round(profit / cgs_subtotal, 2) if cgs_subtotal != 0 else 0
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': line.product_id.id,
                                'x_quantity': quantity,
                                'x_uom_id': line.product_uom.id,
                                'x_price_unit': round(profit / quantity, 2) if quantity != 0 else 0,
                                'x_price_subtotal': profit,
                                'x_calculation_type': 'real',
                                'x_type': line_type,
                                'x_product_type': 'products',
                                'x_line_code': line_code,

                                'x_profit_margin': round(profit / price_subtotal, 2) if price_subtotal != 0 else 0,
                                'x_markup': round(profit / cgs_subtotal, 2) if cgs_subtotal != 0 else 0,
                            })]
                        new_codes_list.append(line_code)
                        # Discount
                        if discount_price != 0:
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'real' + '_' + 'price' + '_' + 'discount'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = discount_price
                                old_cgs_line.x_price_subtotal = discount_price
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 18972,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': discount_price,
                                    'x_price_subtotal': discount_price,
                                    'x_calculation_type': 'real',
                                    'x_type': 'price',
                                    'x_product_type': 'discount',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'real' + '_' + 'profit' + '_' + 'discount'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = discount_price
                                old_cgs_line.x_price_subtotal = discount_price
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 18972,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': discount_price,
                                    'x_price_subtotal': discount_price,
                                    'x_calculation_type': 'real',
                                    'x_type': 'profit',
                                    'x_product_type': 'discount',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                        # Bonus
                        if bonus != 0:
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'estimated' + '_' + 'cost' + '_' + 'bonus'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = bonus
                                old_cgs_line.x_price_subtotal = bonus
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 15728,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': bonus,
                                    'x_price_subtotal': bonus,
                                    'x_calculation_type': 'estimated',
                                    'x_type': 'cost',
                                    'x_product_type': 'bonus',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'estimated' + '_' + 'loss' + '_' + 'bonus'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = bonus
                                old_cgs_line.x_price_subtotal = bonus
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 15728,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': bonus,
                                    'x_price_subtotal': bonus,
                                    'x_calculation_type': 'estimated',
                                    'x_type': 'loss',
                                    'x_product_type': 'bonus',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                            if rec.x_inclusive_of_bonus:
                                total_cgs += usd._convert(bonus, rec.currency_id, self.env.company, order_date)
                            estimated_cost += usd._convert(bonus, rec.currency_id, self.env.company, order_date)
                        # Investor Share
                        if inv_profit != 0:
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'estimated' + '_' + 'cost' + '_' + 'investor_profit'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = inv_profit
                                old_cgs_line.x_price_subtotal = inv_profit
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 18971,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': inv_profit,
                                    'x_price_subtotal': inv_profit,
                                    'x_calculation_type': 'estimated',
                                    'x_type': 'cost',
                                    'x_product_type': 'investor_profit',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                            line_code = rec.name + '_' + line.product_id.name + '_' + 'estimated' + '_' + 'loss' + '_' + 'investor_profit'
                            old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                            if old_cgs_line:
                                old_cgs_line.x_price_unit = inv_profit
                                old_cgs_line.x_price_subtotal = inv_profit
                            else:
                                rec.x_cgs_line_ids = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_product_id': 18971,
                                    'x_quantity': 1,
                                    'x_uom_id': 1,
                                    'x_price_unit': inv_profit,
                                    'x_price_subtotal': inv_profit,
                                    'x_calculation_type': 'estimated',
                                    'x_type': 'loss',
                                    'x_product_type': 'investor_profit',
                                    'x_line_code': line_code,
                                })]
                            new_codes_list.append(line_code)
                            if rec.x_inclusive_of_investor_profit:
                                total_cgs += usd._convert(inv_profit, rec.currency_id, self.env.company,
                                                          order_date)
                            estimated_cost += usd._convert(inv_profit, rec.currency_id, self.env.company, order_date)
            # Freight
            if rec.state in ('sale', 'done'):
                # Get Price
                quantity = 1
                discount = 0
                price_unit = 0
                for line in rec.order_line:
                    if 'Freight' in line.product_id.name:
                        quantity = line.product_uom_qty
                        price_unit = rec.currency_id._convert(line.price_unit, usd, self.env.company, order_date)
                        discount = line.discount / 100
                        break
                # Get Cost
                freight_bills = self.env['account.move'].search([
                    ('x_related_so_s', 'ilike', rec._origin.id), ('type', '=', 'in_invoice'), ('state', '=', 'posted')
                ])
                if freight_bills:
                    freight_cost = 0
                    freight_cost_pkr = 0
                    bill_id = False
                    for bill in freight_bills:
                        freight_cost += bill.currency_id._convert(bill.amount_total, usd, self.env.company, bill.date)
                        freight_cost_pkr += bill.currency_id._convert(bill.amount_total, pkr, self.env.company, bill.date)
                        total_cgs += bill.currency_id._convert(bill.amount_total, usd, self.env.company, bill.date)
                        estimated_cost += bill.currency_id._convert(bill.amount_total, usd, self.env.company, bill.date)
                        bill_id = bill.id
                    # Post CGS Lines
                    price_subtotal = price_unit * quantity * (1 - discount)
                    freight_price_pkr = usd._convert(price_subtotal, pkr, self.env.company, order_date)
                    profit = price_subtotal - freight_cost
                    line_type = 'profit' if profit > 0 else 'loss'
                    profit = profit if profit > 0 else -profit
                    discount_price = round(price_unit * quantity * discount, 2)
                    # Price
                    line_code = rec.name + '_Freight_' + 'real' + '_' + 'price' + '_' + 'freight'
                    old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                    if old_cgs_line:
                        old_cgs_line.x_quantity = 1
                        old_cgs_line.x_price_unit = price_unit
                        old_cgs_line.x_discount = discount
                        old_cgs_line.x_price_subtotal = price_subtotal
                        old_cgs_line.x_cgs_unit_pkr = freight_price_pkr
                        old_cgs_line.x_cgs_subtotal_pkr = freight_price_pkr
                    else:
                        rec.x_cgs_line_ids = [(0, 0, {
                            'x_sale_order_id': rec._origin.id,
                            'x_product_id': 13813,
                            'x_quantity': 1,
                            'x_uom_id': 1,
                            'x_price_unit': price_unit,
                            'x_discount': discount,
                            'x_price_subtotal': price_subtotal,
                            'x_calculation_type': 'real',
                            'x_type': 'price',
                            'x_product_type': 'freight',
                            'x_line_code': line_code,

                            'x_cgs_unit_pkr': freight_price_pkr,
                            'x_cgs_subtotal_pkr': freight_price_pkr,
                        })]
                    new_codes_list.append(line_code)
                    # Cost
                    line_code = rec.name + '_Freight_' + 'real' + '_' + 'cost' + '_' + 'freight'
                    old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                    if old_cgs_line:
                        old_cgs_line.x_quantity = 1
                        old_cgs_line.x_price_unit = freight_cost
                        old_cgs_line.x_price_subtotal = freight_cost
                        old_cgs_line.x_cost_multiplier = round(price_subtotal / freight_cost,
                                                               2) if freight_cost != 0 else 0
                        old_cgs_line.x_cgs_unit_pkr = freight_cost_pkr
                        old_cgs_line.x_cgs_subtotal_pkr = freight_cost_pkr
                    else:
                        rec.x_cgs_line_ids = [(0, 0, {
                            'x_journal_entry_id': bill_id if bill_id else False,
                            'x_sale_order_id': rec._origin.id,
                            'x_product_id': 13813,
                            'x_quantity': 1,
                            'x_uom_id': 1,
                            'x_price_unit': freight_cost,
                            'x_price_subtotal': freight_cost,
                            'x_calculation_type': 'real',
                            'x_type': 'cost',
                            'x_product_type': 'freight',
                            'x_line_code': line_code,

                            'x_cost_multiplier': round(price_subtotal / freight_cost, 2) if freight_cost != 0 else 0,
                            'x_cgs_unit_pkr': freight_cost_pkr,
                            'x_cgs_subtotal_pkr': freight_cost_pkr,
                        })]
                    new_codes_list.append(line_code)
                    # Profit
                    line_code = rec.name + '_Freight_' + 'real' + '_' + 'profit_loss' + '_' + 'freight'
                    old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                    if old_cgs_line:
                        old_cgs_line.x_quantity = 1
                        old_cgs_line.x_price_unit = profit
                        old_cgs_line.x_price_subtotal = profit
                        old_cgs_line.x_profit_margin = round(profit / price_subtotal, 2) if price_subtotal != 0 else 0
                        old_cgs_line.x_markup = round(profit / freight_cost, 2) if freight_cost != 0 else 0
                    else:
                        rec.x_cgs_line_ids = [(0, 0, {
                            'x_sale_order_id': rec._origin.id,
                            'x_product_id': 13813,
                            'x_quantity': 1,
                            'x_uom_id': 1,
                            'x_price_unit': profit,
                            'x_price_subtotal': profit,
                            'x_calculation_type': 'real',
                            'x_type': line_type,
                            'x_product_type': 'freight',
                            'x_line_code': line_code,

                            'x_profit_margin': round(profit / price_subtotal, 2) if price_subtotal != 0 else 0,
                            'x_markup': round(profit / freight_cost, 2) if freight_cost != 0 else 0,
                        })]
                    new_codes_list.append(line_code)
                    # Discount
                    if discount_price != 0:
                        line_code = rec.name + '_Freight_' + 'real' + '_' + 'cost' + '_' + 'discount'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_price_unit = discount_price
                            old_cgs_line.x_price_subtotal = discount_price
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': 18972,
                                'x_quantity': 1,
                                'x_uom_id': 1,
                                'x_price_unit': discount_price,
                                'x_price_subtotal': discount_price,
                                'x_calculation_type': 'real',
                                'x_type': 'cost',
                                'x_product_type': 'discount',
                                'x_line_code': line_code,
                            })]
                        new_codes_list.append(line_code)
                        line_code = rec.name + '_Freight_' + 'real' + '_' + 'loss' + '_' + 'discount'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_price_unit = discount_price
                            old_cgs_line.x_price_subtotal = discount_price
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': 18972,
                                'x_quantity': 1,
                                'x_uom_id': 1,
                                'x_price_unit': discount_price,
                                'x_price_subtotal': discount_price,
                                'x_calculation_type': 'real',
                                'x_type': 'loss',
                                'x_product_type': 'discount',
                                'x_line_code': line_code,
                            })]
                        new_codes_list.append(line_code)
            # Banking Charges (Paypal or 2Checkout)
            banking_charges_paypal = self.env['account.move.line'].search([('name', '=', 'Paypal Fee - ' + rec.name)])
            banking_charges_checkout = self.env['account.move.line'].search(
                [('name', '=', '2Checkout Fee - ' + rec.name)])
            product_id = 18949 if banking_charges_paypal else 18955
            product_name = 'paypal' if banking_charges_paypal else '2checkout'
            banking_charges = banking_charges_paypal if banking_charges_paypal else banking_charges_checkout
            for banking_charge in banking_charges:
                amount = banking_charge.debit
                date = banking_charge.date
                line_code = rec.name + '_' + banking_charge.move_id.name + '_' + product_name + '_' + 'real' + '_' + 'cost' + '_' + 'fees'
                old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                if old_cgs_line:
                    old_cgs_line.x_price_unit = amount
                    old_cgs_line.x_price_subtotal = amount
                else:
                    rec.x_cgs_line_ids = [(0, 0, {
                        'x_journal_entry_id': banking_charge.move_id.id,
                        'x_sale_order_id': rec._origin.id,
                        'x_product_id': product_id,
                        'x_quantity': 1,
                        'x_uom_id': 1,
                        'x_price_unit': amount,
                        'x_price_subtotal': amount,
                        'x_calculation_type': 'real',
                        'x_type': 'cost',
                        'x_product_type': 'fees',
                        'x_line_code': line_code,
                    })]
                new_codes_list.append(line_code)
                line_code = rec.name + '_' + banking_charge.move_id.name + '_' + product_name + '_' + 'real' + '_' + 'loss' + '_' + 'fees'
                old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                if old_cgs_line:
                    old_cgs_line.x_price_unit = amount
                    old_cgs_line.x_price_subtotal = amount
                else:
                    rec.x_cgs_line_ids = [(0, 0, {
                        'x_journal_entry_id': banking_charge.move_id.id,
                        'x_sale_order_id': rec._origin.id,
                        'x_product_id': product_id,
                        'x_quantity': 1,
                        'x_uom_id': 1,
                        'x_price_unit': amount,
                        'x_price_subtotal': amount,
                        'x_calculation_type': 'real',
                        'x_type': 'loss',
                        'x_product_type': 'fees',
                        'x_line_code': line_code,
                    })]
                new_codes_list.append(line_code)
                total_cgs += usd._convert(amount, rec.currency_id, self.env.company, date)
                estimated_cost += usd._convert(amount, rec.currency_id, self.env.company, date)
            # Banking Charges (Bank Al-Falah)
            swift_inwards = self.env['account.move.line'].search([('name', '=', 'EDS - ' + rec.name)])
            for swift_inward in swift_inwards:
                swift_inward = swift_inward.move_id
                for line in swift_inward.line_ids:
                    product_id = False
                    if line.name == 'EDS - ' + rec.name:
                        product_id = 18950
                        product_name = 'EDS'
                    elif line.name == 'FED - ' + rec.name:
                        product_id = 18951
                        product_name = 'FED'
                    elif line.name == 'Alfalah Fee - ' + rec.name:
                        product_id = 18952
                        product_name = 'alfalah_fee'
                    elif line.name == 'WHT 1%' or line.name == 'WHT 1% - ' + rec.name:
                        product_id = 18953
                        product_name = 'wht_1%'
                    elif line.name == 'MIDDLE BANK CUTTINGS - ' + rec.name or line.name == 'Middle Bank Cuttings - ' + rec.name:
                        product_id = 18954
                        product_name = 'middle_bank_cuttings'
                    elif line.name == 'Currency Loss':
                        product_id = 18504
                        product_name = 'currency_loss'
                    if product_id:
                        line_code = rec.name + '_' + swift_inward.name + '_' + product_name + '_' + 'real' + '_' + 'cost' + '_' + 'fees'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_price_unit = line.debit
                            old_cgs_line.x_price_subtotal = line.debit
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_journal_entry_id': swift_inward.id,
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': product_id,
                                'x_quantity': 1,
                                'x_uom_id': 1,
                                'x_price_unit': line.debit,
                                'x_price_subtotal': line.debit,
                                'x_calculation_type': 'real',
                                'x_type': 'cost',
                                'x_product_type': 'fees',
                                'x_line_code': line_code,
                            })]
                        new_codes_list.append(line_code)
                        line_code = rec.name + '_' + swift_inward.name + '_' + product_name + '_' + 'real' + '_' + 'loss' + '_' + 'fees'
                        old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                        if old_cgs_line:
                            old_cgs_line.x_price_unit = line.debit
                            old_cgs_line.x_price_subtotal = line.debit
                        else:
                            rec.x_cgs_line_ids = [(0, 0, {
                                'x_journal_entry_id': swift_inward.id,
                                'x_sale_order_id': rec._origin.id,
                                'x_product_id': product_id,
                                'x_quantity': 1,
                                'x_uom_id': 1,
                                'x_price_unit': line.debit,
                                'x_price_subtotal': line.debit,
                                'x_calculation_type': 'real',
                                'x_type': 'loss',
                                'x_product_type': 'fees',
                                'x_line_code': line_code,
                            })]
                        new_codes_list.append(line_code)
                        total_cgs += usd._convert(line.debit, rec.currency_id, self.env.company, line.date)
                        estimated_cost += usd._convert(line.debit, rec.currency_id, self.env.company, line.date)
            # Other Real Expenses
            other_expenses = self.env['account.move.line'].search([('name', 'ilike', 'Other Cost - ' + rec.name)])
            for other_expense in other_expenses:
                amount = other_expense.debit
                date = other_expense.date
                line_code = rec.name + '_' + other_expense.move_id.name + '_' + 'real' + '_' + 'cost' + '_' + 'other_real'
                old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                if old_cgs_line:
                    old_cgs_line.x_price_unit = amount
                    old_cgs_line.x_price_subtotal = amount
                else:
                    rec.x_cgs_line_ids = [(0, 0, {
                        'x_journal_entry_id': other_expense.move_id.id,
                        'x_sale_order_id': rec._origin.id,
                        'x_product_id': 18977,
                        'x_quantity': 1,
                        'x_uom_id': 1,
                        'x_price_unit': amount,
                        'x_price_subtotal': amount,
                        'x_calculation_type': 'real',
                        'x_type': 'cost',
                        'x_product_type': 'other_real',
                        'x_line_code': line_code,
                    })]
                new_codes_list.append(line_code)
                line_code = rec.name + '_' + other_expense.move_id.name + '_' + 'real' + '_' + 'loss' + '_' + 'other_real'
                old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                if old_cgs_line:
                    old_cgs_line.x_price_unit = amount
                    old_cgs_line.x_price_subtotal = amount
                else:
                    rec.x_cgs_line_ids = [(0, 0, {
                        'x_journal_entry_id': other_expense.move_id.id,
                        'x_sale_order_id': rec._origin.id,
                        'x_product_id': 18977,
                        'x_quantity': 1,
                        'x_uom_id': 1,
                        'x_price_unit': amount,
                        'x_price_subtotal': amount,
                        'x_calculation_type': 'real',
                        'x_type': 'loss',
                        'x_product_type': 'other_real',
                        'x_line_code': line_code,
                    })]
                new_codes_list.append(line_code)
                if rec.x_inclusive_of_other_expense:
                    total_cgs += usd._convert(amount, rec.currency_id, self.env.company, date)
                estimated_cost += usd._convert(amount, rec.currency_id, self.env.company, date)
            # Currency (Loss / Gain)
            if rec.currency_id != 2:
                for invoice in rec.invoice_ids:
                    amount = 0
                    invoice_date = False
                    if invoice.invoice_payments_widget:
                        payments = str(invoice.invoice_payments_widget)
                        payments = payments.replace('"', '')
                        payments = payments.replace(', ', ': ')
                        payments = payments.replace('}', '')
                        payments = payments.replace('{', '')
                        payments = payments.split(': ')
                        for entries in range(len(payments)):
                            if payments[entries] == 'amount':
                                amount = float(payments[entries + 1])
                            elif payments[entries] == 'date':
                                invoice_date = payments[entries + 1].split('-')
                                invoice_date = datetime.date(int(invoice_date[0]), int(invoice_date[1]),
                                                             int(invoice_date[2]))
                            if amount != 0 and invoice_date:
                                sale_order_amount = rec.currency_id._convert(amount, usd, self.env.company, order_date)
                                payment_amount = rec.currency_id._convert(amount, usd, self.env.company, invoice_date)
                                amount = payment_amount - sale_order_amount
                                if amount > 0:
                                    type1 = 'price'
                                    type2 = 'profit'
                                elif amount < 0:
                                    type1 = 'cost'
                                    type2 = 'loss'
                                    amount = -amount
                                if amount != 0:
                                    line_code = rec.name + '_' + invoice.name + '_' + 'price_cost' + '_' + 'estimated' + '_' + 'currency'
                                    old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                                    if old_cgs_line:
                                        old_cgs_line.x_price_unit = amount
                                        old_cgs_line.x_price_subtotal = amount
                                    else:
                                        rec.x_cgs_line_ids = [(0, 0, {
                                            'x_sale_order_id': rec._origin.id,
                                            'x_product_id': 18976,
                                            'x_quantity': 1,
                                            'x_uom_id': 1,
                                            'x_price_unit': amount,
                                            'x_price_subtotal': amount,
                                            'x_calculation_type': 'estimated',
                                            'x_type': type1,
                                            'x_product_type': 'currency',
                                            'x_line_code': line_code,
                                        })]
                                    new_codes_list.append(line_code)
                                    line_code = rec.name + '_' + invoice.name + '_' + 'profit_loss' + '_' + 'estimated' + '_' + 'currency'
                                    old_cgs_line = rec.x_cgs_line_ids.search([('x_line_code', '=', line_code)])
                                    if old_cgs_line:
                                        old_cgs_line.x_price_unit = amount
                                        old_cgs_line.x_price_subtotal = amount
                                    else:
                                        rec.x_cgs_line_ids = [(0, 0, {
                                            'x_sale_order_id': rec._origin.id,
                                            'x_product_id': 18976,
                                            'x_quantity': 1,
                                            'x_uom_id': 1,
                                            'x_price_unit': amount,
                                            'x_price_subtotal': amount,
                                            'x_calculation_type': 'estimated',
                                            'x_type': type2,
                                            'x_product_type': 'currency',
                                            'x_line_code': line_code,
                                        })]
                                    new_codes_list.append(line_code)
                                    if rec.x_inclusive_of_currency:
                                        total_cgs += usd._convert(amount, rec.currency_id, self.env.company,
                                                                  order_date)
                                    estimated_cost += usd._convert(amount, rec.currency_id, self.env.company,
                                                                   order_date)
                                amount = 0
                                invoice_date = False

            rec.x_total_cgs = round(total_cgs, 2)
            rec.x_total_profit = round(rec.amount_total - rec.x_total_cgs, 2)
            rec.x_profit_margin = round(rec.x_total_profit / rec.amount_total, 2) if rec.amount_total != 0 else 0

            rec.x_estimated_profit = round(rec.amount_total - estimated_cost, 2)
            rec.x_estimated_profit_margin = round(rec.x_estimated_profit / rec.amount_total,
                                                  2) if rec.amount_total != 0 else 0

            for line in rec.x_cgs_line_ids:
                if line.x_product_type != "other_estimated":
                    if line.x_line_code not in new_codes_list:
                        line.unlink()

    # -----------------------------------------DEPENDS---------------------------------------------
    @api.depends('invoice_status', 'x_so_payment_state')
    def _compute_task_tags(self):
        for rec in self:
            if rec.x_task_id:
                for tag in rec.x_task_id.tag_ids:
                    if rec.invoice_status == 'invoiced' and rec.x_so_payment_state == 'paid':
                        if tag.name in ['Payment Pending', 'Partially Paid']:
                            rec.x_task_id.tag_ids = [(3, tag.id)]
                        tag_id = self.env['project.tags'].search([('name', '=', 'Fully Paid')], limit=1)
                        rec.x_task_id.tag_ids = [(4, tag_id.id)]
                    elif rec.invoice_status in ['invoiced', 'to invoice'] \
                            and rec.x_so_payment_state in ['paid', 'in_payment']:
                        if tag.name == 'Payment Pending':
                            rec.x_task_id.tag_ids = [(3, tag.id)]

                if (rec.invoice_status == 'invoiced' and rec.x_so_payment_state == 'in_payment') \
                        or (rec.invoice_status == 'to invoice' and rec.x_so_payment_state in ['paid', 'in_payment']):
                    tag_id = self.env['project.tags'].search([('name', '=', 'Partially Paid')], limit=1)
                    rec.x_task_id.tag_ids = [(4, tag_id.id)]

    @api.depends('x_payment_method')
    def _update_payment_acquirer(self):
        for rec in self:
            if rec.x_payment_method:
                payment_acquirer_id = self.env['payment.acquirer'].search(
                    [('journal_id', '=', rec.x_payment_method.id)], limit=1).id
                rec.x_bank = payment_acquirer_id if payment_acquirer_id else False

    @api.depends('order_line', 'state', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'x_end_user',
                 'x_team_member_ids')
    def _compute_partner_products_and_status(self):
        for rec in self:
            if rec.partner_id.id == rec.partner_invoice_id.id == rec.partner_shipping_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
            elif rec.partner_id.id == rec.partner_invoice_id.id == rec.partner_shipping_id.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.x_end_user)
                rec.update_partner(rec.x_end_user.parent_id)
            elif rec.partner_id.id == rec.partner_invoice_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
            elif rec.partner_id.id == rec.partner_shipping_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
            elif rec.partner_invoice_id.id == rec.partner_shipping_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
            elif rec.partner_id.id == rec.partner_invoice_id.id and rec.partner_shipping_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
            elif rec.partner_id.id == rec.partner_shipping_id.id and rec.partner_invoice_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
            elif rec.partner_id.id == rec.x_end_user.id and rec.partner_shipping_id.id == rec.partner_invoice_id.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
            elif rec.partner_id.id == rec.partner_invoice_id.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
                rec.update_partner(rec.x_end_user)
                rec.update_partner(rec.x_end_user.parent_id)
            elif rec.partner_id.id == rec.partner_shipping_id.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
                rec.update_partner(rec.x_end_user)
                rec.update_partner(rec.x_end_user.parent_id)
            elif rec.partner_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
            elif rec.partner_invoice_id.id == rec.partner_shipping_id.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
                rec.update_partner(rec.x_end_user)
                rec.update_partner(rec.x_end_user.parent_id)
            elif rec.partner_invoice_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
            elif rec.partner_shipping_id.id == rec.x_end_user.id:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
            else:
                rec.update_partner(rec.partner_id)
                rec.update_partner(rec.partner_id.parent_id)
                rec.update_partner(rec.partner_invoice_id)
                rec.update_partner(rec.partner_invoice_id.parent_id)
                rec.update_partner(rec.partner_shipping_id)
                rec.update_partner(rec.partner_shipping_id.parent_id)
                rec.update_partner(rec.x_end_user)
                rec.update_partner(rec.x_end_user.parent_id)

            for partner in rec.x_team_member_ids:
                rec.update_partner(partner)
                rec.update_partner(partner.parent_id)

    @api.depends('amount_total', 'picking_ids', 'invoice_ids', 'x_cgs_line_ids')
    def compute_sale_order_cost(self):
        for rec in self:
            total_cgs = 0
            estimated_cost = 0
            rec.x_inclusive_of_other_costs = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_other_costs')
            rec.x_inclusive_of_bonus = self.env['ir.config_parameter'].sudo().get_param('sale.x_inclusive_of_bonus')
            rec.x_inclusive_of_investor_profit = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_investor_profit')
            rec.x_inclusive_of_currency = self.env['ir.config_parameter'].sudo().get_param(
                'sale.x_inclusive_of_currency')
            for line in rec.x_cgs_line_ids:
                if line.x_type == "cost":
                    estimated_cost += line.x_price_subtotal
                if line.x_type == "cost" and line.x_product_type == "products":
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "freight":
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "fees":
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "other_real":
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "other_estimated" and rec.x_inclusive_of_other_costs:
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "bonus" and rec.x_inclusive_of_bonus:
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "investor_profit" and rec.x_inclusive_of_investor_profit:
                    total_cgs += line.x_price_subtotal
                elif line.x_type == "cost" and line.x_product_type == "currency" and rec.x_inclusive_of_currency:
                    total_cgs += line.x_price_subtotal

            rec.x_total_cgs = total_cgs
            rec.x_total_profit = rec.amount_total - rec.x_total_cgs
            rec.x_profit_margin = round(rec.x_total_profit / rec.amount_total, 2) if rec.amount_total != 0 else 0
            rec.x_estimated_profit = rec.amount_total - estimated_cost
            rec.x_estimated_profit_margin = round(rec.x_estimated_profit / rec.amount_total,
                                                  2) if rec.amount_total != 0 else 0

    @api.depends('order_line', 'x_cgs_line_ids')
    def _check_costing(self):
        for rec in self:
            rec.x_costing_complete = True
            cgs_product_list = rec.x_cgs_line_ids.mapped('x_product_id')
            for line in rec.order_line:
                if 'Freight' not in line.product_id.name:
                    if line.product_uom_qty != line.qty_delivered:
                        rec.x_costing_complete = False
                        break
                if 'BOS-' not in line.product_id.name and cgs_product_list:
                    if line.product_id not in cgs_product_list:
                        rec.x_costing_complete = False
                        break
                    for cgs_line in rec.x_cgs_line_ids:
                        if cgs_line.x_type == 'cost' and line.product_id.id == cgs_line.x_product_id.id and line.product_uom_qty != cgs_line.x_quantity:
                            rec.x_costing_complete = False
                            break
                if not rec.x_costing_complete:
                    break

    @api.depends('x_cgs_line_ids', 'x_product', 'x_freight', 'x_fees', 'x_other_real', 'x_other_estimated', 'x_bonus',
                 'x_investor_share', 'x_discount', 'x_currency')
    def _compute_amounts(self):
        for rec in self:
            total_price = 0
            total_cost = 0
            total_profit = 0

            product_price = 0
            freight_price = 0
            fees_price = 0
            other_real_price = 0
            other_estimated_price = 0
            bonus_price = 0
            investor_share_price = 0
            discount_price = 0
            currency_price = 0

            product_cost = 0
            freight_cost = 0
            fees_cost = 0
            other_real_cost = 0
            other_estimated_cost = 0
            bonus_cost = 0
            investor_share_cost = 0
            discount_cost = 0
            currency_cost = 0

            product_profit = 0
            freight_profit = 0
            fees_profit = 0
            other_real_profit = 0
            other_estimated_profit = 0
            bonus_profit = 0
            investor_share_profit = 0
            discount_profit = 0
            currency_profit = 0

            for line in rec.x_cgs_line_ids:
                if line.x_type == 'price':
                    if line.x_product_type == 'discount':
                        total_price += line.x_price_subtotal
                    total_price += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    total_price += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    total_price -= line.x_price_subtotal if rec.x_discount and line.x_product_type == 'discount' else 0
                    total_price += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    total_price += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    total_price += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    total_price += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    total_price += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    total_price += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                    product_price += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    if line.x_product_type == 'discount':
                        product_price += line.x_price_subtotal
                    freight_price += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    if rec.x_discount and line.x_product_type == 'discount':
                        product_price -= line.x_price_subtotal
                        discount_price -= line.x_price_subtotal
                    fees_price += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    other_real_price += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    other_estimated_price += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    bonus_price += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    investor_share_price += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    currency_price += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                elif line.x_type == 'cost':
                    total_cost += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    total_cost += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    total_cost += line.x_price_subtotal if rec.x_discount and line.x_product_type == 'discount' else 0
                    total_cost += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    total_cost += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    total_cost += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    total_cost += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    total_cost += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    total_cost += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                    product_cost += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    freight_cost += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    discount_cost += line.x_price_subtotal if rec.x_discount and line.x_product_type == 'discount' else 0
                    fees_cost += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    other_real_cost += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    other_estimated_cost += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    bonus_cost += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    investor_share_cost += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    currency_cost += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                elif line.x_type == 'profit':
                    if line.x_product_type == 'discount':
                        total_profit += line.x_price_subtotal
                    total_profit += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    total_profit += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    total_profit -= line.x_price_subtotal if rec.x_discount and line.x_product_type == 'discount' else 0
                    total_profit += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    total_profit += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    total_profit += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    total_profit += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    total_profit += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    total_profit += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                    if line.x_product_type == 'discount':
                        product_profit += line.x_price_subtotal
                    product_profit += line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    freight_profit += line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    if rec.x_discount and line.x_product_type == 'discount':
                        product_profit -= line.x_price_subtotal
                        discount_profit -= line.x_price_subtotal
                    fees_profit += line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    other_real_profit += line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    other_estimated_profit += line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    bonus_profit += line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    investor_share_profit += line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    currency_profit += line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                elif line.x_type == 'loss':
                    if line.x_product_type == 'discount':
                        total_profit -= line.x_price_subtotal
                    total_profit -= line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    total_profit -= line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    total_profit += line.x_price_subtotal if rec.x_discount and line.x_product_type == 'discount' else 0
                    total_profit -= line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    total_profit -= line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    total_profit -= line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    total_profit -= line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    total_profit -= line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    total_profit -= line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0
                    if line.x_product_type == 'discount':
                        product_profit -= line.x_price_subtotal
                    product_profit -= line.x_price_subtotal if rec.x_product and line.x_product_type == 'products' else 0
                    freight_profit -= line.x_price_subtotal if rec.x_freight and line.x_product_type == 'freight' else 0
                    if rec.x_discount and line.x_product_type == 'discount':
                        product_profit += line.x_price_subtotal
                        discount_profit += line.x_price_subtotal
                    fees_profit -= line.x_price_subtotal if rec.x_fees and line.x_product_type == 'fees' else 0
                    other_real_profit -= line.x_price_subtotal if rec.x_other_real and line.x_product_type == 'other_real' else 0
                    other_estimated_profit -= line.x_price_subtotal if rec.x_other_estimated and line.x_product_type == 'other_estimated' else 0
                    bonus_profit -= line.x_price_subtotal if rec.x_bonus and line.x_product_type == 'bonus' else 0
                    investor_share_profit -= line.x_price_subtotal if rec.x_investor_share and line.x_product_type == 'investor_profit' else 0
                    currency_profit -= line.x_price_subtotal if rec.x_currency and line.x_product_type == 'currency' else 0

            rec.x_price = round(total_price, 2)
            rec.x_cost = round(total_cost, 2)
            rec.x_profit = round(total_profit, 2)
            rec.x_cost_multiplier = round(total_price / rec.x_cost, 2) if rec.x_cost != 0 else 0
            rec.x_markup = round(total_profit / total_cost, 2) if total_cost != 0 else 0
            rec.x_cost_percentage = round(total_cost / total_price, 2) if total_price != 0 else 0
            rec.x_profit_percentage = round(total_profit / total_price, 2) if total_price != 0 else 0

            rec.x_product_price = '$ ' + str(round(product_price, 2)) + ' @ ' + str(
                round(product_price / total_price * 100, 2)) + '%' if rec.x_product and total_price != 0 else "---"
            rec.x_freight_price = '$ ' + str(round(freight_price, 2)) + ' @ ' + str(
                round(freight_price / total_price * 100, 2)) + '%' if rec.x_freight and total_price != 0 else "---"
            rec.x_discount_price = '$ ' + str(round(discount_price, 2)) + ' @ ' + str(
                round(discount_price / total_price * 100, 2)) + '%' if rec.x_discount and total_price != 0 else "---"
            rec.x_fees_price = '$ ' + str(round(fees_price, 2)) + ' @ ' + str(
                round(fees_price / total_price * 100, 2)) + '%' if rec.x_fees and total_price != 0 else "---"
            rec.x_other_real_price = '$ ' + str(round(other_real_price, 2)) + ' @ ' + str(
                round(other_real_price / total_price * 100,
                      2)) + '%' if rec.x_other_real and total_price != 0 else "---"
            rec.x_other_estimated_price = '$ ' + str(round(other_estimated_price, 2)) + ' @ ' + str(
                round(other_estimated_price / total_price * 100,
                      2)) + '%' if rec.x_other_estimated and total_price != 0 else "---"
            rec.x_bonus_price = '$ ' + str(round(bonus_price, 2)) + ' @ ' + str(
                round(bonus_price / total_price * 100, 2)) + '%' if rec.x_bonus and total_price != 0 else "---"
            rec.x_investor_share_price = '$ ' + str(round(investor_share_price, 2)) + ' @ ' + str(
                round(investor_share_price / total_price * 100,
                      2)) + '%' if rec.x_investor_share and total_price != 0 else "---"
            rec.x_currency_price = '$ ' + str(round(currency_price, 2)) + ' @ ' + str(
                round(currency_price / total_price * 100, 2)) + '%' if rec.x_currency and total_price != 0 else "---"

            rec.x_product_cost = '$ ' + str(round(product_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * product_cost / total_cost * 100,
                      2)) + '%' if rec.x_product and total_cost != 0 else "---"
            rec.x_freight_cost = '$ ' + str(round(freight_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * freight_cost / total_cost * 100,
                      2)) + '%' if rec.x_freight and total_cost != 0 else "---"
            rec.x_discount_cost = '$ ' + str(round(discount_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * discount_cost / total_cost * 100,
                      2)) + '%' if rec.x_discount and total_cost != 0 else "---"
            rec.x_fees_cost = '$ ' + str(round(fees_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * fees_cost / total_cost * 100,
                      2)) + '%' if rec.x_fees and total_cost != 0 else "---"
            rec.x_other_real_cost = '$ ' + str(round(other_real_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * other_real_cost / total_cost * 100,
                      2)) + '%' if rec.x_other_real and total_cost != 0 else "---"
            rec.x_other_estimated_cost = '$ ' + str(round(other_estimated_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * other_estimated_cost / total_cost * 100,
                      2)) + '%' if rec.x_other_estimated and total_cost != 0 else "---"
            rec.x_bonus_cost = '$ ' + str(round(bonus_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * bonus_cost / total_cost * 100,
                      2)) + '%' if rec.x_bonus and total_cost != 0 else "---"
            rec.x_investor_share_cost = '$ ' + str(round(investor_share_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * investor_share_cost / total_cost * 100,
                      0)) + '%' if rec.x_investor_share and total_cost != 0 else "---"
            rec.x_currency_cost = '$ ' + str(round(currency_cost, 2)) + ' @ ' + str(
                round(rec.x_cost_percentage * currency_cost / total_cost * 100,
                      2)) + '%' if rec.x_currency and total_cost != 0 else "---"

            rec.x_product_profit = '$ ' + str(round(product_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * product_profit / total_profit * 100,
                      2)) + '%' if rec.x_product and total_profit != 0 else "---"
            rec.x_freight_profit = '$ ' + str(round(freight_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * freight_profit / total_profit * 100,
                      2)) + '%' if rec.x_freight and total_profit != 0 else "---"
            rec.x_discount_profit = '$ ' + str(round(discount_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * discount_profit / total_profit * 100,
                      2)) + '%' if rec.x_discount and total_profit != 0 else "---"
            rec.x_fees_profit = '$ ' + str(round(fees_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * fees_profit / total_profit * 100,
                      2)) + '%' if rec.x_fees and total_profit != 0 else "---"
            rec.x_other_real_profit = '$ ' + str(round(other_real_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * other_real_profit / total_profit * 100,
                      2)) + '%' if rec.x_other_real and total_profit != 0 else "---"
            rec.x_other_estimated_profit = '$ ' + str(round(other_estimated_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * other_estimated_profit / total_profit * 100,
                      2)) + '%' if rec.x_other_estimated and total_profit != 0 else "---"
            rec.x_bonus_profit = '$ ' + str(round(bonus_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * bonus_profit / total_profit * 100,
                      2)) + '%' if rec.x_bonus and total_profit != 0 else "---"
            rec.x_investor_share_profit = '$ ' + str(round(investor_share_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * investor_share_profit / total_profit * 100,
                      2)) + '%' if rec.x_investor_share and total_profit != 0 else "---"
            rec.x_currency_profit = '$ ' + str(round(currency_profit, 2)) + ' @ ' + str(
                round(rec.x_profit_percentage * currency_profit / total_profit * 100,
                      2)) + '%' if rec.x_currency and total_profit != 0 else "---"

    @api.depends('picking_ids.carrier_tracking_ref')
    def _compute_tracking_ref(self):
        for rec in self:
            rec.x_tracking_reference = ', '.join(awb for awb in rec.picking_ids.mapped('carrier_tracking_ref') if awb)

    @api.depends('order_line')
    def compute_shipment_product(self):
        for rec in self:
            rec.x_sale_order_product_ids = [(5, 0, 0)]
            for line in rec.order_line:
                # freight_line = rec.x_sale_order_product_ids.search([('x_sale_order_id', '=', rec._origin.id),('x_product_id', '=', line.product_id.id)], limit=1)
                # if freight_line:
                #     freight_line.x_quantity = line.product_uom_qty
                if 'Freight' not in line.product_id.name and 'BOS-' not in line.product_id.name \
                        and 'Down Payment' not in line.product_id.name and line.product_uom_qty != 0:
                    rec.x_sale_order_product_ids = [(0, 0, {
                        'x_sale_order_id': rec._origin.id,
                        'x_product_id': line.product_id.id,
                        'x_quantity': line.product_uom_qty,
                    })]

    @api.depends('x_sale_order_product_ids')
    def compute_shipment_weight(self):
        for rec in self:
            rec.x_shipment_weight = 0
            for line in rec.x_sale_order_product_ids:
                rec.x_shipment_weight += line.x_total_weight

    @api.depends('date_order', 'x_shipment_weight', 'partner_shipping_id')
    def shipment_freight_calculation(self):
        for rec in self:
            rec.x_dhl_weight_from = 0
            rec.x_dhl_weight_to = 0
            rec.x_dhl_shipping_rate = 0

            rec.x_ups_weight_from = 0
            rec.x_ups_weight_to = 0
            rec.x_ups_shipping_rate = 0

            rec.x_dhl_charges = [(5, 0, 0)]
            rec.x_total_dhl = 0
            rec.x_ups_charges = [(5, 0, 0)]
            rec.x_total_ups = 0

            sale_order_date = rec.date_order.date()
            if rec.x_shipment_weight == 0:
                return
            # DHL Calculations
            shipping_rate = self.env['shipping.rates'].search(
                [('x_carrier', '=', 2), ('x_zone', '=', rec.x_dhl_export_zone.id),
                 ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                 ('x_multiplier', '=', False), ('x_shipping', 'in', ['export', 'import_export']),
                 ('x_weight_from', '<', rec.x_shipment_weight), ('x_weight_to', '>=', rec.x_shipment_weight)], limit=1)
            if shipping_rate:
                rec.x_dhl_weight_from = shipping_rate.x_weight_from
                rec.x_dhl_weight_to = shipping_rate.x_weight_to
                shipping_rate = shipping_rate.x_rate
                rec.x_dhl_shipping_rate = shipping_rate
                rec.x_dhl_charges = [(5, 0, 0)]
                rec.x_dhl_charges = [(0, 0, {
                    'x_sale_order_id': rec._origin.id,
                    'x_name': 'Shipping Rate',
                    'x_amount': shipping_rate,
                })]
                subtotal = shipping_rate
                carrier = self.env['delivery.carrier'].search([('id', '=', 2)])
                for charges in carrier.x_export_charges:
                    if charges.x_name == 'Emergency Situation Surcharge':
                        rec.x_dhl_charges = [(0, 0, {
                            'x_sale_order_id': rec._origin.id,
                            'x_name': charges.x_name,
                            'x_amount': rec.x_dhl_weight_to * rec.x_delivery_country.x_emergency_situation_surcharge,
                        })]
                        subtotal += rec.x_dhl_weight_to * rec.x_delivery_country.x_emergency_situation_surcharge
                    elif charges.x_name == 'Fuel Surcharge':
                        fuel_surcharge = self.env['fuel.surcharge'].search(
                            [('x_carrier', '=', 2), ('x_date_from', '<=', sale_order_date)], limit=1).x_rate
                        if fuel_surcharge:
                            rec.x_dhl_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name,
                                'x_amount': shipping_rate * fuel_surcharge,
                            })]
                            subtotal += shipping_rate * fuel_surcharge
                    elif 'GST' not in charges.x_name:
                        if charges.x_type == 'fix':
                            rec.x_dhl_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name,
                                'x_amount': charges.x_amount,
                            })]
                            subtotal += charges.x_amount
                        elif charges.x_type == 'percentage':
                            rec.x_dhl_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                'x_amount': shipping_rate * charges.x_percentage,
                            })]
                            subtotal += shipping_rate * charges.x_percentage
                rec.x_total_dhl += subtotal
                for charges in carrier.x_export_charges:
                    if 'GST' in charges.x_name:
                        rec.x_dhl_charges = [(0, 0, {
                            'x_sale_order_id': rec._origin.id,
                            'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                            'x_amount': subtotal * charges.x_percentage,
                        })]
                        rec.x_total_dhl += subtotal * charges.x_percentage
            elif not shipping_rate:
                shipping_rate = self.env['shipping.rates'].search(
                    [('x_carrier', '=', 2), ('x_zone', '=', rec.x_dhl_export_zone.id),
                     ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                     ('x_multiplier', '=', False), ('x_shipping', 'in', ['export', 'import_export']),
                     ('x_weight_from', '<', 30), ('x_weight_to', '>=', 30)], limit=1).x_rate
                if rec.x_shipment_weight > 30:
                    shipment_weight = rec.x_shipment_weight - 30 if rec.x_shipment_weight <= 70 else 40
                    shipping_rate_m = self.env['shipping.rates'].search(
                        [('x_carrier', '=', 2), ('x_zone', '=', rec.x_dhl_export_zone.id),
                         ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                         ('x_multiplier', '=', True), ('x_shipping', 'in', ['export', 'import_export']),
                         ('x_weight_from', '<', 70), ('x_weight_to', '>=', 70)], limit=1)
                    shipping_rate += shipping_rate_m.x_rate * shipment_weight
                    rec.x_dhl_weight_from = shipping_rate_m.x_weight_from
                    rec.x_dhl_weight_to = shipping_rate_m.x_weight_to
                if rec.x_shipment_weight > 70:
                    shipment_weight = rec.x_shipment_weight - 70 if rec.x_shipment_weight <= 300 else 230
                    shipping_rate_m = self.env['shipping.rates'].search(
                        [('x_carrier', '=', 2), ('x_zone', '=', rec.x_dhl_export_zone.id),
                         ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                         ('x_multiplier', '=', True), ('x_shipping', 'in', ['export', 'import_export']),
                         ('x_weight_from', '<', 300), ('x_weight_to', '>=', 300)], limit=1)
                    shipping_rate += shipping_rate_m.x_rate * shipment_weight
                    rec.x_dhl_weight_from = shipping_rate_m.x_weight_from
                    rec.x_dhl_weight_to = shipping_rate_m.x_weight_to
                if rec.x_shipment_weight > 300:
                    shipment_weight = rec.x_shipment_weight - 300
                    shipping_rate_m = self.env['shipping.rates'].search(
                        [('x_carrier', '=', 2), ('x_zone', '=', rec.x_dhl_export_zone.id),
                         ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                         ('x_multiplier', '=', True), ('x_shipping', 'in', ['export', 'import_export']),
                         ('x_weight_from', '<', 99999), ('x_weight_to', '>=', 99999)], limit=1)
                    shipping_rate += shipping_rate_m.x_rate * shipment_weight
                    rec.x_dhl_weight_from = shipping_rate_m.x_weight_from
                    rec.x_dhl_weight_to = shipping_rate_m.x_weight_to

                if shipping_rate:
                    rec.x_dhl_shipping_rate = shipping_rate
                    rec.x_dhl_charges = [(5, 0, 0)]
                    rec.x_dhl_charges = [(0, 0, {
                        'x_sale_order_id': rec._origin.id,
                        'x_name': 'Shipping Rate',
                        'x_amount': shipping_rate,
                    })]
                    subtotal = shipping_rate
                    carrier = self.env['delivery.carrier'].search([('id', '=', 2)])
                    for charges in carrier.x_export_charges:
                        if charges.x_name == 'Emergency Situation Surcharge':
                            rec.x_dhl_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name,
                                'x_amount': rec.x_shipment_weight * rec.x_delivery_country.x_emergency_situation_surcharge,
                            })]
                            subtotal += rec.x_shipment_weight * rec.x_delivery_country.x_emergency_situation_surcharge
                        elif charges.x_name == 'Fuel Surcharge':
                            fuel_surcharge = self.env['fuel.surcharge'].search(
                                [('x_carrier', '=', 2), ('x_date_from', '<=', sale_order_date)], limit=1).x_rate
                            if fuel_surcharge:
                                rec.x_dhl_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name,
                                    'x_amount': shipping_rate * fuel_surcharge,
                                })]
                                subtotal += shipping_rate * fuel_surcharge
                        elif 'GST' not in charges.x_name:
                            if charges.x_type == 'fix':
                                rec.x_dhl_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name,
                                    'x_amount': charges.x_amount,
                                })]
                                subtotal += charges.x_amount
                            elif charges.x_type == 'percentage':
                                rec.x_dhl_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                    'x_amount': shipping_rate * charges.x_percentage,
                                })]
                                subtotal += shipping_rate * charges.x_percentage
                    rec.x_total_dhl += subtotal
                    for charges in carrier.x_export_charges:
                        if 'GST' in charges.x_name:
                            rec.x_dhl_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                'x_amount': subtotal * charges.x_percentage,
                            })]
                            rec.x_total_dhl += subtotal * charges.x_percentage
            shipping_rate = self.env['shipping.rates'].search(
                [('x_carrier', '=', 6), ('x_zone', '=', rec.x_ups_export_zone.id),
                 ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                 ('x_multiplier', '=', False), ('x_shipping', 'in', ['export', 'import_export']),
                 ('x_weight_from', '<', rec.x_shipment_weight), ('x_weight_to', '>=', rec.x_shipment_weight)], limit=1)
            if shipping_rate:
                rec.x_ups_weight_from = shipping_rate.x_weight_from
                rec.x_ups_weight_to = shipping_rate.x_weight_to
                shipping_rate = shipping_rate.x_rate
                rec.x_ups_shipping_rate = shipping_rate

                rec.x_ups_charges = [(5, 0, 0)]
                rec.x_ups_charges = [(0, 0, {
                    'x_sale_order_id': rec._origin.id,
                    'x_name': 'Shipping Rate',
                    'x_amount': shipping_rate,
                })]
                subtotal = shipping_rate
                carrier = self.env['delivery.carrier'].search([('id', '=', 6)])
                for charges in carrier.x_export_charges:
                    if charges.x_name == 'Fuel Surcharge':
                        fuel_surcharge = self.env['fuel.surcharge'].search(
                            [('x_carrier', '=', 6), ('x_date_from', '<=', sale_order_date)], limit=1).x_rate
                        if fuel_surcharge:
                            rec.x_ups_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name,
                                'x_amount': shipping_rate * fuel_surcharge,
                            })]
                            subtotal += shipping_rate * fuel_surcharge
                    elif 'GST' not in charges.x_name:
                        if charges.x_type == 'fix':
                            rec.x_ups_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name,
                                'x_amount': charges.x_amount,
                            })]
                            subtotal += charges.x_amount
                        elif charges.x_type == 'percentage':
                            rec.x_ups_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                'x_amount': shipping_rate * charges.x_percentage,
                            })]
                            subtotal += shipping_rate * charges.x_percentage
                rec.x_total_ups += subtotal
                for charges in carrier.x_export_charges:
                    if 'GST' in charges.x_name:
                        rec.x_ups_charges = [(0, 0, {
                            'x_sale_order_id': rec._origin.id,
                            'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                            'x_amount': subtotal * charges.x_percentage,
                        })]
                        rec.x_total_ups += subtotal * charges.x_percentage
            elif not shipping_rate and rec.x_shipment_weight > 70:
                shipping_rate = self.env['shipping.rates'].search(
                    [('x_carrier', '=', 6), ('x_zone', '=', rec.x_ups_export_zone.id),
                     ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                     ('x_multiplier', '=', False), ('x_shipping', 'in', ['export', 'import_export']),
                     ('x_weight_from', '<', 70), ('x_weight_to', '>=', 70)], limit=1).x_rate
                if rec.x_shipment_weight > 70:
                    shipment_weight = rec.x_shipment_weight - 70
                    shipping_rate_m = self.env['shipping.rates'].search(
                        [('x_carrier', '=', 6), ('x_zone', '=', rec.x_ups_export_zone.id),
                         ('x_date_from', '<=', sale_order_date), ('x_date_to', '>=', sale_order_date),
                         ('x_multiplier', '=', True), ('x_shipping', 'in', ['export', 'import_export']),
                         ('x_weight_from', '<', 99999), ('x_weight_to', '>=', 99999)], limit=1)
                    shipping_rate += shipping_rate_m.x_rate * shipment_weight
                    rec.x_ups_weight_from = shipping_rate_m.x_weight_from
                    rec.x_ups_weight_to = shipping_rate_m.x_weight_to

                if shipping_rate:
                    rec.x_ups_shipping_rate = shipping_rate
                    rec.x_ups_charges = [(5, 0, 0)]
                    rec.x_ups_charges = [(0, 0, {
                        'x_sale_order_id': rec._origin.id,
                        'x_name': 'Shipping Rate',
                        'x_amount': shipping_rate,
                    })]
                    subtotal = shipping_rate
                    carrier = self.env['delivery.carrier'].search([('id', '=', 6)])
                    for charges in carrier.x_export_charges:
                        if charges.x_name == 'Fuel Surcharge':
                            fuel_surcharge = self.env['fuel.surcharge'].search(
                                [('x_carrier', '=', 6), ('x_date_from', '<=', sale_order_date)], limit=1).x_rate
                            if fuel_surcharge:
                                rec.x_ups_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name,
                                    'x_amount': shipping_rate * fuel_surcharge,
                                })]
                                subtotal += shipping_rate * fuel_surcharge
                        elif 'GST' not in charges.x_name:
                            if charges.x_type == 'fix':
                                rec.x_ups_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name,
                                    'x_amount': charges.x_amount,
                                })]
                                subtotal += charges.x_amount
                            elif charges.x_type == 'percentage':
                                rec.x_ups_charges = [(0, 0, {
                                    'x_sale_order_id': rec._origin.id,
                                    'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                    'x_amount': shipping_rate * charges.x_percentage,
                                })]
                                subtotal += shipping_rate * charges.x_percentage
                    rec.x_total_ups += subtotal
                    for charges in carrier.x_export_charges:
                        if 'GST' in charges.x_name:
                            rec.x_ups_charges = [(0, 0, {
                                'x_sale_order_id': rec._origin.id,
                                'x_name': charges.x_name + '@' + str(charges.x_percentage * 100) + '%',
                                'x_amount': subtotal * charges.x_percentage,
                            })]
                            rec.x_total_ups += subtotal * charges.x_percentage

    @api.depends('order_line')
    def _compute_total(self):
        for rec in self:
            total_without_discount = 0
            total_discount = 0
            for line in rec.order_line:
                total_without_discount += line.price_unit * line.product_uom_qty
                total_discount += line.price_unit * line.product_uom_qty * line.discount / 100
            rec.x_total_without_discount = total_without_discount
            rec.x_total_discount = total_discount

    @api.depends('state')
    def _compute_tags(self):
        for rec in self:
            if rec.company_id.id == 2:
                continue
            if rec.state == 'sale':
                if not rec.x_task_id:
                    rec.create_project_task()
                elif rec.x_task_id.stage_id.id == 26:
                    tag_id = self.env['project.tags'].search([('name', '=', 'Payment Pending')], limit=1).id
                    rec.x_tag_ids = [tag_id]
                    rec.update_project_task()
                    rec.x_task_id.stage_id = 4

    @api.depends('order_line')
    def _compute_contain_pelab(self):
        for rec in self:
            rec.x_contain_pelab = False
            for line in rec.order_line:
                if 'PELab' in line.product_id.name:
                    rec.x_contain_pelab = True
                    break

    @api.depends('date_order')
    def update_start_task_on(self):
        for record in self:
            record.x_start_task_on = record.date_order

    @api.depends('x_folder_name', 'state')
    def update_task_name(self):
        for record in self:
            record.x_task_name = record.x_folder_name

    @api.depends('x_start_task_on', 'x_lead_time')
    def update_deadline(self):
        for record in self:
            if record.x_start_task_on:
                if record.x_lead_time:
                    if record.x_lead_time == '1 day':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(1)
                    elif record.x_lead_time == '2-3 days':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(3)
                    elif record.x_lead_time == '1 week':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(7)
                    elif record.x_lead_time == '2 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(14)
                    elif record.x_lead_time == '3 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(21)
                    elif record.x_lead_time == '4 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(28)
                    elif record.x_lead_time == '5 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(35)
                    elif record.x_lead_time == '6 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(42)
                    elif record.x_lead_time == '7 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(49)
                    elif record.x_lead_time == '8 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(56)
                    elif record.x_lead_time == '10 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(70)
                    elif record.x_lead_time == '12 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(84)
                    elif record.x_lead_time == '18 weeks':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(126)
                    elif record.x_lead_time == '6 months':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(180)
                    elif record.x_lead_time == '1 year':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(365)
                    elif record.x_lead_time == '2 year':
                        record.x_deadline = record.x_start_task_on + datetime.timedelta(730)
                else:
                    record.x_deadline = record.x_start_task_on
                if record.x_deadline:
                    record.x_production_deadline = record.x_deadline - datetime.timedelta(5)

    @api.depends('x_processes')
    def update_task_list(self):
        for record in self:
            record.x_tasks = [(5, 0, 0)]
            for process in record.x_processes:
                for task in process.x_tasks:
                    add00 = True

                    add01 = False
                    add02 = False
                    add03 = False
                    add04 = False
                    add05 = False
                    add06 = False
                    add07 = False
                    add08 = False
                    add09 = False
                    add10 = False

                    for condition in task.x_conditions:
                        if condition.x_model.model == record._name:
                            condition_field = condition.x_field_id.name

                            for model in self.env['ir.model'].search([('model', '=', record._name)]):
                                for field in model.field_id:
                                    if field.name == condition_field:
                                        condition_value = ''
                                        condition_value = condition.x_value
                                        field_value = ''
                                        field_value = record[condition_field]

                                        if field.ttype == 'many2one':
                                            if record[condition_field].name:
                                                field_value = record[condition_field].name

                                        if task.x_check == 'All':
                                            if condition.x_relation == 'equals':
                                                if record[condition_field]:
                                                    if field_value != condition_value:
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'not equals':
                                                if record[condition_field]:
                                                    if field_value == condition_value:
                                                        add00 = False
                                                elif not record[condition_field] and condition_value == '':
                                                    add00 = False
                                            elif condition.x_relation == 'is set':
                                                if not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is not set':
                                                if record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'contains':
                                                if record[condition_field] and condition_value:
                                                    if not condition_value in field_value:
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'does not contain':
                                                if record[condition_field] and condition_value:
                                                    if condition_value in field_value:
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is greater than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) >= int(field_value):
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is less than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) <= int(field_value):
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is greater than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) > int(field_value):
                                                        add00 = False
                                                elif not record[condition_field]:
                                                    add00 = False
                                            elif condition.x_relation == 'is less than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) < int(field_value):
                                                        add00 = False
                                                elif record[condition_field]:
                                                    add00 = False
                                        elif task.x_check == 'Any':
                                            if condition.x_relation == 'equals':
                                                if record[condition_field] and condition_value:
                                                    if field_value == condition_value:
                                                        add01 = True
                                                        break
                                                elif not record[condition_field] and not condition_value:
                                                    add01 = True
                                                    break
                                            elif condition.x_relation == 'not equals':
                                                if record[condition_field] and condition_value:
                                                    if field_value != condition_value:
                                                        add02 = True
                                                        break
                                                elif not record[condition_field] and condition_value:
                                                    add02 = True
                                                    break
                                                elif record[condition_field] and not condition_value:
                                                    add02 = True
                                                    break
                                            elif condition.x_relation == 'is set':
                                                if record[condition_field]:
                                                    add03 = True
                                                    break
                                            elif condition.x_relation == 'is not set':
                                                if not record[condition_field]:
                                                    add04 = True
                                                    break
                                            elif condition.x_relation == 'contains':
                                                if record[condition_field] and condition_value:
                                                    if condition_value in field_value:
                                                        add06 = True
                                                        break
                                                elif not record[condition_field] and not condition_value:
                                                    add06 = True
                                                    break
                                                elif record[condition_field] and not condition_value:
                                                    add06 = True
                                                    break
                                            elif condition.x_relation == 'does not contain':
                                                if record[condition_field] and condition_value:
                                                    if not condition_value in field_value:
                                                        add06 = True
                                                        break
                                                elif not record[condition_field] and condition_value:
                                                    add06 = True
                                                    break
                                            elif condition.x_relation == 'is greater than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) < int(field_value):
                                                        add07 = True
                                                        break
                                                elif record[condition_field]:
                                                    add07 = True
                                                    break
                                            elif condition.x_relation == 'is less than':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) > int(field_value):
                                                        add08 = True
                                                        break
                                                elif not record[condition_field]:
                                                    add08 = True
                                                    break
                                            elif condition.x_relation == 'is greater than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) <= int(field_value):
                                                        add09 = True
                                                        break
                                                elif record[condition_field]:
                                                    add09 = True
                                                    break
                                            elif condition.x_relation == 'is less than and equal to':
                                                if record[condition_field] and condition_value:
                                                    if int(condition_value) >= int(field_value):
                                                        add10 = True
                                                        break
                                                elif not record[condition_field]:
                                                    add10 = True
                                                    break
                                if (
                                        add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                                    break
                        if (
                                add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                            break

                    if add00 and task.x_check == 'All':
                        task.x_task_name = '[' + str(process.x_name) + '] [' + str(task.x_name) + '] ' + str(
                            record.x_task_name)
                        record.x_tasks = [(4, task.id)]

                    elif (
                            add01 or add02 or add03 or add04 or add05 or add06 or add07 or add08 or add09 or add10) and task.x_check == 'Any':
                        task.x_task_name = '[' + str(process.x_name) + '] [' + str(task.x_name) + '] ' + str(
                            record.x_task_name)
                        record.x_tasks = [(4, task.id)]

    @api.depends('x_update_freight', 'carrier_id', 'x_tracking_reference')
    def freight_calculation(self):
        for rec in self:
            weight = 0.00
            freight = 0.00

            pos = self.env['purchase.order'].search([('x_item_type', '=', 'Cost of Freight Sold')])
            for po in pos:
                if rec.name in po.x_related_so_s.mapped('name'):
                    currency_rate = self.env['res.currency.rate'].search([('currency_id', '=', po.currency_id.id),
                                                                          ('name', '=',
                                                                           po.date_order.strftime('%Y-%m-%d'))]).rate
                    freight += round(po.amount_total / currency_rate, 2) if currency_rate else self.env[
                        'res.currency'].search([('id', '=', po.currency_id.id)]).rate
                    weight += po.x_weight_kg

            rec.x_total_freight = freight
            rec.x_total_weight = weight
            rec.x_freight_per_kg = round(freight / weight, 2) if weight != 0 else 0

    @api.depends('name', 'partner_id', 'client_order_ref', 'company_id')
    def update_folder_name(self):
        for record in self:
            record.x_folder_name = record.name
            record.x_folder_name += ' - TarazPK' if record.company_id.id == 1 else ' - TarazTR'
            if record.partner_id:
                if record.partner_id.country_id:
                    record.x_folder_name += ' - ' + record.partner_id.country_id.name
                if record.partner_id.parent_id:
                    record.x_folder_name += ' - ' + record.partner_id.parent_id.name
                if record.partner_id.name:
                    record.x_folder_name += ' - ' + record.partner_id.name
            if record.client_order_ref:
                record.x_folder_name += ' - ' + record.client_order_ref

    # -----------------------------------------ON CHANGE--------------------------------------------
    @api.onchange('payment_term_id')
    def update_term_sale_order_list(self):
        term_ids = self.env['account.payment.term'].search([])
        for term in term_ids:
            order_ids = self.env['sale.order'].search([('payment_term_id', '=', term.id)]).ids
            term.x_order_ids = [(6, 0, order_ids)]

    @api.onchange('order_line')
    def update_stock_level(self):
        for record in self:
            record.x_stock_level = [(5, 0, 0)]
            for lines in record.order_line:
                if lines.product_id.x_product_group:
                    products = self.env['product.product'].search(
                        [('x_product_group', '=', lines.product_id.x_product_group.id)])
                    for product in products:
                        if product.sale_ok:
                            record.x_stock_level = [(4, product.id)]
                else:
                    products = self.env['product.product'].search([('name', '=', lines.product_id.name)])
                    for product in products:
                        if product.sale_ok:
                            record.x_stock_level = [(4, product.id)]

    @api.onchange('amount_total')
    def update_ui_value(self):
        for record in self:
            if record.amount_total != 0:
                record.x_ui_value = round(record.amount_total / 10, 2)

    @api.onchange('partner_id')
    def update_end_user(self):
        for record in self:
            record.x_end_user = record.partner_id.id

    @api.onchange('state', 'x_task_name', 'x_start_task_on', 'x_deadline', 'x_notes', 'x_tag_ids', 'x_tasks',
                  'x_user_responsible', 'x_user_participants', 'x_user_observers')
    def update_project_task(self):
        for rec in self:
            record_task = rec._origin.x_task_id
            if record_task:
                record_task.name = rec.x_task_name
                record_task.user_id = rec.x_user_responsible.id
                record_task.x_user_participants = rec.x_user_participants.ids
                record_task.x_user_observers = rec.x_user_observers.ids
                record_task.x_start_task_on = rec.x_start_task_on
                record_task.date_deadline = rec.x_deadline if rec.state not in ['draft', 'sent'] else False
                record_task.x_notes = rec.x_notes
                record_task.tag_ids = rec.x_tag_ids.ids
                subtasks = record_task.x_subtask_list.mapped('x_name')
                for task in rec.x_tasks:
                    if task.x_name not in subtasks:
                        record_task.x_subtask_list = [(0, 0, {
                            'x_task_id': record_task.id,
                            'x_name': task.x_name,
                            'x_user_id': task.x_user_responsible.id,
                            'x_user_participants': task.x_user_participants.ids,
                            'x_user_observers': task.x_user_observers.ids,
                            'x_notes': task.x_description,
                            'x_checklist_items': task.x_checklist_items.ids,
                            'x_project_id': task.x_project_id.id,
                            'x_project_stage_id': task.x_project_stage_id.id,
                            'x_deadline': rec.x_deadline,
                        })]
                    else:
                        for subtask in record_task.x_subtask_list:
                            if task.x_name == subtask.x_name:
                                record_task.x_subtask_list = [(1, subtask.id, {
                                    'x_name': task.x_name,
                                    'x_user_id': task.x_user_responsible.id,
                                    'x_user_participants': task.x_user_participants.ids,
                                    'x_user_observers': task.x_user_observers.ids,
                                    'x_notes': task.x_description,
                                    'x_checklist_items': task.x_checklist_items.ids,
                                    'x_project_id': task.x_project_id.id,
                                    'x_project_stage_id': task.x_project_stage_id.id,
                                    'x_deadline': rec.x_deadline,
                                })]

                # subtasks = rec.x_tasks.mapped('x_name')
                # for task in record_task.x_subtask_list:
                #     if task.x_name not in subtasks:
                #         if task.x_created_task_id:
                #             task.x_created_task_id.unlink()
                #         task.unlink()

                if record_task.x_subtask_list:
                    record_task.x_subtask_list_hide = False
                else:
                    record_task.x_subtask_list_hide = True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_internal_notes = fields.Text(string="Internal Notes", required=False, )
