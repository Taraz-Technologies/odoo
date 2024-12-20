from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from datetime import date

import datetime
import logging

_logger = logging.getLogger("*__addons_custom__*")


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_default_partner_type(self):
        if self._context.get('res_partner_search_mode') == 'supplier':
            return 'Vendor'
        elif self._context.get('res_partner_search_mode') == 'customer':
            return 'Customer'
        else:
            return 'Vendor'

    x_contact_name = fields.Char(string="Contact Name", required=False, )
    x_company = fields.Char(string="Company", required=False, readonly=False, store=True, compute="_get_company", )
    x_region = fields.Many2one(comodel_name="country.regions", string="Country Region", required=False,
                               compute="compute_region_subregion", store=True, )
    x_subregion = fields.Many2one(comodel_name="country.subregions", string="Country Sub-region", required=False,
                                  compute="compute_region_subregion", store=True, )
    x_quickbooks_name = fields.Char(string="QuickBooks Name", required=False, )

    x_partner_type = fields.Selection(selection=[
        ('Vendor', 'Vendor'),
        ('Customer', 'Customer'),
        ('Employee', 'Employee'),
    ], required=True, string="Partner Type", default=_get_default_partner_type)

    x_distributor = fields.Boolean(string="Is Distributor?", store=True)
    # ---------- Vendor Data ----------
    x_define_vendor_code = fields.Boolean(string="Define Vendor Code", )
    x_vendor_code = fields.Char(string="Vendor Code", required=False, )
    x_vendor_counter = fields.Integer(string="Vendor Counter", required=False, default=1)
    x_vendor_type = fields.Selection(selection=[
        ('Local', 'Local'),
        ('Foreign', 'Foreign'),
    ], required=False, string="Vendor Type", )
    # ---------- Customer Individual Data ----------
    x_mailing_contact_id = fields.Many2one(comodel_name="mailing.contact", string="Mailing Contact", required=False,
                                           compute="add_mailing_contact", store=True, )
    x_exclude_from_newsletter = fields.Boolean(string="Excl. from NEWSLTR", store=True, )
    x_customer_status = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'),
    ], default="Targeted", string="Customer Status", store=True, )
    x_customer_group_id = fields.Many2one(comodel_name="partner.group", string="Customer Department", required=False,
                                          store=True, )
    x_team_member_ids = fields.One2many('res.partner', 'x_team_lead_id', string='Team Members',
                                        domain=[('active', '=', True)])
    x_team_lead_id = fields.Many2one(comodel_name="res.partner", string="Team Lead", required=False, store=True,
                                     index=True,
                                     domain="[('is_company', '=', False),('id', '!=', id),('x_team_lead_id', '=', False)]", )
    x_team_lead_text = fields.Char(string="Team Lead", required=False, readonly=True, default="Team Lead", )
    x_engagement = fields.Selection(string="Engagement",
                                    selection=[('Email', 'Email'), ('Meeting', 'Meeting'), ('Call', 'Call'), ],
                                    required=False, store=True, )

    x_interest_ids = fields.Many2many(comodel_name="partner.interest", relation="partner_interest_res_partner_rel_1",
                                      column1="partner_interest_id", column2="res_partner_id",
                                      string="Area of Interests", store=True, )
    x_interested_product_ids = fields.Many2many(comodel_name="product.group",
                                                relation="product_group_res_partner_rel_1",
                                                column1="product_group_id", column2="res_partner_id",
                                                string="Products Interest", store=True, )
    x_purchased_product_ids = fields.Many2many(comodel_name="product.group", relation="product_group_res_partner_rel_2",
                                               column1="product_group_id", column2="res_partner_id",
                                               string="Purchased Products", readonly=True, )
    x_mailing_list_ids = fields.Many2many(comodel_name="mailing.list", relation="mailing_list_res_partner_rel",
                                          related="x_mailing_contact_id.list_ids",
                                          column1="mailing_list_id", column2="res_partner_id", string="Mailing List",
                                          readonly=True, )
    # ---------- Customer Company Data ----------
    x_company_type = fields.Selection(selection=[
        ('University', 'University'),
        ('Industry', 'Industry'), ], string="Company Type", required=False, )
    x_company_revenue = fields.Float(string="Company Revenue", required=False, )
    x_company_size = fields.Integer(string="Company Size", required=False, )
    x_logo_added = fields.Boolean(string="Logo on Website", )

    x_customer_status_comp = fields.Selection(selection=[
        ('Enquirer', 'Enquirer'),
        ('Customer', 'Customer'),
        ('Targeted', 'Targeted'), ], string="Company Status", related="parent_id.x_customer_status", )
    x_distributor_comp = fields.Boolean(string="Distributor", related="parent_id.x_distributor", )
    x_company_type_comp = fields.Selection(selection=[
        ('University', 'University'),
        ('Industry', 'Industry'), ], string="Company Type", related="parent_id.x_company_type", )
    x_company_revenue_comp = fields.Float(string="Company Revenue", required=False,
                                          related="parent_id.x_company_revenue", )
    x_company_size_comp = fields.Integer(string="Company Size", required=False, related="parent_id.x_company_size", )
    x_total_invoiced_comp = fields.Monetary(string="Total Invoiced", related="parent_id.total_invoiced", )
    x_logo_added_comp = fields.Boolean(string="Logo on Website", related="parent_id.x_logo_added", )
    x_interest_ids_comp = fields.Many2many(comodel_name="partner.interest",
                                           relation="partner_interest_res_partner_rel_2",
                                           column1="partner_interest_id", column2="res_partner_id",
                                           string="Area of Interests",
                                           related="parent_id.x_interest_ids", )
    x_interested_product_ids_comp = fields.Many2many(comodel_name="product.group",
                                                     relation="product_group_res_partner_rel_3",
                                                     column1="product_group_id", column2="res_partner_id",
                                                     string="Products Interest",
                                                     related="parent_id.x_interested_product_ids", )
    x_purchased_product_ids_comp = fields.Many2many(comodel_name="product.group",
                                                    relation="product_group_res_partner_rel_4",
                                                    column1="product_group_id", column2="res_partner_id",
                                                    string="Purchased Products",
                                                    related="parent_id.x_purchased_product_ids", )
    x_update_company_data = fields.Boolean(compute="update_company_area_of_interests")
    # ---------- Testimonials ----------
    x_testimonial_ids = fields.One2many(comodel_name="res.testimonial", inverse_name="x_partner_id",
                                        string="Testimonials", required=False, )
    # ---------- Testimonials ----------
    x_customer_ids = fields.Many2many(comodel_name="res.partner", relation="res_partner_res_partner_rel_00",
                                      column1="res_partner_id_1", column2="res_partner_id_2", string="Customers",
                                      compute="update_related_customers", store=True, )

    @api.model
    def update_contact_data(self):
        contact_ids = self.env['res.partner'].search([('x_partner_type', '=', 'Customer')])
        for contact in contact_ids:
            self.env['sale.order'].update_partner(contact)
            self.env['sale.order'].update_partner(contact.parent_id)

    def unlink(self):
        self.x_mailing_contact_id.unlink()
        return super(Partner, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(Partner, self).create(vals_list)
        self.add_mailing_contact()
        return partners

    @api.depends('x_distributor')
    def update_related_customers(self):
        for rec in self:
            rec.x_customer_ids = [(5, 0, 0)]
            if rec.x_distributor:
                partner_id = rec.id
                sale_order_ids = self.env['sale.order'].search(['|', '|', '|',
                                                                ('partner_id', '=', partner_id),
                                                                ('partner_invoice_id', '=', partner_id),
                                                                ('partner_shipping_id', '=', partner_id),
                                                                ('x_end_user', '=', partner_id),
                                                                ])
                for sale_order in sale_order_ids:
                    if sale_order.partner_id:
                        rec.x_customer_ids = [(4, sale_order.partner_id.id)]
                    if sale_order.partner_invoice_id:
                        rec.x_customer_ids = [(4, sale_order.partner_invoice_id.id)]
                    if sale_order.partner_shipping_id:
                        rec.x_customer_ids = [(4, sale_order.partner_shipping_id.id)]
                    if sale_order.x_end_user:
                        rec.x_customer_ids = [(4, sale_order.x_end_user.id)]

                for child in rec.child_ids:
                    partner_id = child.id
                    sale_order_ids = self.env['sale.order'].search(['|', '|', '|',
                                                                    ('partner_id', '=', partner_id),
                                                                    ('partner_invoice_id', '=', partner_id),
                                                                    ('partner_shipping_id', '=', partner_id),
                                                                    ('x_end_user', '=', partner_id),
                                                                    ])
                    for sale_order in sale_order_ids:
                        if sale_order.partner_id:
                            rec.x_customer_ids = [(4, sale_order.partner_id.id)]
                        if sale_order.partner_invoice_id:
                            rec.x_customer_ids = [(4, sale_order.partner_invoice_id.id)]
                        if sale_order.partner_shipping_id:
                            rec.x_customer_ids = [(4, sale_order.partner_shipping_id.id)]
                        if sale_order.x_end_user:
                            rec.x_customer_ids = [(4, sale_order.x_end_user.id)]

                rec.parent_id.x_distributor = False
                rec.parent_id.x_distributor = True

    @api.depends('x_partner_type')
    def add_mailing_contact(self):
        for rec in self:
            if rec.x_partner_type == 'Customer' and rec._origin.id:
                if not rec.x_mailing_contact_id:
                    mailing_contact_id = self.env['mailing.contact'].search([('x_contact_id', '=', rec._origin.id)])
                    if mailing_contact_id:
                        rec.x_mailing_contact_id = mailing_contact_id.id
                    else:
                        mailing_contact_id = self.env['mailing.contact'].create({'x_contact_id': rec._origin.id})
                        rec.x_mailing_contact_id = mailing_contact_id.id
            elif rec.x_mailing_contact_id:
                rec.x_mailing_contact_id.unlink()

    @api.depends('parent_id')
    def _get_company(self):
        for rec in self:
            if not rec.x_company:
                if rec.parent_id.parent_id:
                    rec.x_company = rec.parent_id.parent_id.name
                elif rec.parent_id:
                    rec.x_company = rec.parent_id.name

    @api.depends('country_id')
    def compute_region_subregion(self):
        for rec in self:
            rec.x_region = rec.country_id.x_region
            rec.x_subregion = rec.country_id.x_subregion

    @api.depends('x_interest_ids', 'x_interested_product_ids')
    def update_company_area_of_interests(self):
        for rec in self:
            if rec.parent_id:
                rec.parent_id.x_interest_ids = rec.parent_id.child_ids.mapped('x_interest_ids').ids
                rec.parent_id.x_interested_product_ids = rec.parent_id.child_ids.mapped('x_interested_product_ids').ids
            rec.x_update_company_data = True
