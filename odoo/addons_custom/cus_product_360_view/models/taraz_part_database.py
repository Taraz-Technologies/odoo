from odoo import _, api, fields, models
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from scipy.stats import norm

import statistics
import datetime
from math import sqrt
import re


class TarazPartNumber(models.Model):
    _name = "taraz.part.number"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Taraz Part Number"
    _rec_name = "x_name"
    _order = "x_name"

    x_name = fields.Char(string='Taraz Part#', readonly=False, compute="_compute_name",
                         store=True, tracking=True, track_visibility='always')
    x_tag_ids = fields.Many2many(comodel_name='custom.tags', string='Tags')
    x_description = fields.Text(string="Description", tracking=True, track_visibility='always')

    x_category = fields.Selection(selection=[('prd', 'PRD'), ('rnd', 'RND')], string='Category',
                                  default='prd', tracking=True, track_visibility='always')
    x_mounting_type = fields.Selection([('smd', 'SMT'), ('th', 'THT'), ('other', 'OTHER')], 'Type',
                                       tracking=True, track_visibility='always')
    x_creation = fields.Selection(selection=[('auto', 'Auto'), ('manual', 'Manual')], string='Creation',
                                  tracking=True, track_visibility='always', readonly=True, default='manual')

    x_order_quantity = fields.Float(string='Reorder Quantity', required=False, tracking=True,
                                    track_visibility='always', digits="Product Unit of Measure")

    x_virtual_available = fields.Float(string='Forecasted', required=False,  tracking=True,
                                       track_visibility='always', digits="Product Unit of Measure", )
    x_backorder_qty = fields.Float(string='Backorder', required=False, tracking=True,
                                   track_visibility='always', digits="Product Unit of Measure", )
    x_qty_available = fields.Float(string='Actual Forecasted', required=False, tracking=True,
                                   track_visibility='always', digits="Product Unit of Measure",
                                   help="Forecasted quantity without backorder quantity")

    x_tz_qty_available = fields.Float(string='On Hand', compute="_compute_tz_quantities", store=True,)
    x_tz_to_consume_qty = fields.Float(string='To Consume', compute="_compute_tz_quantities", store=True,)
    x_tz_tray_out_qty = fields.Float(string='Tray Out', compute="_compute_tz_quantities", store=True,)
    x_tz_available_qty = fields.Float(string='Available', compute="_compute_tz_quantities", store=True,)
    x_tz_incoming_qty = fields.Float(string='Incoming', compute="_compute_tz_quantities", store=True,)
    x_tz_backorder_qty = fields.Float(string='Backorder', compute="_compute_tz_quantities", store=True,)
    x_tz_outgoing_qty = fields.Float(string='Reserved', compute="_compute_tz_quantities", store=True,)
    x_tz_virtual_available = fields.Float(string='Forecasted', compute="_compute_tz_quantities", store=True,)

    @api.depends(
        'x_alternate_ids.x_product_id.qty_available', 'x_alternate_ids.x_product_id.x_to_consume_qty',
        'x_alternate_ids.x_product_id.x_tray_out_qty', 'x_alternate_ids.x_product_id.x_available_qty',
        'x_alternate_ids.x_product_id.x_incoming_qty', 'x_alternate_ids.x_product_id.x_backorder_qty',
        'x_alternate_ids.x_product_id.virtual_available', 'x_alternate_ids.x_product_id.outgoing_qty',
    )
    def _compute_tz_quantities(self):
        for rec in self:
            rec.x_tz_qty_available = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('qty_available'))
            rec.x_tz_to_consume_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('x_to_consume_qty'))
            rec.x_tz_tray_out_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('x_tray_out_qty'))
            rec.x_tz_available_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('x_available_qty'))
            rec.x_tz_incoming_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('x_incoming_qty'))
            rec.x_tz_backorder_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('x_backorder_qty'))
            rec.x_tz_outgoing_qty = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('outgoing_qty'))
            rec.x_tz_virtual_available = sum(rec.x_alternate_ids.mapped('x_product_id').mapped('virtual_available'))

    x_total_purchased = fields.Float(string='Total Purchased', digits="Product Unit of Measure",
                                     compute="_compute_stat_values", store=True)
    x_total_manufactured = fields.Float(string='Total Manufactured', digits="Product Unit of Measure",
                                        compute="_compute_stat_values", store=True)
    x_total_consumed = fields.Float(string='Total Consumed', digits="Product Unit of Measure",
                                    compute="_compute_stat_values", store=True)
    x_total_sold = fields.Float(string='Total Sold', digits="Product Unit of Measure",
                                compute="_compute_stat_values", store=True)

    x_start_date = fields.Date(string='Start Date', required=False)
    x_end_date = fields.Date(string='End Date', required=False)

    x_period_purchased = fields.Float(string='Purchased in Period', digits="Product Unit of Measure",
                                      compute="_compute_stat_values", store=True)
    x_period_manufactured = fields.Float(string='Manufactured in Period', digits="Product Unit of Measure",
                                         compute="_compute_stat_values", store=True)
    x_period_consumed = fields.Float(string='Consumed in Period', digits="Product Unit of Measure",
                                     compute="_compute_stat_values", store=True)
    x_period_sold = fields.Float(string='Sold in Period', digits="Product Unit of Measure",
                                 compute="_compute_stat_values", store=True)

    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', default=1,
                               tracking=True, track_visibility='always')

    x_inventory_turnover = fields.Float(string='Inventory Turnover', digits="Product Unit of Measure",
                                        compute="_compute_stat_values", store=True)

    x_alternate_ids = fields.One2many('taraz.part.alternates', 'x_taraz_part_number_id', string='Alternates')
    x_compromised_ids = fields.One2many('taraz.part.compromised', 'x_taraz_part_number_id', string='Compromised')

    x_usage_ids = fields.One2many('mass.component.usage', 'x_taraz_part_id', string='Mass Usage', required=False)

    x_safety_stock = fields.Float(string='Safety Stock', digits="Product Unit of Measure")
    x_reorder_point = fields.Float(string='Reorder Point', digits="Product Unit of Measure")

    x_product_purchase_packaging_id = fields.Many2one(
        related='x_alternate_ids.x_product_id.x_product_purchase_packaging_id',
        string='Purchase Packaging',
        store=True)
    x_roq = fields.Float(
        related='x_product_purchase_packaging_id.x_roq',
        string='Bulk Reorder Quantity')
    x_quantity_buffer = fields.Float(
        related='x_product_purchase_packaging_id.x_quantity_buffer',
        string='Reel Loading Buffer')
    x_enable_safety_stock = fields.Boolean(
        string='Enable Safety Stock',
        required=False,
        tracking=True)
    x_consider_compromised = fields.Boolean(
        string='For SS Consider Compromised',
        required=False,
        tracking=True)
    x_safety_stock_calculated = fields.Boolean(
        string='Safety Stock Calculated',
        required=False,
        tracking=True)

    x_average_demand = fields.Boolean(
        string='Delete Field',
        required=False)

    def compute_safety_stock(self):
        for rec in self:
            rec.x_virtual_available = sum(rec.x_alternate_ids.mapped('x_virtual_available'))
            rec.x_backorder_qty = sum(rec.x_alternate_ids.mapped('x_backorder_qty'))

            if rec.x_consider_compromised:
                rec.x_virtual_available += sum(rec.x_compromised_ids.mapped('x_compromised_id').mapped(
                    'x_alternate_ids').mapped('x_virtual_available'))
                rec.x_backorder_qty += sum(rec.x_compromised_ids.mapped('x_compromised_id').mapped(
                    'x_alternate_ids').mapped('x_backorder_qty'))
            rec.x_qty_available = rec.x_virtual_available - rec.x_backorder_qty

            if not rec.x_enable_safety_stock:
                rec.x_safety_stock = 0
                rec.x_reorder_point = 0
                rec.x_safety_stock_calculated = False
                return

            product_ids = rec.x_alternate_ids.mapped('x_product_id').mapped('product_variant_id').ids
            if rec.x_consider_compromised:
                product_ids += rec.x_compromised_ids.mapped('x_compromised_id').mapped('x_alternate_ids').mapped(
                    'x_product_id').mapped('product_variant_id').ids

            stock_valuation_layer = self.env['stock.valuation.layer']
            consumption_history = stock_valuation_layer.read_group(
                domain=[('quantity', '<', 0), ('product_id', 'in', product_ids), ],
                fields=['create_date', 'quantity',],
                groupby=['create_date'],
                lazy=False
            )
            calculated_with = self.env['ir.config_parameter'].sudo().get_param('stock.x_calculated_with')
            # fill missing months in consumption history
            if consumption_history and calculated_with != 'consumption_months':
                # convert consumption history 'create_date' to datetime
                for line in consumption_history:
                    line['create_date'] = datetime.datetime.strptime(line['create_date'],  "%B %Y").date()
                # fill missing months in consumption history
                first_month = consumption_history[0]['create_date']
                last_month = fields.Date.today()
                while first_month < last_month:
                    if first_month not in [line['create_date'] for line in consumption_history]:
                        consumption_history.append({
                            'create_date': first_month, 'quantity': 0,
                        })
                    first_month += relativedelta(months=1)
                # get last twelve months from consumption history
                if calculated_with == 'twelve_months':
                    # sort consumption history by 'create_date'
                    consumption_history = sorted(consumption_history, key=lambda k: k['create_date'])
                    # get last twelve months from consumption history
                    consumption_history = consumption_history[-12:]

            if len(consumption_history) < 2:
                rec.x_safety_stock = 0
                rec.x_reorder_point = 0
                rec.x_safety_stock_calculated = False
                return

            demand_details = []
            for line in consumption_history:
                demand_details.append(- line['quantity'])

            if demand_details:
                average_demand = sum(demand_details) / len(demand_details)
            else:
                rec.x_safety_stock = 0
                rec.x_reorder_point = 0
                rec.x_safety_stock_calculated = False
                return

            target_rate = float(self.env['ir.config_parameter'].sudo().get_param('stock.x_target_rate'))
            average_lead_time = float(self.env['ir.config_parameter'].sudo().get_param('stock.x_average_lead_time'))
            coefficient = norm.ppf(target_rate)
            standard_deviation = statistics.stdev(demand_details)

            safety_stock = round(coefficient * standard_deviation * sqrt(average_lead_time) + rec.x_quantity_buffer, 0)
            reorder_point = round(average_demand * average_lead_time + safety_stock, 0)

            rec.x_safety_stock = safety_stock
            rec.x_reorder_point = reorder_point
            rec.x_safety_stock_calculated = True

    def merge_taraz_part(self):
        action = self.env.ref('cus_product_360_view.action_merge_taraz_parts').read()[0]
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

    def action_view_stock_status(self):
        action = self.env.ref('stock.product_template_action_product').read()[0]
        alt_product_ids = self.x_alternate_ids.mapped('x_product_id')
        for product in alt_product_ids:
            product.x_tzp_type = 'alternates'
        comp_product_ids = []
        for compromise in self.x_compromised_ids:
            for product in compromise.x_compromised_id.x_alternate_ids.mapped('x_product_id'):
                product.x_tzp_type = 'compromised'
            comp_product_ids += compromise.x_compromised_id.x_alternate_ids.mapped('x_product_id').ids
        product_ids = alt_product_ids.ids + comp_product_ids
        action['domain'] = [('id', 'in', product_ids)]
        action['context'] = {'search_default_tzp_type': 1}
        return action

    def action_view_purchase_history(self):
        action = self.env.ref('cus_product_360_view.action_purchase_history').read()[0]

        alt_product_ids = self.x_alternate_ids.mapped('x_product_id').ids
        comp_product_ids = []
        for compromise in self.x_compromised_ids:
            comp_product_ids += compromise.x_compromised_id.x_alternate_ids.mapped('x_product_id').ids
        product_ids = alt_product_ids + comp_product_ids

        history_ids = self.env['purchase.history'].search([('x_product_id', 'in', alt_product_ids)])
        for history in history_ids:
            history.x_tzp_type = 'alternates'
        history_ids = self.env['purchase.history'].search([('x_product_id', 'in', comp_product_ids)])
        for history in history_ids:
            history.x_tzp_type = 'compromised'

        action['domain'] = [('x_product_id', 'in', product_ids)]
        action['context'] = {'search_default_product_id': 1, 'search_default_tzp_type': 1}
        return action

    def action_view_manufacturing_history(self):
        action = self.env.ref('cus_product_360_view.action_manufacturing_history').read()[0]

        alt_product_ids = self.x_alternate_ids.mapped('x_product_id').ids
        comp_product_ids = []
        for compromise in self.x_compromised_ids:
            comp_product_ids += compromise.x_compromised_id.x_alternate_ids.mapped('x_product_id').ids
        product_ids = alt_product_ids + comp_product_ids

        history_ids = self.env['manufacturing.history'].search([('x_component_id', 'in', alt_product_ids)])
        for history in history_ids:
            history.x_tzp_type = 'alternates'
        history_ids = self.env['manufacturing.history'].search([('x_component_id', 'in', comp_product_ids)])
        for history in history_ids:
            history.x_tzp_type = 'compromised'

        action['domain'] = [('x_component_id', 'in', product_ids)]
        action['context'] = {'search_default_component_id': 1, 'search_default_type': 1, 'search_default_tzp_type': 1}
        return action

    def action_view_bom_tool_usage(self):
        action = self.env.ref('cus_bom_tool.action_view_bom_tool').read()[0]
        base_bom_ids = self.env['bom.tool'].search([]).mapped('x_base_bom_id').mapped('x_bom_line_ids').filtered(
            lambda l: l.x_taraz_part_id.id == self.id
        ).mapped('x_base_bom_id')
        bom_tool_ids = self.env['bom.tool'].search([('x_base_bom_id', 'in', base_bom_ids.ids)])
        action['domain'] = [('id', 'in', bom_tool_ids.ids)]
        return action

    def alternate_mass_usage_editing(self):
        for rec in self:
            if not rec.x_alternate_ids:
                raise UserError("Alternates doesn't exist!")

            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')
            line_ids = rec.x_alternate_ids[0].x_product_usage_ids.filtered(
                lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id).mapped('x_base_bom_line_id')

            for line in line_ids:
                if line.id not in usage_ids.mapped('x_base_bom_line_id').ids:
                    rec.x_usage_ids = [(0, 0, {'x_base_bom_line_id': line.id, 'x_usage_type': 'alternate'})]

            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')
            usage_ids.filtered(lambda l: l.x_base_bom_line_id.id not in line_ids.ids).unlink()

        action = self.env.ref('cus_product_360_view.action_alternate_mass_usage_editing').read()[0]
        return action

    def compromised_mass_usage_editing(self):
        for rec in self:
            if not rec.x_compromised_ids:
                raise UserError("Compromised doesn't exist!")

            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'compromised')
            line_ids = rec.x_compromised_ids[0].x_product_usage_ids.filtered(
                lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id).mapped('x_base_bom_line_id')

            for line in line_ids:
                if line.id not in usage_ids.mapped('x_base_bom_line_id').ids:
                    rec.x_usage_ids = [(0, 0, {'x_base_bom_line_id': line.id, 'x_usage_type': 'compromised'})]

            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'compromised')
            usage_ids.filtered(lambda l: l.x_base_bom_line_id.id not in line_ids.ids).unlink()

        action = self.env.ref('cus_product_360_view.action_compromised_mass_usage_editing').read()[0]
        return action

    @api.depends('x_alternate_ids', 'x_start_date', 'x_end_date')
    def _compute_stat_values(self):
        for rec in self:
            total_purchased = 0
            total_manufactured = 0
            total_consumed = 0
            total_sold = 0

            period_purchased = 0
            period_manufactured = 0
            period_consumed = 0
            period_sold = 0

            a_inventory = 0
            cogs = 0
            for alternate in rec.x_alternate_ids:

                stat_values = alternate.x_product_id.compute_stat_values(rec.x_start_date, rec.x_end_date)

                if stat_values:
                    period_purchased += stat_values[0]
                    period_manufactured += stat_values[1]
                    period_consumed += stat_values[2]
                    period_sold += stat_values[3]

                    a_inventory += stat_values[5]
                    cogs += stat_values[6]

                    total_purchased += stat_values[7]
                    total_manufactured += stat_values[8]
                    total_consumed += stat_values[9]
                    total_sold += stat_values[10]

            rec.x_total_purchased = total_purchased
            rec.x_total_manufactured = total_manufactured
            rec.x_total_consumed = total_consumed
            rec.x_total_sold = total_sold

            rec.x_period_purchased = period_purchased
            rec.x_period_manufactured = period_manufactured
            rec.x_period_consumed = period_consumed
            rec.x_period_sold = period_sold

            rec.x_inventory_turnover = round(cogs / a_inventory, 2) if a_inventory != 0 else 0

    def write(self, vals):
        res = super(TarazPartNumber, self).write(vals)
        if vals.get('x_name'):
            self._compute_alternates()
            self._compute_compromised()
        return res

    def _compute_alternates(self):
        for rec in self:
            alternate_product_ids = rec.x_alternate_ids.mapped('x_product_id')
            product_ids = self.env['product.template'].search([('x_taraz_part_number_id', '=', rec._origin.id)])
            for product_id in product_ids:
                if product_id.id not in alternate_product_ids.ids:
                    alternate_id = self.env['taraz.part.alternates'].search([('x_product_id', '=', product_id.id)])
                    if alternate_id:
                        alternate_id.x_taraz_part_number_id = rec._origin.id
                    else:
                        alternate_id = self.env['taraz.part.alternates'].create({
                            'x_taraz_part_number_id': rec._origin.id,
                            'x_product_id': product_id.id,
                            'x_creation': 'auto',
                        })
                    if rec.x_alternate_ids:
                        usage_ids = rec.x_alternate_ids[0].x_product_usage_ids
                        for line in usage_ids:
                            usage = rec.x_usage_ids.filtered(
                                lambda
                                    l: l.x_base_bom_line_id == line.x_base_bom_line_id and l.x_usage_type == 'alternate')
                            line.copy({
                                'x_alternate_id': alternate_id.id, 'x_usage': usage.x_usage, 'x_mass_editing': 'enabled'
                            })
                            line.x_base_bom_line_id.x_to_be_reviewed = True
                            if line.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                                line.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'

    def _compute_compromised(self):
        for rec in self:
            if rec.compute_taraz_part_number(rec.x_description):
                if rec.x_name[:3] == 'TZR':
                    desc_list = rec.x_description.upper().split()
                    package = self.get_package(desc_list)
                    value = self.get_res_value(desc_list)
                    tolerance = self.get_res_tolerance(desc_list)
                    tolerance = float(tolerance[:-1]) if tolerance else 0
                    power = self.get_res_power(desc_list)
                    try:
                        power = float(power[:-1]) if power else 100
                    except ValueError:
                        power = float(power[:-2]) * 1000 if 'kW' in power else 100
                    compromised_ids = rec.x_compromised_ids.mapped('x_compromised_id')
                    taraz_part_number_ids = self.env['taraz.part.number'].search([
                        ('x_name', 'ilike', 'TZR'), ('id', '!=', rec._origin.id)])
                    for taraz_part_number in taraz_part_number_ids:
                        tzp_compromised_ids = taraz_part_number.x_compromised_ids.mapped('x_compromised_id')
                        tzp_desc_list = taraz_part_number.x_description.upper().split() if taraz_part_number.x_description else []
                        tzp_package = self.get_package(tzp_desc_list)
                        tzp_value = self.get_res_value(tzp_desc_list)
                        tzp_tolerance = self.get_res_tolerance(tzp_desc_list)
                        tzp_tolerance = float(tzp_tolerance[:-1]) if tzp_tolerance else 100
                        tzp_power = self.get_res_power(tzp_desc_list)
                        try:
                            tzp_power = float(tzp_power[:-1]) if tzp_power else 100
                        except ValueError:
                            tzp_power = float(tzp_power[:-2]) * 1000 if 'kW' in tzp_power else 100
                        if value == tzp_value and package == tzp_package \
                                and tolerance >= tzp_tolerance and power <= tzp_power \
                                and taraz_part_number not in compromised_ids:
                            compromised_id = self.env['taraz.part.compromised'].create({
                                'x_taraz_part_number_id': rec._origin.id,
                                'x_compromised_id': taraz_part_number.id,
                                'x_creation': 'auto',
                            })
                            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'compromised')
                            if not usage_ids:
                                usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')
                            for line in usage_ids:
                                line_id = self.env['component.usage'].create({
                                    'x_compromised_id': compromised_id.id,
                                    'x_base_bom_line_id': line.x_base_bom_line_id.id,
                                    'x_usage': line.x_usage,
                                    'x_mass_editing': 'enabled'
                                })
                                line_id.x_base_bom_line_id.x_to_be_reviewed = True
                                if line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                                    line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'
                        elif value == tzp_value and package == tzp_package \
                                and tolerance <= tzp_tolerance and power >= tzp_power \
                                and rec._origin.id not in tzp_compromised_ids.ids:
                            compromised_id = self.env['taraz.part.compromised'].create({
                                'x_taraz_part_number_id': taraz_part_number.id,
                                'x_compromised_id': rec._origin.id,
                                'x_creation': 'auto',
                            })
                            usage_ids = taraz_part_number.x_usage_ids.filtered(
                                lambda l: l.x_usage_type == 'compromised')
                            if not usage_ids:
                                usage_ids = taraz_part_number.x_usage_ids.filtered(
                                    lambda l: l.x_usage_type == 'alternate')
                            for line in usage_ids:
                                line_id = self.env['component.usage'].create({
                                    'x_compromised_id': compromised_id.id,
                                    'x_base_bom_line_id': line.x_base_bom_line_id.id,
                                    'x_usage': line.x_usage,
                                    'x_mass_editing': 'enabled'
                                })
                                line_id.x_base_bom_line_id.x_to_be_reviewed = True
                                if line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                                    line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'
                elif rec.x_name[:4] == 'TZCC':
                    desc_list = rec.x_description.upper().split()
                    package = self.get_package(desc_list)
                    value = self.get_cap_value(desc_list)
                    tolerance = self.get_cap_tolerance(desc_list)
                    tolerance = float(tolerance[:-1]) if tolerance else 0
                    voltage = self.get_cap_voltage(desc_list)
                    try:
                        voltage = float(voltage[:-1]) if voltage else 100
                    except ValueError:
                        voltage = float(voltage[:-2]) * 1000 if 'kV' in voltage else 100
                    compromised_ids = rec.x_compromised_ids.mapped('x_compromised_id')
                    taraz_part_number_ids = self.env['taraz.part.number'].search([
                        ('x_name', 'ilike', 'TZCC'), ('id', '!=', rec._origin.id)])
                    for taraz_part_number in taraz_part_number_ids:
                        tzp_compromised_ids = taraz_part_number.x_compromised_ids.mapped('x_compromised_id')
                        tzp_desc_list = taraz_part_number.x_description.upper().split() if taraz_part_number.x_description else []
                        tzp_package = self.get_package(tzp_desc_list)
                        tzp_value = self.get_cap_value(tzp_desc_list)
                        tzp_voltage = self.get_cap_voltage(tzp_desc_list)
                        try:
                            tzp_voltage = float(tzp_voltage[:-1]) if tzp_voltage else 0
                        except ValueError:
                            tzp_voltage = float(tzp_voltage[:-2]) * 1000 if 'kV' in tzp_voltage else 0
                        tzp_tolerance = self.get_cap_tolerance(tzp_desc_list)
                        tzp_tolerance = float(tzp_tolerance[:-1]) if tzp_tolerance else 100
                        if value == tzp_value and package == tzp_package \
                                and tolerance >= tzp_tolerance and voltage <= tzp_voltage \
                                and taraz_part_number not in compromised_ids:
                            compromised_id = self.env['taraz.part.compromised'].create({
                                'x_taraz_part_number_id': rec._origin.id,
                                'x_compromised_id': taraz_part_number.id,
                                'x_creation': 'auto',
                            })
                            usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'compromised')
                            if not usage_ids:
                                usage_ids = rec.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')
                            for line in usage_ids:
                                line_id = self.env['component.usage'].create({
                                    'x_compromised_id': compromised_id.id,
                                    'x_base_bom_line_id': line.x_base_bom_line_id.id,
                                    'x_usage': line.x_usage,
                                    'x_mass_editing': 'enabled'
                                })
                                line_id.x_base_bom_line_id.x_to_be_reviewed = True
                                if line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                                    line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'
                        elif value == tzp_value and package == tzp_package \
                                and tolerance <= tzp_tolerance and voltage >= tzp_voltage \
                                and rec._origin.id not in tzp_compromised_ids.ids:
                            compromised_id = self.env['taraz.part.compromised'].create({
                                'x_taraz_part_number_id': taraz_part_number.id,
                                'x_compromised_id': rec._origin.id,
                                'x_creation': 'auto',
                            })
                            usage_ids = taraz_part_number.x_usage_ids.filtered(
                                lambda l: l.x_usage_type == 'compromised')
                            if not usage_ids:
                                usage_ids = taraz_part_number.x_usage_ids.filtered(
                                    lambda l: l.x_usage_type == 'alternate')
                            for line in usage_ids:
                                line_id = self.env['component.usage'].create({
                                    'x_compromised_id': compromised_id.id,
                                    'x_base_bom_line_id': line.x_base_bom_line_id.id,
                                    'x_usage': line.x_usage,
                                    'x_mass_editing': 'enabled'
                                })
                                line_id.x_base_bom_line_id.x_to_be_reviewed = True
                                if line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                                    line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'

    @api.depends('x_description')
    def _compute_name(self):
        for rec in self:
            description = rec.x_description.upper() if rec.x_description else ''
            if rec.compute_taraz_part_number(description):
                rec.x_name = rec.compute_taraz_part_number(description)
                rec.x_mounting_type = 'smd' if self.get_package(description.split()) else False
                rec.x_creation = 'auto'
            else:
                rec_id = '0000%s' % rec.id
                rec_id = rec_id[-5:]
                rec.x_name = 'TZP%s' % rec_id

    def compute_taraz_part_number(self, desc):
        if desc == '' or not desc:
            return False
        desc_list = desc.upper().split()
        package = self.get_package(desc_list)

        taraz_part_number = False
        if package and [s for s in desc_list if any(x == s for x in ['CAP', 'CER', 'Ceramic', 'Capacitors', 'TZCC'])]:
            taraz_part_number = 'TZCC'
            # Value
            taraz_part_number += self.get_cap_value(desc_list) if self.get_cap_value(desc_list) else ''
            # Voltage
            taraz_part_number += self.get_cap_voltage(desc_list) if self.get_cap_voltage(desc_list) else ''
            # Tolerance
            taraz_part_number += self.get_cap_tolerance(desc_list) if self.get_cap_tolerance(desc_list) else ''
            # Dielectric
            taraz_part_number += self.get_cap_dielectric(desc_list) if self.get_cap_dielectric(desc_list) else ''
            # Package
            taraz_part_number += self.get_package(desc_list) if self.get_package(desc_list) else ''
        elif package and [s for s in desc_list if any(x == s for x in ['OHM', 'RES', 'TZR', 'MELF'])]:
            taraz_part_number = 'TZR'
            # Value
            taraz_part_number += self.get_res_value(desc_list) if self.get_res_value(desc_list) else ''
            # Tolerance
            taraz_part_number += self.get_res_tolerance(desc_list) if self.get_res_tolerance(desc_list) else ''
            # Power
            taraz_part_number += self.get_res_power(desc_list) if self.get_res_power(desc_list) else ''
            # Package
            taraz_part_number += self.get_package(desc_list) if self.get_package(desc_list) else ''

        return taraz_part_number

    def get_package(self, desc_list):
        packages = ['0201', '0204', '0207', '0306', '0402', '0508', '0603', '0805', '0816',
                    '1206', '1210', '1812', '2010', '2220', '2412', '2512', '2917', '4320']
        package = set(desc_list).intersection(packages)
        return next(iter(set(desc_list).intersection(packages))) if package else False

    def get_res_value(self, desc_list):
        resistance = False
        if [s for s in desc_list if any(x == s[:-1] for x in ['K', 'M'])]:
            resistance = [s for s in desc_list if any(x == s[:-1] for x in ['K', 'M'])][0]
        else:
            value = desc_list[desc_list.index('OHM') - 1] if 'OHM' in desc_list else ''
            resistance = value if any(x in value for x in ['K', 'M']) else value + 'R'
        return resistance

    def get_res_tolerance(self, desc_list):
        tolerance = False
        if [s for s in desc_list if "%" in s]:
            value = [s for s in desc_list if "%" in s]
            tolerance = value[0] if len(value[0]) < 10 else value[1] if len(value) > 1 else False
        return tolerance

    def get_res_power(self, desc_list):
        power = False
        if [s for s in desc_list if all(x in s for x in ['W', '/']) and any(char.isdigit() for char in s)]:
            power = [s for s in desc_list if all(x in s for x in ['W', '/'])][0].replace('W', '').split('/')
            power1 = round(float(power[0]) / float(power[1]))
            power2 = round(float(power[0]) / float(power[1]), 2)
            power = str(power1) + 'W' if power1 == power2 else str(power2) + 'W'
        elif [s for s in desc_list if "W" in s]:
            value = [s for s in desc_list if "W" in s]
            power = value[0] if len(value[0]) < 10 else value[1] if len(value) > 1 else False
        return power

    def get_cap_value(self, desc_list):
        capacitance = False
        if [s for s in desc_list
            if any(x in s for x in ['PF', 'NF', 'UF'])
               and all(x not in s for x in ['+/-', '±'])]:
            value = [s for s in desc_list
                     if any(x in s for x in ['PF', 'NF', 'UF'])
                     and all(x not in s for x in ['+/-', '±'])]
            if 10 > len(value[0]) > 5 and '.' not in value[0]:
                capacitance1 = round(int(value[0][:-2]) / 1000)
                capacitance2 = round(int(value[0][:-2]) / 1000, 3)
                capacitance = capacitance1 if capacitance1 == capacitance2 else capacitance2
                value[0] = '%sNF' % capacitance if value[0][-2:] == 'PF' else '%sUF' % capacitance
            elif 10 > len(value[0]) > 4 and '0.' in value[0] and value[0][-2:] == 'UF':
                capacitance1 = round(float(value[0][:-2]) * 1000)
                capacitance2 = round(float(value[0][:-2]) * 1000, 3)
                capacitance = capacitance1 if capacitance1 == capacitance2 else capacitance2
                value[0] = '%sNF' % capacitance
            elif len(value) > 1:
                if 10 > len(value[1]) > 5 and '.' not in value[1]:
                    capacitance1 = round(int(value[1][:-2]) / 1000)
                    capacitance2 = round(int(value[1][:-2]) / 1000, 3)
                    capacitance = capacitance1 if capacitance1 == capacitance2 else capacitance2
                    value[1] = '%sNF' % capacitance if value[1][-2:] == 'PF' else '%sUF' % capacitance
                elif 10 > len(value[1]) > 4 and '0.' in value[1] and value[1][-2:] == 'UF':
                    capacitance1 = round(float(value[1][:-2]) * 1000)
                    capacitance2 = round(float(value[1][:-2]) * 1000, 3)
                    capacitance = capacitance1 if capacitance1 == capacitance2 else capacitance2
                    value[1] = '%sNF' % capacitance
            capacitance = value[0] if len(value[0]) < 10 else value[1] if len(value) > 1 else ''
        return capacitance

    def get_cap_voltage(self, desc_list):
        voltage = False
        if [s for s in desc_list if "V" in s]:
            value = [s for s in desc_list if "V" in s]
            voltage = value[0] if len(value[0]) < 10 else value[1] if len(value) > 1 else ''
        return voltage

    def get_cap_tolerance(self, desc_list):
        tolerance = False
        capacitance = self.get_cap_value(desc_list)
        if [s for s in desc_list if "%" in s]:
            value = [s for s in desc_list if "%" in s]
            tolerance = value[0] if len(value[0]) < 10 else value[1] if len(value) > 1 else ''
            tolerance = tolerance.replace('±', '').replace('+/-', '')
        elif [s for s in desc_list if any(x in s for x in ['+/-', '±'])] and capacitance:
            tolerance = [s for s in desc_list if any(x in s for x in ['+/-', '±'])][0]
            tolerance = tolerance.replace('±', '').replace('+/-', '')
            if capacitance[-2:] == tolerance[-2:]:
                capacitance = float(capacitance.replace(capacitance[-2:], ''))
            elif capacitance[-2:] == 'NF' and tolerance[-2:] == 'PF':
                capacitance = float(capacitance.replace(capacitance[-2:], '')) * 1000
            elif capacitance[-2:] == 'UF' and tolerance[-2:] == 'PF':
                capacitance = float(capacitance.replace(capacitance[-2:], '')) * 1000000
            tolerance = float(tolerance.replace(tolerance[-2:], ''))
            tolerance1 = round(tolerance / capacitance * 100)
            tolerance2 = round(tolerance / capacitance * 100, 1)
            tolerance = str(tolerance1) + '%' if tolerance1 == tolerance2 else str(tolerance2) + '%'
        return tolerance

    def get_cap_dielectric(self, desc_list):
        dielectric = False
        dielectrics = ['X5R', 'X5S', 'X5T', 'X6R', 'X6S', 'X6T', 'X7R', 'X7S',
                       'X7T', 'X8G', 'X8L', 'X8R', 'X8S', 'X8T', 'Y5V', 'Z5U']
        dielectric = set(desc_list).intersection(dielectrics)
        dielectric = next(iter(set(desc_list).intersection(dielectrics))) if dielectric else False
        dielectrics = ['NPO', 'NP0', 'C0G', 'C0G/NP0', 'C0G/NPO', 'NP0/C0G', 'NPO/C0G']
        dielectric = 'C0G' if set(desc_list).intersection(dielectrics) else dielectric
        return dielectric

    def unlink(self):
        self.x_alternate_ids.unlink()
        self.x_compromised_ids.unlink()
        self.x_usage_ids.unlink()
        return super(TarazPartNumber, self).unlink()


class TarazPartAlternates(models.Model):
    _name = "taraz.part.alternates"
    _inherit = ['mail.activity.mixin']
    _description = "Taraz Part Alternates"
    _rec_name = "x_product_id"
    _order = "x_product_id"

    x_taraz_part_number_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part#', required=False)
    x_product_id = fields.Many2one(comodel_name='product.template', string='Part Number', required=False)
    x_description = fields.Text(string="Description", required=False, related="x_product_id.description")

    x_qty_available = fields.Float(string='On Hand', required=False, related="x_product_id.qty_available")
    x_to_consume_qty = fields.Float(string='To Consume', required=False, related="x_product_id.x_to_consume_qty")
    x_tray_out_qty = fields.Float(string='Tray Out', required=False, related="x_product_id.x_tray_out_qty")
    x_available_qty = fields.Float(string='Available', required=False, related="x_product_id.x_available_qty")
    x_incoming_qty = fields.Float(string='Incoming', required=False, related="x_product_id.x_incoming_qty")
    x_backorder_qty = fields.Float(string='Backorder', required=False, related="x_product_id.x_backorder_qty")
    x_outgoing_qty = fields.Float(string='Reserved', required=False, related="x_product_id.outgoing_qty")
    x_virtual_available = fields.Float(string='Forecasted', required=False, related="x_product_id.virtual_available")

    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', related="x_product_id.uom_id")
    x_creation = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')], string='Creation', default="auto")
    x_product_usage_ids = fields.One2many('component.usage', 'x_alternate_id', string='Component Usage', store=True)

    x_search_usage = fields.Char(string='Search Usage', required=False)
    x_usage_ids = fields.Many2many(comodel_name='component.usage', string='Usage')

    @api.onchange('x_search_usage')
    def filter_component_usage(self):
        for rec in self:
            rec.unselect_all_usage()
            search_text = rec.x_search_usage
            usage_ids = rec.x_product_usage_ids.filtered(
                lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id)

            if search_text:
                usage_ids = usage_ids.filtered(lambda l: re.search(search_text, '%s %s %s %s %s' % (
                    l.x_bom_tool_id.x_name, l.x_base_bom_id.x_name, l.x_base_bom_line_id.display_name,
                    l.x_line_block_id.display_name, l.x_type), re.IGNORECASE))

            rec.x_usage_ids = [(6, 0, usage_ids.ids)]
            rec.select_all_usage()

    def select_all_usage(self):
        for rec in self:
            for line in rec.x_usage_ids:
                line.x_line_select = True

    def unselect_all_usage(self):
        for rec in self:
            for line in rec.x_usage_ids:
                line.x_line_select = False

    def usage_auto_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'auto_use'
                    line.x_mass_editing = 'disabled'

    def usage_not_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'not_use'
                    line.x_mass_editing = 'disabled'

    def unlink(self):
        self.x_product_usage_ids.unlink()
        return super(TarazPartAlternates, self).unlink()


class TarazPartCompromised(models.Model):
    _name = "taraz.part.compromised"
    _inherit = ['mail.activity.mixin']
    _description = "Taraz Part Compromised"
    _rec_name = "x_compromised_id"
    _order = "x_compromised_id"

    x_taraz_part_number_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part#')
    x_compromised_id = fields.Many2one(comodel_name='taraz.part.number', string='Compromised')
    x_description = fields.Text(string="Description", related="x_compromised_id.x_description")

    x_qty_available = fields.Float(string='On Hand', related="x_compromised_id.x_qty_available")
    x_virtual_available = fields.Float(string='Forecasted', related="x_compromised_id.x_virtual_available")

    x_tz_qty_available = fields.Float(string='On Hand', related="x_compromised_id.x_tz_qty_available")
    x_tz_to_consume_qty = fields.Float(string='To Consume', related="x_compromised_id.x_tz_to_consume_qty")
    x_tz_tray_out_qty = fields.Float(string='Tray Out', related="x_compromised_id.x_tz_tray_out_qty")
    x_tz_available_qty = fields.Float(string='Available', related="x_compromised_id.x_tz_available_qty")
    x_tz_incoming_qty = fields.Float(string='Incoming', related="x_compromised_id.x_tz_incoming_qty")
    x_tz_backorder_qty = fields.Float(string='Backorder', related="x_compromised_id.x_tz_backorder_qty")
    x_tz_outgoing_qty = fields.Float(string='Reserved', related="x_compromised_id.x_tz_outgoing_qty")
    x_tz_virtual_available = fields.Float(string='Forecasted', related="x_compromised_id.x_tz_virtual_available")

    x_uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', related="x_compromised_id.x_uom_id")
    x_creation = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')], string='Creation', default="auto")
    x_product_usage_ids = fields.One2many('component.usage', 'x_compromised_id', string='Component Usage', store=True)

    x_search_usage = fields.Char(string='Search Usage', required=False)
    x_usage_ids = fields.Many2many(comodel_name='component.usage', string='Usage')

    x_two_way_comp = fields.Boolean(string='Two Way', required=False)

    def compute_two_way_comp(self):
        for rec in self:
            two_way_comp_id = self.env['taraz.part.compromised'].search([
                ('x_taraz_part_number_id', '=', rec.x_compromised_id.id),
                ('x_compromised_id', '=', rec.x_taraz_part_number_id.id),
            ])
            if rec.x_two_way_comp:
                rec.x_two_way_comp = False
                if two_way_comp_id:
                    two_way_comp_id.unlink()
            elif not rec.x_two_way_comp:
                rec.x_two_way_comp = True
                if not two_way_comp_id:
                    compromised_id = self.env['taraz.part.compromised'].create({
                        'x_taraz_part_number_id': rec.x_compromised_id.id,
                        'x_compromised_id': rec.x_taraz_part_number_id.id,
                        'x_two_way_comp': True,
                        'x_creation': 'auto',
                    })
                    usage_ids = rec.x_compromised_id.x_usage_ids.filtered(lambda l: l.x_usage_type == 'compromised')
                    if not usage_ids:
                        usage_ids = rec.x_compromised_id.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')
                    for line in usage_ids:
                        line_id = self.env['component.usage'].create({
                            'x_compromised_id': compromised_id.id,
                            'x_base_bom_line_id': line.x_base_bom_line_id.id,
                            'x_usage': line.x_usage,
                            'x_mass_editing': 'enabled'
                        })
                        line_id.x_base_bom_line_id.x_to_be_reviewed = True
                        if line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state == 'active':
                            line_id.x_base_bom_line_id.x_base_bom_id.x_bom_tool_id.state = 'to_be_review'

    @api.onchange('x_search_usage')
    def filter_component_usage(self):
        for rec in self:
            rec.unselect_all_usage()
            search_text = rec.x_search_usage
            usage_ids = rec.x_product_usage_ids.filtered(
                lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id)

            if search_text:
                usage_ids = usage_ids.filtered(lambda l: re.search(search_text, '%s %s %s %s %s' % (
                    l.x_bom_tool_id.x_name, l.x_base_bom_id.x_name, l.x_base_bom_line_id.display_name,
                    l.x_line_block_id.display_name, l.x_type), re.IGNORECASE))

            rec.x_usage_ids = [(6, 0, usage_ids.ids)]
            rec.select_all_usage()

    def select_all_usage(self):
        for rec in self:
            for line in rec.x_usage_ids:
                line.x_line_select = True

    def unselect_all_usage(self):
        for rec in self:
            for line in rec.x_usage_ids:
                line.x_line_select = False

    def usage_auto_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'auto_use'
                    line.x_mass_editing = 'disabled'

    def usage_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'use'
                    line.x_mass_editing = 'disabled'

    def usage_not_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'not_use'
                    line.x_mass_editing = 'disabled'

    def unlink(self):
        self.x_product_usage_ids.unlink()
        return super(TarazPartCompromised, self).unlink()


class ComponentUsage(models.Model):
    _name = 'component.usage'
    _description = "Component Usage"

    x_line_select = fields.Boolean(string='Select', required=False)
    x_alternate_id = fields.Many2one(comodel_name='taraz.part.alternates', string='Alternate', required=False)
    x_compromised_id = fields.Many2one(comodel_name='taraz.part.compromised', string='Compromised', required=False)
    x_mass_editing = fields.Selection(selection=[('enabled', 'Enabled'), ('disabled', 'Disabled')],
                                      default="enabled", string='Mass Editing?', required=True)

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product', required=False)
    x_usage = fields.Selection(selection=[('auto_use', 'Auto Use'), ('use', 'Use'), ('not_use', "Don't Use")],
                               default="auto_use", string='Usage', required=False)


class MassComponentUsage(models.Model):
    _name = "mass.component.usage"
    _description = "Component Usage"

    x_line_select = fields.Boolean(string='Select', required=False)
    x_taraz_part_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part #', required=False)

    x_usage = fields.Selection(selection=[('auto_use', 'Auto Use'), ('use', 'Use'), ('not_use', "Don't Use")],
                               default="auto_use", string='Usage', required=False)

    x_usage_type = fields.Selection(selection=[('alternate', 'Alternate'), ('compromised', 'Compromised')],
                                    string='Usage Type', required=False, )


class TarazPartEditor(models.Model):
    _name = "taraz.part.editor"
    _description = 'Taraz Part Editor'
