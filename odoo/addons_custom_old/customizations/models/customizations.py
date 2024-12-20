from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    x_notes = fields.Text(string="Notes", required=False)
    x_valuation_adjustment_lines = fields.One2many(
        'stock.valuation.adjustment.lines', 'cost_id', 'Valuation Adjustments',
        states={'done': [('readonly', True)]})


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    x_add_in_landed_cost = fields.Boolean(string="Add", related='product_id.x_add_in_landed_cost', readonly=False, store=True)
    x_custom_duty_value = fields.Float('Custom Duty Value', digits='Duties', required=False)
    x_additional_custom_duty_value = fields.Float('Additional Custom Duty Value', digits='Duties', required=False)
    x_regulatory_duty_value = fields.Float('Regulatory Duty Value', digits='Duties', required=False)
    x_weight = fields.Float('Product Weight', related='product_id.weight', store=True, readonly=False)
    x_volume = fields.Float('Product Volume', related='product_id.volume', store=True, readonly=False)
    x_custom_duty = fields.Float('Custom Duty', related='product_id.x_custom_duty', store=True, readonly=False)
    x_additional_custom_duty = fields.Float('Additional Custom Duty', related='product_id.x_additional_custom_duty', store=True, readonly=False)
    x_regulatory_duty = fields.Float('Regulatory Duty', related='product_id.x_regulatory_duty', store=True, readonly=False)
    x_split_method = fields.Selection(selection=[
        ('equal', 'Equal'),
        ('by_quantity', 'By Quantity'),
        ('by_current_cost_price', 'By Current Cost'),
        ('by_weight', 'By Weight'),
        ('by_volume', 'By Volume'),
        ('custom_duty', 'Custom Duty'),
        ('additional_custom_duty', 'Additional Custom Duty'),
        ('regulatory_duty', 'Regulatory Duty'),
    ], string="Split Method", required=False, )


class TransferPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    x_report_msg = fields.Html(
        'Report Message', translate=True,
        help='Message displayed to explain and help the payment process.')

    x_report_code = fields.Char(string="Report Code", required=False, )


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    x_reference = fields.Char(string="Reference", related="stock_move_id.reference", )
    x_origin = fields.Char(string="Source Document", related="stock_move_id.origin", )


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    x_journal_entry_id = fields.Many2one(comodel_name="account.move", string="Journal Entry", required=False,
                                         compute="_get_journal_entry", store=True, )

    @api.depends('name', 'product_id')
    def _get_journal_entry(self):
        for rec in self:
            rec.x_journal_entry_id = self.env['account.move'].search(
                [('ref', 'ilike', rec.name), ('ref', 'ilike', rec.product_id.name)], limit=1).id


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_linked_with_bill = fields.Boolean(string="Linked Payment", required=False, store=True,
                                        compute="_check_link_with_bill", )

    def open_record(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_account_payment_form').id,
                'res_id': rec.id,
            }

    @api.depends('state', 'name', 'amount', 'payment_date', 'communication', 'invoice_ids', 'reconciled_invoices_count')
    def _check_link_with_bill(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.x_linked_with_bill = False
            elif rec.reconciled_invoices_count != 0:
                rec.x_linked_with_bill = True
            elif len(rec.invoice_ids.ids) != 0:
                rec.x_linked_with_bill = True
            elif rec.move_reconciled:
                rec.x_linked_with_bill = True
            elif 'SALARY' in str(rec.communication) or 'Salary' in str(rec.communication):
                rec.x_linked_with_bill = True
            else:
                rec.x_linked_with_bill = False


class ProjectTaskTimeSheet(models.Model):
    _inherit = 'account.analytic.line'

    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date', readonly=1)
    timer_duration = fields.Float(invisible=1, string='Time Duration (Minutes)')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    x_image_ids = fields.One2many(comodel_name="odoo.image", inverse_name="x_maintenance_equipment_id", string="Images",
                                  required=False, )


class Country(models.Model):
    _inherit = "res.country"

    x_dhl_import_zone = fields.Many2one(comodel_name="shipping.zone", string="DHL Import Zone", required=False, )
    x_dhl_export_zone = fields.Many2one(comodel_name="shipping.zone", string="DHL Export Zone", required=False, )
    x_ups_import_zone = fields.Many2one(comodel_name="shipping.zone", string="UPS Import Zone", required=False, )
    x_ups_export_zone = fields.Many2one(comodel_name="shipping.zone", string="UPS Export Zone", required=False, )

    x_region = fields.Many2one(comodel_name="country.regions", string="Country Region", required=False, )
    x_subregion = fields.Many2one(comodel_name="country.subregions", string="Country Sub-region", required=False, )

    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_emergency_situation_surcharge = fields.Float(string="DHL Emergency Situation Surcharge", required=False, )


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    x_export_charges = fields.One2many(comodel_name="shipping.export.charges", inverse_name="x_carrier_id",
                                       string="Export Charges", required=False, )
    x_import_charges = fields.One2many(comodel_name="shipping.import.charges", inverse_name="x_carrier_id",
                                       string="Import Charges", required=False, )


class Images(models.Model):
    _inherit = "odoo.image"

    x_project_task_id = fields.Many2one(comodel_name="project.task", string="Project Task ID", required=False, )
    x_maintenance_equipment_id = fields.Many2one(comodel_name="maintenance.equipment",
                                                 string="Maintenance Equipment ID", required=False, )


class UtmCampaign(models.Model):
    _name = 'utm.campaign'
    _inherit = ['utm.campaign', 'mail.thread', 'mail.activity.mixin']

    x_campaign_id = fields.Many2one(comodel_name="campaign.group", string="Campaign", required=True, tracking=True,
                                    track_visibility='always', )

    x_relation_01 = fields.Selection(string="Company Type Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_02 = fields.Selection(string="Company Status Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_03 = fields.Selection(string="Customer Status Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_04 = fields.Selection(string="Customer Department Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_05 = fields.Selection(string="Area of Interests Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_06 = fields.Selection(string="Products Interest Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )
    x_relation_07 = fields.Selection(string="Products Purchased Relation",
                                     selection=[('or', 'Or'), ('and', 'And'), ('n_a', 'N/A'), ], required=True,
                                     default="n_a", tracking=True, track_visibility='always', )

    x_operation_01 = fields.Selection(string="Customer Department Operation",
                                      selection=[('any', 'Any'), ('all', 'All'), ('equal', 'Equal'), ], required=True,
                                      default="any", tracking=True, track_visibility='always', )
    x_operation_02 = fields.Selection(string="Area of Interests Operation",
                                      selection=[('any', 'Any'), ('all', 'All'), ('equal', 'Equal'), ], required=True,
                                      default="any", tracking=True, track_visibility='always', )
    x_operation_03 = fields.Selection(string="Products Interest Operation",
                                      selection=[('any', 'Any'), ('all', 'All'), ('equal', 'Equal'), ], required=True,
                                      default="any", tracking=True, track_visibility='always', )

    x_company_type = fields.Selection(selection=[
        ('University', 'University'),
        ('Industry', 'Industry'),
        ('any', 'Any'), ], string="Company Type", default="any", required=True, tracking=True,
        track_visibility='always', )
    x_company_status = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'),
        ('Enquirer_Customer', 'Enquirer or Customer'),
        ('Enquirer_Targeted', 'Enquirer or Targeted'),
        ('Customer_Targeted', 'Customer or Targeted'),
        ('any', 'Any'), ], string="Company Status", default="any", required=True, tracking=True,
        track_visibility='always', )
    x_customer_status = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'),
        ('Enquirer_Customer', 'Enquirer or Customer'),
        ('Enquirer_Targeted', 'Enquirer or Targeted'),
        ('Customer_Targeted', 'Customer or Targeted'),
        ('any', 'Any'), ], string="Customer Status", default="any", required=True, tracking=True,
        track_visibility='always', )
    x_customer_group_ids = fields.Many2many(comodel_name="partner.group", relation="partner_group_utm_campaign_rel",
                                            column1="partner_group_id", column2="utm_campaign_id",
                                            string="Customer Department", tracking=True, track_visibility='always', )
    x_interest_ids = fields.Many2many(comodel_name="partner.interest", relation="partner_interest_utm_campaign_rel",
                                      column1="partner_interest_id", column2="utm_campaign_id",
                                      string="Area of Interests", tracking=True, track_visibility='always', )
    x_interested_product_ids = fields.Many2many(comodel_name="product.group",
                                                relation="product_group_utm_campaign_rel_1",
                                                column1="product_group_id", column2="utm_campaign_id",
                                                string="Products Interest", tracking=True, track_visibility='always', )
    x_purchased_product_ids = fields.Many2many(comodel_name="product.group",
                                               relation="product_group_utm_campaign_rel_2",
                                               column1="product_group_id", column2="utm_campaign_id",
                                               string="Products Purchased", tracking=True, track_visibility='always', )

    x_comment = fields.Text(string="Notes", required=False, tracking=True, track_visibility='always', )

    def action_edit_mailing_content(self):
        action = self.env.ref('mass_mailing.action_view_mass_mailings_from_campaign').read()[0]
        form_view = [(self.env.ref('mass_mailing.view_mail_mass_mailing_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        mailing_id = self.env['mailing.mailing'].search([('campaign_id', '=', self.id)], limit=1,
                                                        order='create_date desc')
        action['res_id'] = mailing_id.id
        return action

    def create_new_mailing_for_current_campaign(self):
        campaign_ids = self.env['utm.campaign'].search([])

    @api.model
    def create_new_mailings(self):
        campaign_ids = self.env['utm.campaign'].search([])


class MassMailing(models.Model):
    _inherit = 'mailing.mailing'

    x_contact_ids = fields.Many2many(comodel_name="mailing.contact", relation="mailing_contact_mailing_mailing_rel",
                                     column1="mailing_contact_id", column2="mailing_mailing_id", string="Contacts",
                                     compute="get_mailing_contacts", store=True, )

    def stop_resume_email(self):
        for rec in self:
            rec.state = 'stopped'

    @api.depends('contact_list_ids', 'mailing_model_id', 'mailing_model_name')
    def get_mailing_contacts(self):
        for rec in self:
            rec.mailing_domain = []
            rec.x_contact_ids = [(6, 0, rec.contact_list_ids.contact_ids.ids)]
            rec._onchange_model_and_list()

    @api.model
    def create(self, values):
        user_id = self.env['res.users'].search([('id', '=', 34)])
        if user_id:
            values['email_from'] = tools.formataddr((user_id.name, user_id.email))
            values['reply_to'] = tools.formataddr((user_id.name, user_id.email))
        return super(MassMailing, self).create(values)

    @api.constrains('subject')
    def _update_mailing_name(self):
        self.name = self.subject

    def unlink(self):
        for contact_list in self.contact_list_ids:
            if contact_list.name != 'New Mailing': contact_list.unlink()
        return super(MassMailing, self).unlink()


class MassMailingContact(models.Model):
    _inherit = 'mailing.contact'

    x_contact_id = fields.Many2one(comodel_name="res.partner", string="Contact", )

    x_name = fields.Char(string="Name", required=False, related="x_contact_id.name", readonly=False, )
    x_tag_ids = fields.Many2many(comodel_name="res.partner.category",
                                 relation="mailing_contact_res_partner_category_rel_00",
                                 column1="mailing_contact_id", column2="res_partner_category_id", string="Tags",
                                 related="x_contact_id.category_id", readonly=False, )

    x_email = fields.Char(string="Email", required=False, related="x_contact_id.email", readonly=False, )
    x_title_id = fields.Many2one(comodel_name="res.partner.title", string="Title", required=False,
                                 related="x_contact_id.title", readonly=False, )
    x_parent_id = fields.Many2one(comodel_name="res.partner", string="Company", required=False,
                                  related="x_contact_id.parent_id", readonly=False, )
    x_country_id = fields.Many2one(comodel_name="res.country", string="Country", required=False,
                                   related="x_contact_id.country_id", readonly=False, )

    x_exclude_from_newsletter = fields.Boolean(string="Excl. from NEWSLTR",
                                               related="x_contact_id.x_exclude_from_newsletter", readonly=False, )
    x_customer_status = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'), ], default="Targeted", related="x_contact_id.x_customer_status", readonly=False, )
    x_customer_group_id = fields.Many2one(comodel_name="partner.group", string="Customer Department",
                                          related="x_contact_id.x_customer_group_id", readonly=False, )
    x_team_lead_id = fields.Many2one(comodel_name="res.partner", string="Team Lead",
                                     related="x_contact_id.x_team_lead_id", readonly=False, )
    x_engagement = fields.Selection(string="Engagement", selection=[
        ('Email', 'Email'),
        ('Meeting', 'Meeting'),
        ('Call', 'Call'), ], related="x_contact_id.x_engagement", readonly=False, )
    x_distributor = fields.Boolean(string="Distributor", related="x_contact_id.x_distributor", readonly=False, )
    x_customer_ids = fields.Many2many(comodel_name="res.partner", relation="res_partner_mailing_contact_rel_00",
                                      column1="res_partner_id", column2="mailing_contact_id", string="Customers",
                                      related="x_contact_id.x_customer_ids", )

    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False,
                                    related="x_contact_id.currency_id", )
    x_total_invoiced = fields.Monetary(string="Total Invoiced", related="x_contact_id.total_invoiced", )
    x_interest_ids = fields.Many2many(comodel_name="partner.interest",
                                      relation="partner_interest_mailing_contact_rel_1",
                                      column1="partner_interest_id", column2="mailing_contact_id",
                                      string="Ind. Area of Interests",
                                      related="x_contact_id.x_interest_ids", readonly=False, )
    x_interested_product_ids = fields.Many2many(comodel_name="product.group",
                                                relation="product_group_mailing_contact_rel_1",
                                                column1="product_group_id", column2="mailing_contact_id",
                                                string="Ind. Products Interest",
                                                related="x_contact_id.x_interested_product_ids", readonly=False, )
    x_purchased_product_ids = fields.Many2many(comodel_name="product.group",
                                               relation="product_group_mailing_contact_rel_2",
                                               column1="product_group_id", column2="mailing_contact_id",
                                               string="Ind. Purchased Products",
                                               related="x_contact_id.x_purchased_product_ids", )

    x_company_status = fields.Selection(selection=[('Enquirer', 'Enquirer'),
                                                   ('Customer', 'Customer'),
                                                   ('Targeted', 'Targeted'), ], default="Targeted",
                                        string=" Company Status", related="x_contact_id.x_customer_status_comp", )
    x_company_type = fields.Selection(selection=[
        ('University', 'University'),
        ('Industry', 'Industry'), ], string="Company Type", related="x_contact_id.x_company_type_comp", )
    x_company_revenue = fields.Float(string="Company Revenue", related="x_contact_id.x_company_revenue_comp", )
    x_company_size = fields.Integer(string="Company Size", related="x_contact_id.x_company_size_comp", )
    x_distributor_comp = fields.Boolean(string="Distributor", related="x_contact_id.x_distributor_comp", )

    x_total_invoiced_comp = fields.Monetary(string="Total Invoiced", related="x_contact_id.x_total_invoiced_comp", )
    x_interest_ids_comp = fields.Many2many(comodel_name="partner.interest",
                                           relation="partner_interest_mailing_contact_rel_2",
                                           column1="partner_interest_id", column2="mailing_contact_id",
                                           string="Area of Interests",
                                           related="x_contact_id.x_interest_ids_comp", )
    x_interested_product_ids_comp = fields.Many2many(comodel_name="product.group",
                                                     relation="product_group_mailing_contact_rel_3",
                                                     column1="product_group_id", column2="mailing_contact_id",
                                                     string="Products Interest",
                                                     related="x_contact_id.x_interested_product_ids_comp", )
    x_purchased_product_ids_comp = fields.Many2many(comodel_name="product.group",
                                                    relation="product_group_mailing_contact_rel_4",
                                                    column1="product_group_id", column2="mailing_contact_id",
                                                    string="Purchased Products",
                                                    related="x_contact_id.x_purchased_product_ids_comp", )

    x_comment = fields.Text(string="Notes", related="x_contact_id.comment", readonly=False, )

    x_update_mailing_contact_data = fields.Boolean(string="Update Data", compute="update_mailing_contact_data",
                                                   store=True, )

    x_group_by_customer_status = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'), ], default="Targeted", )
    x_group_by_customer_group_id = fields.Many2one(comodel_name="partner.group", string="Customer Department", )
    x_group_by_team_lead_id = fields.Many2one(comodel_name="res.partner", string="Team Lead", )
    x_group_by_engagement = fields.Selection(string="Engagement", selection=[
        ('Email', 'Email'),
        ('Meeting', 'Meeting'),
        ('Call', 'Call'), ], )
    x_group_by_company_status = fields.Selection(selection=[('Enquirer', 'Enquirer'),
                                                            ('Customer', 'Customer'),
                                                            ('Targeted', 'Targeted'), ], default="Targeted",
                                                 string=" Company Status", )
    x_group_by_company_type = fields.Selection(selection=[
        ('University', 'University'),
        ('Industry', 'Industry'), ], string="Company Type", )

    @api.depends('x_name',
                 'x_tag_ids',
                 'x_email',
                 'x_title_id',
                 'x_parent_id',
                 'x_country_id',
                 'x_customer_status',
                 'x_customer_group_id',
                 'x_team_lead_id',
                 'x_engagement',
                 'x_company_status',
                 'x_company_type',
                 'x_exclude_from_newsletter', )
    def update_mailing_contact_data(self):
        for rec in self:
            if rec.x_contact_id and rec.x_contact_id.id:
                rec.name = rec.x_name
                rec.tag_ids = rec.x_tag_ids
                rec.email = rec.x_email
                rec.title_id = rec.x_title_id.id
                rec.company_name = rec.x_parent_id.name if rec.x_parent_id else False
                rec.country_id = rec.x_country_id.id
                rec.x_group_by_customer_status = rec.x_customer_status
                rec.x_group_by_customer_group_id = rec.x_customer_group_id.id
                rec.x_group_by_team_lead_id = rec.x_team_lead_id.id
                rec.x_group_by_engagement = rec.x_engagement
                rec.x_group_by_company_status = rec.x_company_status
                rec.x_group_by_company_type = rec.x_company_type
                for mailing_list in rec.subscription_list_ids:
                    if rec.x_exclude_from_newsletter: mailing_list.opt_out = True


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    x_order_ids = fields.Many2many(comodel_name='sale.order', string='Sale Orders')


class AccountPaymentTermLine(models.Model):
    _inherit = 'account.payment.term.line'

    x_report_remark = fields.Char(string="Report Remark", required=True, )

    @api.onchange('option', 'days')
    def update_remarks(self):
        for rec in self:
            rec.x_report_remark = ''
            if rec.option == "day_after_invoice_date" and rec.days == 0:
                rec.x_report_remark = "Advance"
            elif rec.option == "day_after_delivery_date" and rec.days == 0:
                rec.x_report_remark = "Upon Delivery"
            elif rec.option == "day_after_delivery_date" and rec.days > 0:
                rec.x_report_remark = "After Delivery"


class Note(models.Model):
    _inherit = 'note.note'

    x_model_id = fields.Many2one(comodel_name="ir.model", string="Model", required=False, )

    @api.constrains('x_model_id')
    def check_model(self):
        for rec in self:
            note_id = self.env['note.note'].search(
                [('id', '!=', rec._origin.id), ('x_model_id', '=', rec.x_model_id.id)], limit=1)
            if note_id:
                raise UserError(_("Cannot add this model.\nModel already has note assigned to it."))


# --------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- Custom Models -------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------


class CampaignGroup(models.Model):
    _name = "campaign.group"
    _description = "Campaign"
    _rec_name = "x_name"

    x_name = fields.Char(string="Campaign Name", required=False, )


class Testimonials(models.Model):
    _name = "res.testimonial"
    _description = "Testimonials"
    _rec_name = "x_product_id"

    x_partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", required=False, )
    x_date = fields.Date(string="Date", required=False, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    x_url = fields.Char(string="URL", required=False, )
    x_attachment = fields.Binary(string="Attachment", )
    x_description = fields.Text(string="Description", required=False, )
    x_quotes = fields.Text(string="Quotes", required=False, )


class ProductTags(models.Model):
    _name = "product.tags"
    _description = "Product Tags"
    _rec_name = "x_name"

    x_name = fields.Char(string="Tag Name", required=False, )


class HSCode(models.Model):
    _name = "hs.code"
    _description = "HS Code"


class SaleOrderCGS(models.Model):
    _name = "sale.order.cgs"
    _description = "Cost of Goods Sold"

    x_journal_entry_id = fields.Many2one(comodel_name="account.move", string="Journal Entry", required=False, )
    x_bos_move_id = fields.Many2one(comodel_name="account.move", string=" BOS Journal Entry", required=False, )
    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False, )
    x_partner_id = fields.Many2one(comodel_name="res.partner", string="Customer", required=False,
                                   compute="_get_sale_order_data", store=True, )
    x_date_order = fields.Date(string="Order Date", required=False, compute="_get_sale_order_data", store=True, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True, )
    x_calculation_type = fields.Selection(string="Calculation Type",
                                          selection=[('real', 'Real'), ('estimated', 'Estimated'), ], required=True,
                                          default="estimated", )
    x_type = fields.Selection(selection=[
        ('price', 'Price'),
        ('cost', 'Cost'),
        ('profit', 'Profit'),
        ('loss', 'Loss'), ], string="Amount Type", required=True, default="cost", )
    x_product_type = fields.Selection(selection=[
        ('products', 'Products'),
        ('freight', 'Freight'),
        ('discount', 'Discount'),
        ('fees', 'Fees'),
        ('other_real', 'Other Real'),
        ('other_estimated', 'Other Estimated'),
        ('bonus', 'Bonus'),
        ('investor_profit', 'Investor Share'),
        ('currency', 'Currency'), ], string="Product Type", required=True, default="other_estimated", )
    x_line_code = fields.Char(string="Line Code", required=False, compute="_compute_line_code", store=True)

    x_quantity = fields.Float(string="Quantity", required=False, )
    x_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", required=False, )
    x_currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_price_unit = fields.Float(string="Unit Price", required=False, )
    x_discount = fields.Float(string="Discount", required=False, )
    x_price_subtotal = fields.Float(string="Total Price", required=False, compute="_compute_total_price", store=True, )
    x_profit_margin = fields.Float(string="Profit Margin", required=False, )
    x_markup = fields.Float(string="Markup (%)", required=False, )
    x_cost_multiplier = fields.Float(string="Cost Multiplier", required=False, )
    x_pkr_currency_id = fields.Many2one(comodel_name="res.currency", string="PKR Currency", required=False, defualt=165)
    x_cgs_unit_pkr = fields.Float(string="Unit (PKR)", required=False, )
    x_cgs_subtotal_pkr = fields.Float(string="Total (PKR)", required=False, )
    x_note = fields.Text(string="Note", required=False, )

    x_description = fields.Text(string="Description", required=False, readonly=True, store=True, )
    x_move_line_ids = fields.Many2many(comodel_name="account.move.line",
                                       relation="sale_order_cgs_account_move_line_rel",
                                       column1="sale_order_cgs_id", column2="account_move_line_id",
                                       string="Journal Items", )

    @api.depends('x_quantity', 'x_price_unit', 'x_discount')
    def _compute_total_price(self):
        for rec in self:
            rec.x_price_subtotal = rec.x_quantity * rec.x_price_unit * (1 - rec.x_discount)

    @api.constrains('x_sale_order_id')
    @api.depends('x_sale_order_id')
    def _get_sale_order_data(self):
        for rec in self:
            rec.x_partner_id = rec.x_sale_order_id.partner_id
            rec.x_date_order = rec.x_sale_order_id.date_order.date()

    @api.depends('x_sale_order_id', 'x_product_id', 'x_calculation_type', 'x_type', 'x_product_type', )
    def _compute_line_code(self):
        for rec in self:
            if rec.x_calculation_type == "estimated" and rec.x_product_type == "other_estimated":
                rec.x_line_code = str(rec.x_sale_order_id.name) + "_" + str(rec.x_product_id.name) + "_" + \
                                  str(rec.x_calculation_type) + "_" + str(rec.x_type) + "_" + str(rec.x_product_type)


class PartnerInterest(models.Model):
    _name = "partner.interest"
    _description = "Partner Interest"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Name", required=False, )


class PartnerGroup(models.Model):
    _name = "partner.group"
    _description = "Partner Department"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Department Name", required=False, )


class FuelSurcharge(models.Model):
    _name = "fuel.surcharge"
    _description = "Fuel Surcharge"
    _rec_name = "x_name"
    _order = "x_date_from desc"

    x_name = fields.Char(string="Fuel Surcharge", required=False, store=True, compute="_compute_name", )
    x_carrier = fields.Many2one(comodel_name="delivery.carrier", string="Carrier", required=False, )
    x_date_from = fields.Date(string="Date from", required=False, )
    x_rate = fields.Float(string="Rate", required=False, )

    @api.depends('x_rate', 'x_date_from')
    def _compute_name(self):
        for rec in self:
            if rec.x_date_from and rec.x_rate:
                rec.x_name = rec.x_date_from.strftime("%B") + ' ' + rec.x_date_from.strftime("%Y") + ' @' + str(
                    rec.x_rate * 100) + '%'


class SaleOrderProducts(models.Model):
    _name = "sale.order.products"
    _description = "Sale Order Products"
    _rec_name = "x_product_id"
    _order = "x_product_id"

    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale ID", required=False, )
    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    x_short_description = fields.Char(string="Description", required=False, related="x_product_id.x_short_description",
                                      readonly=False, )
    x_gross_weight = fields.Float(string="Gross Weight (kg)", required=False, related="x_product_id.weight",
                                  readonly=False, )
    x_quantity = fields.Float(string="Quantity", required=False, )
    x_total_weight = fields.Float(string="Total Weight (kg)", required=False, store=True,
                                  compute="compute_total_weight")

    @api.depends('x_gross_weight', 'x_quantity')
    def compute_total_weight(self):
        for rec in self:
            rec.x_total_weight = rec.x_gross_weight * rec.x_quantity


class CountrySubregions(models.Model):
    _name = "country.subregions"
    _description = "Country Sub-region"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Name", required=False, )
    x_region = fields.Many2one(comodel_name="country.regions", string="Region", required=False, )


class CountryRegions(models.Model):
    _name = "country.regions"
    _description = "Country Region"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Name", required=False, )


class DHLAdditionalCharges(models.Model):
    _name = "dhl.additional.charges"
    _description = "DHL Additional Charges"
    _rec_name = "x_name"

    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale ID", required=False, )
    x_purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase ID", required=False, )
    x_name = fields.Char(string="Description", required=True, )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_amount = fields.Float(string="Amount", required=False, )


class UPSAdditionalCharges(models.Model):
    _name = "ups.additional.charges"
    _description = "UPS Additional Charges"
    _rec_name = "x_name"

    x_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale ID", required=False, )
    x_purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase ID", required=False, )
    x_name = fields.Char(string="Description", required=True, )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_amount = fields.Float(string="Amount", required=False, )


class ShippingImportCharges(models.Model):
    _name = "shipping.import.charges"
    _description = "Shipping Import Charges"
    _rec_name = "x_name"

    x_carrier_id = fields.Many2one(comodel_name="delivery.carrier", string="Carrier", required=False, )
    x_name = fields.Char(string="Label", required=True, )
    x_type = fields.Selection(string="Type", selection=[('percentage', 'Percentage'), ('fix', 'Fix'), ], required=True,
                              default='percentage')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_amount = fields.Float(string="Amount", required=False, )
    x_percentage = fields.Float(string="Percentage", required=False, )


class ShippingExportCharges(models.Model):
    _name = "shipping.export.charges"
    _description = "Shipping Export Charges"
    _rec_name = "x_name"

    x_carrier_id = fields.Many2one(comodel_name="delivery.carrier", string="Carrier", required=False, )
    x_name = fields.Char(string="Label", required=True, )
    x_type = fields.Selection(string="Type",
                              selection=[('percentage', 'Percentage'), ('fix', 'Fix'), ('none', 'None'), ],
                              required=True, default='none')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_amount = fields.Float(string="Amount", required=False, )
    x_percentage = fields.Float(string="Percentage", required=False, )


class ShippingRates(models.Model):
    _name = "shipping.rates"
    _description = "Shipping Rates"
    _rec_name = "x_name"
    _order = "x_carrier"

    x_name = fields.Char(string="Name", required=False, store=True, compute="_compute_name", )
    x_carrier = fields.Many2one(comodel_name="delivery.carrier", string="Carrier", required=False, )
    x_zone = fields.Many2one(comodel_name="shipping.zone", string="Shipping Zone", required=False, )
    x_shipping = fields.Selection(string="Shipping", selection=[('import', 'Import'), ('export', 'Export'),
                                                                ('import_export', 'Import/Export'), ], required=False, )
    x_weight_from = fields.Float(string="Weight from", required=False, )
    x_weight_to = fields.Float(string="Weight to", required=False, )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False, default=2)
    x_rate = fields.Float(string="Rate", required=False, )
    x_multiplier = fields.Boolean(string="Multiplier", help="Set to true if weight is multiplier", )
    x_date_from = fields.Date(string="Date from", required=False, )
    x_date_to = fields.Date(string="Date to", required=False, )

    @api.depends('x_carrier', 'x_zone')
    def _compute_name(self):
        for rec in self:
            if rec.x_carrier and rec.x_zone:
                rec.x_name = rec.x_carrier.name + '(' + rec.x_zone.x_name + ')'


class ShippingZone(models.Model):
    _name = "shipping.zone"
    _description = "Shipping Zone"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Zone Name", required=False, )


class Stations(models.Model):
    _name = "res.stations"
    _description = "Stations"
    _rec_name = "x_name"

    x_name = fields.Char(string="Station Name", required=True, )
    x_responsible_person_ids = fields.Many2many(comodel_name="res.users", relation="res_users_res_stations_rel",
                                                column1="res_stations_id", column2="res_users_id",
                                                string="Responsible Persons", )
    x_consumable_ids = fields.Many2many(comodel_name="product.product", relation="product_product_res_stations_rel_1",
                                        column1="res_stations_id", column2="product_product_id", string="Consumables", )
    x_items_ids = fields.Many2many(comodel_name="station.items", relation="station_items_res_stations_rel_1",
                                   column1="res_stations_id", column2="station_items_id", string="Station Items", )
    x_equipment_ids = fields.Many2many(comodel_name="product.product", relation="product_product_res_stations_rel_2",
                                       column1="res_stations_id", column2="product_product_id",
                                       string="Equipments and Tools", )

    def create_station_tasks(self):
        for rec in self:
            station_tag_id = self.env['project.tags'].search([('name', '=', rec.x_name)]).id
            if not station_tag_id:
                station_tag_id = self.env['project.tags'].create({'name': rec.x_name, 'color': 1, }).id

            for item in rec.x_consumable_ids:
                task = self.env['project.task'].search(
                    [('name', '=', item.name), ('project_id', '=', 51), ('tag_ids', 'ilike', station_tag_id)])
                if not task:
                    vals = {
                        'name': item.name,
                        'stage_id': 215,
                        'user_id': 28,
                        'project_id': 51,
                        'x_user_participants': rec.x_responsible_person_ids,
                        'tag_ids': [station_tag_id],
                    }
                    self.env['project.task'].create(vals)

            for item in rec.x_items_ids:
                task = self.env['project.task'].search(
                    [('name', '=', item.x_name), ('project_id', '=', 51), ('tag_ids', 'ilike', station_tag_id)])
                if not task:
                    vals = {
                        'name': item.x_name,
                        'stage_id': 215,
                        'user_id': 28,
                        'project_id': 51,
                        'x_user_participants': rec.x_responsible_person_ids,
                        'tag_ids': [station_tag_id],
                    }
                    self.env['project.task'].create(vals)

            for item in rec.x_equipment_ids:
                task = self.env['project.task'].search(
                    [('name', '=', item.name), ('project_id', '=', 51), ('tag_ids', 'ilike', station_tag_id)])
                if not task:
                    vals = {
                        'name': item.name,
                        'stage_id': 215,
                        'user_id': 28,
                        'project_id': 51,
                        'x_user_participants': rec.x_responsible_person_ids,
                        'tag_ids': [station_tag_id],
                    }
                    self.env['project.task'].create(vals)

    @api.model
    def create(self, vals):
        res = super(Stations, self).create(vals)
        self.create_station_tasks()
        return res

    def write(self, vals):
        res = super(Stations, self).write(vals)
        self.create_station_tasks()
        return res


class StationItems(models.Model):
    _name = "station.items"
    _description = "Station Items"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True, )


class ProjectGroup(models.Model):
    _name = "project.group"
    _description = "Project Group"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True, )


class BankingInvoiceLines(models.Model):
    _name = "banking.invoice.lines"
    _description = 'Banking Invoice Lines'


class InvoiceLines(models.Model):
    _name = "invoice.lines"
    _description = "Banking Invoice Lines"

    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice ID", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )

    name = fields.Text(string="Description", required=True, widget="section_and_note_text", )

    quantity = fields.Float(string="Quantity", required=False, )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", required=False, )
    unit_price = fields.Float(string="Unit Price", required=False, )
    discount = fields.Float(string="Disc (%)", required=False, )
    tax_ids = fields.Many2many(comodel_name="account.tax", relation="invoice_lines_account_tax_rel",
                               column1="invoice_lines_id", column2="account_tax_id", string="Taxes", )
    currency_id = fields.Many2one(comodel_name="res.currency", string="", required=False,
                                  related="invoice_id.currency_id")
    price_subtotal = fields.Float(string="Subtotal", required=False, )
    display_type = fields.Selection([('line_section', 'Section'), ('line_note', 'Note'), ], default=False,
                                    help="Technical field for UX purpose.")


class SaleTaxInvoiceLines(models.Model):
    _name = "sale.tax.invoice.lines"
    _description = "Sale Tax Invoice Lines"

    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice ID", )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=False,
                                  related='invoice_id.currency_id')
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    name = fields.Text(string="Description", required=False, widget="section_and_note_text", )
    quantity = fields.Float(string="Quantity", required=False, )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", required=False, )
    price_unit = fields.Monetary(string="Unit Price", required=False, )
    discount = fields.Float(string="Disc (%)", required=False, )
    tax_ids = fields.Many2many(comodel_name="account.tax", relation="account_tax_sale_tax_invoice_lines_rel",
                               column1="account_tax_id", column2="sale_tax_invoice_lines_id", string="Taxes", )
    price_subtotal = fields.Monetary(string="Subtotal", required=False, )


class ProductGroup(models.Model):
    _name = "product.group"
    _description = "Product Group"
    _rec_name = "name"

    name = fields.Char(string="Name", required=False, )
    series = fields.Many2one(comodel_name="product.series", string="Series", required=False, )


class ProductSeries(models.Model):
    _name = "product.series"
    _description = "Product Series"
    _rec_name = "display_name"

    display_name = fields.Char(string="Display Name", required=False, store=True, compute="update_display_name")
    name = fields.Char(string="Series Name", required=False, )
    code = fields.Char(string="Series Code", required=False, )
    division = fields.Many2one(comodel_name="product.division", string="Division", required=False, )

    @api.depends('name', 'code')
    def update_display_name(self):
        for record in self:
            if record.code and record.name:
                record.display_name = record.code + " " + record.name


class ProductDivision(models.Model):
    _name = "product.division"
    _description = "Product Division"
    _rec_name = "display_name"

    display_name = fields.Char(string="Display Name", required=False, compute="update_display_name", )
    name = fields.Char(string="Division Name", required=False, )
    code = fields.Char(string="Division Code", required=False, )

    @api.onchange('name', 'code')
    def update_display_name(self):
        for record in self:
            record.display_name = record.code + " " + record.name


class PendingBill(models.Model):
    _name = "pending.bills"
    _description = "Pending Bills"
    _rec_name = "name"

    name = fields.Char(string="Name", required=False, )


class Processes(models.Model):
    _name = "processes"
    _description = "Processes"
    _rec_name = 'x_name'

    x_name = fields.Char(string="Name", required=False, )

    x_models = fields.Many2many(comodel_name="ir.model", relation="x_ir_model_processes_rel", column1="x_processes_id",
                                column2="ir_model_id", string="Models", )
    x_tasks = fields.Many2many(comodel_name="tasks", relation="x_tasks_processes_rel", column1="x_processes_id",
                               column2="x_tasks_id", string="Tasks", )


class Tasks(models.Model):
    _name = "tasks"
    _description = "Tasks"
    _rec_name = 'x_name'
    _order = 'x_sequence'

    x_name = fields.Char(string="Name", required=False, )
    x_task_name = fields.Char(string="Name", required=False, )
    x_start_task_on = fields.Datetime(string="Start task on", required=False, )
    x_has_deadline = fields.Boolean(string="Deadline?", )
    x_deadline = fields.Datetime(string="Deadline", required=False, )
    x_quantity_multiplying_factor = fields.Float(string="Quantity Multiplying Factor", required=False, )
    x_per_unit_time = fields.Float(string="Per Unit Time (Hours)", required=False, )
    x_hours = fields.Float(string="Hours", required=False, )
    x_task_has_time_constraints = fields.Integer(string="Task has time constraints", required=False, )
    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_checklists = fields.Many2many(comodel_name="checklists", relation="x_checklists_task_rel", column1="x_task_id",
                                    column2="x_checklists_id", string="Checklists", )
    x_conditions = fields.Many2many(comodel_name="conditions", relation="x_conditions_task_rel", column1="x_task_id",
                                    column2="x_conditions_id", string="Conditions", )
    x_checklist_items = fields.Many2many(comodel_name="checklist.items", relation="x_checklist_items_task_rel",
                                         column1="x_task_id", column2="x_checklist_items_id",
                                         string="Checklist Items", )
    x_responsible_person = fields.Many2one(comodel_name="hr.employee", string="Responsible person", required=False, )
    x_participants = fields.Many2many(comodel_name="hr.employee", relation="x_hr_employee_task_rel_2",
                                      column1="x_task_id", column2="hr_employee_id", string="Participants", )
    x_observers = fields.Many2many(comodel_name="hr.employee", relation="x_hr_employee_task_rel_1",
                                   column1="x_task_id", column2="hr_employee_id", string="Observers", )
    x_user_responsible = fields.Many2one(comodel_name="res.users", string="Responsible User", required=False, )
    x_user_participants = fields.Many2many(comodel_name="res.users", relation="x_res_users_task_rel_1",
                                           column1="x_task_id", column2="res_users_id", string="Participants", )
    x_user_observers = fields.Many2many(comodel_name="res.users", relation="x_res_users_task_rel_2",
                                        column1="x_task_id", column2="res_users_id", string="Observers", )
    x_project = fields.Selection(selection=[
        ('Sale Order Tracking', 'Sale Order Tracking'),
        ('MO Tracking', 'MO Tracking'),
        ('Purchase Order Tracking', 'Purchase Order Tracking'),
        ('Procurement', 'Procurement'),
        ('Production', 'Production'),
        ('Operations', 'Operations'),
        ('Quality Control', 'Quality Control'),
    ], string="Project", required=False, )
    x_project_id = fields.Many2one(comodel_name="project.project", string="Project", required=True, )
    x_project_stage_id = fields.Many2one(comodel_name="project.task.type", string="Project Stage", required=True,
                                         domain="[('project_ids','ilike',x_project_id)]", )
    x_check = fields.Selection(string="Check", selection=[('All', 'All'), ('Any', 'Any'), ], required=False, )
    x_checklist_items_text = fields.Text(string="Checklist", required=False, )
    x_description = fields.Text(string="Description", required=False, )

    @api.onchange('x_checklists')
    def update_checklist_items(self):
        for record in self:
            for checklist in record.x_checklists:
                for checklist_item in checklist.x_default_checklists:
                    record.x_checklist_items = [(4, checklist_item.id)]

    @api.onchange('x_checklist_items')
    def update_checklist_items_text(self):
        for record in self:
            for checklist in record.x_checklist_items:
                if not record.x_checklist_items_text:
                    record.x_checklist_items_text = '[*]' + checklist.x_name
                else:
                    record.x_checklist_items_text = record.x_checklist_items_text + '\n[*]' + checklist.x_name


class Checklists(models.Model):
    _name = "checklists"
    _description = "Checklists"
    _rec_name = 'x_name'

    x_name = fields.Char(string="Name", required=False, )

    x_default_checklists = fields.Many2many(comodel_name="checklist.items",
                                            relation="checklist_details_checklists_rel_1",
                                            column1="checklists_id",
                                            column2="checklist_items_id",
                                            string="Default Checklists", )

    x_variant_checklists = fields.Many2many(comodel_name="checklist.items",
                                            relation="checklist_details_checklists_rel_2",
                                            column1="checklists_id",
                                            column2="checklist_items_id",
                                            string="Variant Checklists", )


class ChecklistItems(models.Model):
    _name = "checklist.items"
    _description = "Checklist Items"
    _rec_name = 'x_name'

    x_name = fields.Char(string="Description", required=True, )

    x_sequence = fields.Integer(string="Sequence", required=False, )

    x_checklist_group = fields.Many2one(comodel_name="checklists", string="Checklist Group", required=True, )
    x_default_checklist = fields.Many2one(comodel_name="checklist.items", string="Default Checklist", required=False, )

    x_status = fields.Selection(string="Status", selection=[('Default', 'Default'), ('Variant', 'Variant'), ],
                                required=True, )
    x_condition = fields.Selection(string="Condition", selection=[('All', 'All'), ('Any', 'Any'), ], required=False, )

    x_responsible_person = fields.Many2many(comodel_name="hr.employee", relation="hr_employee_checklist_details_rel",
                                            column1="checklist_items_id", column2="hr_employee_id",
                                            string="Responsible person", )

    x_responsible_users = fields.Many2many(comodel_name="res.users", relation="res_users_checklist_items_rel",
                                           required=True,
                                           column1="checklist_items_id", column2="res_users_id",
                                           string="Responsible Users", )
    x_checklist_conditions = fields.Many2many(comodel_name="conditions",
                                              relation="checklist_conditions_checklist_items_rel",
                                              column1="checklist_items_id", column2="checklist_conditions_id",
                                              string="Checklist Conditions", )


class Conditions(models.Model):
    _name = "conditions"
    _description = "Conditions"
    _rec_name = 'x_name'

    x_name = fields.Char(string="Name", required=False, compute='update_name')
    x_model = fields.Many2one(comodel_name="ir.model", string="Model", required=False, )
    x_field_id = fields.Many2one(comodel_name="ir.model.fields", string="Field", domain="[('model_id', '=', x_model)]", )
    x_value = fields.Char(string="Value", required=False, )

    x_relation = fields.Selection(string="Relation",
                                  selection=[
                                      ('equals', 'equals'),
                                      ('not equals', 'not equals'),
                                      ('is set', 'is set'),
                                      ('is not set', 'is not set'),
                                      ('contains', 'contains'),
                                      ('does not contain', 'does not contain'),
                                      ('is greater than', 'is greater than'),
                                      ('is greater than and equal to', 'is greater than and equal to'),
                                      ('is less than', 'is less than'),
                                      ('is less than and equal to', 'is less than and equal to'),
                                  ],
                                  required=False, )

    @api.onchange('x_field_id', 'x_value', 'x_relation')
    def update_name(self):
        for record in self:
            if record.x_field_id and record.x_relation and record.x_value:
                record.x_name = record.x_field_id.field_description + ' ' + record.x_relation + ' ' + record.x_value
            elif record.x_field_id and record.x_relation:
                record.x_name = record.x_field_id.field_description + ' ' + record.x_relation
            else:
                record.x_name = ''


class ShippingPackage(models.Model):
    _name = "shipping.package"
    _description = "Shipping Package"
    _rec_name = "x_package"
    _order = "x_package"

    x_package = fields.Char(string="Package", required=False, )
    x_marking = fields.Char(string="Marking", required=False, )
    x_net_weight = fields.Float(string="Net Weight (kg)", required=False, )
    x_gross_weight = fields.Float(string="Gross Weight (kg)", required=False, )

    x_shipping_box = fields.Many2one(comodel_name="shipping.box", string="Shipping Box", required=False, )
    x_dimension = fields.Char(string="Box Dimension", required=False, related="x_shipping_box.x_dimension", )
    x_description = fields.Char(string="Box Description", required=False, related="x_shipping_box.x_description", )
    x_allowed_weight = fields.Float(string="Box Allowed Weight (kg)", required=False,
                                    related="x_shipping_box.x_allowed_weight", )
    x_quantity_on_hand = fields.Integer(string="Box Quantity on Hand", required=False,
                                        related="x_shipping_box.x_quantity_on_hand", )

    x_picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking ID", required=False, )

class PackingList(models.Model):
    _name = "packing.list"
    _description = "Packing List"
    _rec_name = "x_package"
    _order = "x_package"

    x_picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking ID", required=False, )
    x_package_ids = fields.One2many(comodel_name="shipping.package", inverse_name="x_picking_id", string="Packages",
                                    required=False, related="x_picking_id.x_package_ids")
    x_product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True, )
    x_quantity = fields.Float(string="Quantity", required=False, )
    x_package = fields.Many2one(
        comodel_name="shipping.package", string="Package", required=False, domain="[('id', 'in', x_package_ids)]"
    )


class ShippingBox(models.Model):
    _name = "shipping.box"
    _description = "Shipping Box"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string="Name", required=False, )
    x_description = fields.Char(string="Description", required=False, )
    x_length = fields.Float(string="Length (cm)", required=False, )
    x_allowed_weight = fields.Float(string="Allowed Weight (kg)", required=False, )
    x_width = fields.Float(string="Width (cm)", required=False, )
    x_box_weight = fields.Float(string="Box Weight (kg)", required=False, )
    x_height = fields.Float(string="Height (cm)", required=False, )
    x_quantity_on_hand = fields.Integer(string="Quantity on Hand", required=False, )
    x_dimension = fields.Char(string="Dimension", required=False, )
    x_volumetric_weight = fields.Float(string="Volumetric Weight (kg)", required=False, )
    x_note = fields.Text(string="Note", required=False, )

    @api.onchange('x_length', 'x_width', 'x_height')
    def update_values(self):
        for record in self:
            record.x_volumetric_weight = round(record.x_length * record.x_width * record.x_height / 5000, 2)
            record.x_dimension = str(record.x_length) + ' x ' + str(record.x_width) + ' x ' + str(
                record.x_height) + ' cm'
