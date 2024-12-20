"""Example request for extracting GraphQL part data."""
from odoo import fields, models, api
from odoo.exceptions import UserError

import datetime

from odoo.addons_custom.cus_octopart_connector.models.nexarClient import NexarClient

QUERY_MPN = '''
query Search($mpn: String!) {
    supSearchMpn(q: $mpn, limit: 1, inStockOnly: true) {
      results {
        part {
          mpn
          shortDescription
          manufacturer {
            name
          }
          sellers {
            company {
              name
            }
            isAuthorized
            offers {
              clickUrl
              inventoryLevel
              moq
              packaging
              prices {
                price
                quantity
              }
            }
          }
          specs {
            attribute {
              shortname
            }
            value
          }
        }
      }
    }
  }
'''


class OctoPartConnector(models.Model):
    _name = 'octopart.connector'
    _description = 'OctoPart Connector'
    _rec_name = 'x_product_id'

    x_product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    image_128 = fields.Image(related='x_product_id.image_128', string='Image')
    x_mpn = fields.Char(string='MPN', compute='get_part_details', store=True, readonly=False)
    x_description = fields.Char(string='Description', required=False)
    x_manufacturer = fields.Char(string='Manufacturer', required=False)
    x_lifecycle_status = fields.Char(string='Lifecycle Status', required=False)
    x_seller_ids = fields.One2many(comodel_name='part.seller', inverse_name='x_connector_id', string='Part Seller')
    x_data_date = fields.Datetime(string='Data Date', required=False)

    def getLifecycleStatus(self, specs):
        if specs:
            lifecycleSpec = [i for (i) in specs if i.get('attribute', {}).get('shortname') == 'lifecyclestatus']
            if len(lifecycleSpec) > 0:
                return lifecycleSpec[0].get('value', {})
        return ''

    @api.depends('x_product_id')
    def get_part_details(self):
        for rec in self:
            date_now = datetime.datetime.now()
            if rec.x_data_date:
                date_difference = date_now - rec.x_data_date
                if date_difference.days == 0:
                    return

            rec.x_seller_ids = [(2, seller.id) for seller in rec.x_seller_ids]
            clientId = self.env['ir.config_parameter'].sudo().get_param('cus_octopart_connector.client_id')
            clientSecret = self.env['ir.config_parameter'].sudo().get_param('cus_octopart_connector.client_secret')

            nexar = NexarClient(clientId, clientSecret)

            mpn = rec.x_product_id.name

            if not mpn:
                return

            rec.x_data_date = datetime.datetime.now()
            variables = {
                'mpn': mpn
            }
            results = nexar.get_query(QUERY_MPN, variables)
            if results:
                try:
                    seller_ids = []
                    for it in results.get("supSearchMpn", {}).get("results", {}):
                        rec.x_mpn = it.get("part", {}).get("mpn")
                        rec.x_description = it.get("part", {}).get("shortDescription")
                        rec.x_manufacturer = it.get("part", {}).get("manufacturer", {}).get("name")
                        rec.x_lifecycle_status = rec.getLifecycleStatus(it.get("part", {}).get("specs", {}))
                        for seller in it.get("part", {}).get("sellers", {}):
                            for offer in seller.get('offers', {}):
                                for prices in offer.get('prices', {}):
                                    vals = {
                                        'x_name': seller.get('company', {}).get('name'),
                                        'x_click_url': offer.get('clickUrl'),
                                        'x_inventory_level': offer.get('inventoryLevel'),
                                        'x_moq': offer.get('moq'),
                                        'x_packaging': offer.get('packaging'),
                                        'x_quantity': prices.get('quantity'),
                                        'x_price': prices.get('price'),
                                    }
                                    seller_ids.append((0, 0, vals))
                    rec.x_seller_ids = seller_ids
                except:
                    return
            else:
                return


class PartSeller(models.Model):
    _name = 'part.seller'
    _description = 'Part Seller'
    _rec_name = 'display_name'
    _order = 'x_price'

    x_connector_id = fields.Many2one(comodel_name='octopart.connector', string='Connector', required=False)
    x_name = fields.Char(string='Seller Name', required=False)
    x_click_url = fields.Char(string='URL', required=False)
    x_inventory_level = fields.Float(string='Stock', digits=(12, 4))
    x_moq = fields.Float(string='MOQ', digits=(12, 4))
    x_packaging = fields.Char(string='Packaging', required=False)
    x_quantity = fields.Float(string='Quantity', digits=(12, 4))
    x_price = fields.Float(string='Price', required=False, digits=(12, 4))
    x_ext_price = fields.Float(string='Ext Price', compute='_compute_ext_price', store=True, digits=(12, 4))
    x_partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor', compute="_compute_partner", store=True)

    x_vendor_type = fields.Selection(selection=[
        ('preferred', 'Preferred'),
        ('other', 'Other'),
    ], string='Vendor ', default='other', compute="_compute_vendor_type", store=True)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('x_quantity', 'x_price')
    def _compute_ext_price(self):
        for rec in self:
            rec.x_ext_price = rec.x_quantity * rec.x_price

    @api.depends('x_name', 'x_packaging', 'x_price', 'x_inventory_level', 'x_moq')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s | %s | %s | %s | %s" % (
                rec.x_name, rec.x_packaging, round(rec.x_price, 4), round(rec.x_inventory_level, 4), round(rec.x_moq, 4)
            )

    @api.depends('x_name')
    def _compute_partner(self):
        for rec in self:
            rec.x_partner_id = self.env['res.partner'].search([
                # '|',
                # ('x_octopart_name', 'ilike', rec.x_name),
                ('name', 'ilike', rec.x_name),
            ], limit=1).id if rec.x_name else False

    @api.depends('x_partner_id')
    def _compute_vendor_type(self):
        for rec in self:
            if rec.x_partner_id:
                rec.x_vendor_type = 'preferred'
            else:
                rec.x_vendor_type = 'other'


