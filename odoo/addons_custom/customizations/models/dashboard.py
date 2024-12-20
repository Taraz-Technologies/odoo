# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class UserDashboard(models.Model):
    _name = "user.dashboard"
    _description = "User Dashboard"
    _order = "x_sequence"
    _rec_name = "x_user_id"

    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_user_id = fields.Many2one('res.users', string='User', index=True, required=True, ondelete='cascade')
    x_items_count = fields.Integer(string="Total Items", required=False, )

    x_hide_update_dashboard_button = fields.Boolean(string="Hide Update Dashboard Button",  )

    x_user_dashboard_code = fields.Text(string="Dashboard Code", required=False, )
    x_current_user_dashboard_code = fields.Text(string="Current Dashboard Code", required=False, )
    x_user_dashboard_items = fields.Many2many(comodel_name="dashboard.item",
                                              relation="user_dashboard_dashboard_item_rel",
                                              column1="user_dashboard_id",
                                              column2="dashboard_item_id",
                                              string="Dashboard Items", )

    def duplicate_current_dashboard(self):
        current_user_dashboard_code = self.env['ir.ui.view.custom'].search([('user_id', '=', self.env.uid), ('ref_id', '=', 1438)], limit=1)

        for record in self:
            if current_user_dashboard_code and record.x_user_id.id != self.env.uid:
                custom_view_arch = current_user_dashboard_code.arch
                if '<action name="925" string="Dashboard of' in custom_view_arch:
                    actions = custom_view_arch.split('<action')
                    for action in actions:
                        action = '<action' + action
                        if '<action name="925" string="Dashboard of' in custom_view_arch:
                            if '/>' in action:
                                action = action.split('/>')
                                action = action[0] + '/>'
                            elif '</action>' in action:
                                action = action.split('</action>')
                                action = action[0] + '</action>'
                            custom_view_arch = custom_view_arch.replace(action, '')

                item_count = 0
                record.x_user_dashboard_code = custom_view_arch
                record.x_user_dashboard_items = [(5, 0, 0)]

                dashboard_items = self.env['dashboard.item'].search([])
                for item in dashboard_items:
                    item_code = item.x_view_code
                    if item_code in record.x_user_dashboard_code:
                        item_count = item_count + 1
                        record.x_user_dashboard_items = [(4, item.id)]
                record.x_items_count = item_count
                record.update_user_dashboard()

    def update_user_dashboard(self):
        for record in self:
            dashboard_custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', record.x_user_id.id), ('ref_id', '=', 1438)], limit=1)
            if dashboard_custom_view:
                dashboard_custom_view.arch = record.x_user_dashboard_code
                if record.x_user_id.id == self.env.uid and record.x_current_user_dashboard_code:
                    record.x_current_user_dashboard_code = False
                    record.x_hide_update_dashboard_button = False
            else:
                values = {
                    'user_id': record.x_user_id.id,
                    'ref_id': 1438,
                    'arch': record.x_user_dashboard_code,
                }
                self.env['ir.ui.view.custom'].sudo().create(values)

    def view_dashboard(self):
        for record in self:
            current_user_dashboard_code = self.env['ir.ui.view.custom'].search([('user_id', '=', self.env.uid), ('ref_id', '=', 1438)], limit=1)
            user_dashboard_code = record.x_user_dashboard_code
            if record.x_user_id.id == self.env.uid and record.x_current_user_dashboard_code:
                current_user_dashboard_code.arch = record.x_current_user_dashboard_code
                record.get_user_data()
                record.x_current_user_dashboard_code = False
                record.x_hide_update_dashboard_button = False
            elif record.x_user_id.id != self.env.uid:
                current_user_dashboard = self.env['user.dashboard'].search([('x_user_id', '=', self.env.uid)])
                current_user_dashboard.x_hide_update_dashboard_button = True
                if not current_user_dashboard.x_current_user_dashboard_code:
                    current_user_dashboard.x_current_user_dashboard_code = current_user_dashboard_code.arch

                current_dashboard_user = _('<action name="925" string="Dashboard of %s (User Dashboards)" modifiers="{}" fold="1"/>') % (record.x_user_id.name)
                if '<action' in user_dashboard_code:
                    user_dashboard_code = user_dashboard_code.split('<action')
                    for value in user_dashboard_code:
                        if '<board' in value:
                            current_user_dashboard_code.arch = value + current_dashboard_user
                        else:
                            current_user_dashboard_code.arch = current_user_dashboard_code.arch + '<action' + value
                else:
                    current_user_dashboard_code.arch = user_dashboard_code

            action = self.env.ref('board.open_board_my_dash_action').read()[0]
            return action

    @api.onchange('x_user_dashboard_items')
    def update_data(self):
        for record in self:
            # Remove Items view code in Dashboard Code
            dashboard_items = self.env['dashboard.item'].search([])
            user_dashboard_items = record.x_user_dashboard_items

            if not record.x_user_dashboard_code:
                record.x_user_dashboard_items = [(5, 0, 0)]
            else:
                for dashboard_item in dashboard_items:
                    user_dashboard_code = record.x_user_dashboard_code

                    dashboard_item_exist = False
                    for user_dashboard_item in user_dashboard_items:
                        if dashboard_item.x_view_code == user_dashboard_item.x_view_code:
                            dashboard_item_exist = True
                            break

                    if not dashboard_item_exist and dashboard_item.x_view_code in user_dashboard_code:
                        dashboard_item_code = dashboard_item.x_view_code
                        action_codes = user_dashboard_code.split('<action')

                        for action_code in action_codes:
                            action_code = '<action' + action_code

                            if '/>' in action_code:                     # For Last item
                                action_code = action_code.split('/>')
                                action_code = action_code[0] + '/>'
                            elif '</action>' in action_code:            # For Last item
                                action_code = action_code.split('</action>')
                                action_code = action_code[0] + '</action>'

                            if dashboard_item_code in action_code:
                                record.x_user_dashboard_code = user_dashboard_code.replace(action_code, '')

            # Add Items view code in Dashboard Code
            item_count = 0
            if not record.x_user_dashboard_code:
                record.x_user_dashboard_code = '<form string="My Dashboard" js_class="board">\n' \
                                               '    <board style="1">\n' \
                                               '        <column>\n' \
                                               '\n' \
                                               '        </column><column>\n' \
                                               '\n' \
                                               '        </column><column>\n' \
                                               '\n' \
                                               '        </column>\n' \
                                               '    </board>\n' \
                                               '</form>'

            for user_dashboard_item in record.x_user_dashboard_items:
                item_count = item_count + 1

                if not user_dashboard_item.x_view_code in record.x_user_dashboard_code:

                    dashboard_code = record.x_user_dashboard_code
                    dashboard_code = dashboard_code.split('<column>')

                    record.x_user_dashboard_code = dashboard_code[0] + '<column>\n                ' + user_dashboard_item.x_view_code + '/>'
                    if len(dashboard_code) >= 2:
                        record.x_user_dashboard_code = record.x_user_dashboard_code + dashboard_code[1]
                    if len(dashboard_code) >= 3:
                        record.x_user_dashboard_code = record.x_user_dashboard_code + '<column>' + dashboard_code[2]
                    if len(dashboard_code) >= 4:
                        record.x_user_dashboard_code = record.x_user_dashboard_code + '<column>' + dashboard_code[3]

            record.x_items_count = item_count

    @api.onchange('x_user_id')
    def get_user_data(self):
        for record in self:
            if record.x_user_id:
                dashboard_custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', record.x_user_id.id), ('ref_id', '=', 1438)], limit=1)
                item_count = 0
                if dashboard_custom_view:
                    record.x_user_dashboard_code = dashboard_custom_view.arch
                    record.x_user_dashboard_items = [(5, 0 ,0)]

                    dashboard_items = self.env['dashboard.item'].search([])
                    for item in dashboard_items:
                        item_code = item.x_view_code
                        if item_code in record.x_user_dashboard_code:
                            item_count = item_count + 1
                            record.x_user_dashboard_items = [(4, item.id)]
                record.x_items_count = item_count


class DashboardItem(models.Model):
    _name = "dashboard.item"
    _description = "Dashboard Item"
    _rec_name = "x_name"
    _order = "create_date desc"

    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_name = fields.Char(string="Name", required=False, readonly=True, )
    x_view_name = fields.Char(string="View Name", required=False, )
    x_view_mode = fields.Char(string="View Mode", required=False, )
    x_view_code = fields.Text(string="View Code", required=False, )
    x_user_id = fields.Many2one(comodel_name="res.users", string="User", required=False, )
    x_user_ids = fields.Many2many(comodel_name="res.users",
                                  relation="dashboard_item_res_users_rel",
                                  column1="res_users_id",
                                  column2="dashboard_item_id",
                                  string="Shared with", )

    def view_user_dashboard(self):
        for record in self:
            user_dashboard = self.env['user.dashboard'].search([('x_user_id', '=', record.x_user_id.id)])
            return user_dashboard.view_dashboard()

    @api.onchange('x_user_ids')
    def update_dashboard(self):
        for record in self:
            item_code = record.x_view_code
            item_users = record.x_user_ids.mapped('name')
            odoo_users = self.env['res.users'].sudo().search([]).mapped('name')
            for odoo_user in odoo_users:
                odoo_user_id = self.env['res.users'].sudo().search([('name', '=', odoo_user)])
                user_custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', odoo_user_id.id), ('ref_id', '=', 1438)], limit=1)
                if odoo_user in item_users and user_custom_view:
                    custom_view_code = user_custom_view.arch
                    if not item_code in custom_view_code:
                        custom_view_code = custom_view_code.split('<column>')

                        user_custom_view.arch = custom_view_code[0] + '<column>\n                ' + record.x_view_code + '/>'
                        if len(custom_view_code) >= 2:
                            user_custom_view.arch = user_custom_view.arch + custom_view_code[1]
                        if len(custom_view_code) >= 3:
                            user_custom_view.arch = user_custom_view.arch + '<column>' + custom_view_code[2]
                        if len(custom_view_code) >= 4:
                            user_custom_view.arch = user_custom_view.arch + '<column>' + custom_view_code[3]
                elif odoo_user in item_users and not user_custom_view:
                    custom_view_code = '<form string="My Dashboard" js_class="board">\n' \
                                       '    <board style="1">\n' \
                                       '        <column>\n' \
                                       '                ' + item_code + '/>\n' \
                                       '        </column><column>\n' \
                                       '\n' \
                                       '        </column><column>\n' \
                                       '\n' \
                                       '        </column>\n' \
                                       '    </board>\n' \
                                       '</form>'
                    values = {
                        'user_id': odoo_user_id.id,
                        'ref_id': 1438,
                        'arch': custom_view_code,
                    }
                    self.env['ir.ui.view.custom'].sudo().create(values)
                elif not odoo_user in item_users and user_custom_view:
                    custom_view_code = user_custom_view.arch
                    if item_code in custom_view_code:
                        action_codes = custom_view_code.split('<action')

                        for action_code in action_codes:
                            action_code = '<action' + action_code

                            if '/>' in action_code:                     # For Last item
                                action_code = action_code.split('/>')
                                action_code = action_code[0] + '/>'
                            elif '</action>' in action_code:            # For Last item
                                action_code = action_code.split('</action>')
                                action_code = action_code[0] + '</action>'

                            if item_code in action_code:
                                user_custom_view.arch = custom_view_code.replace(action_code, '')


class ViewCustom(models.Model):
    _inherit = 'ir.ui.view.custom'


    def _update_dashboard_items(self):
        user_dashboard_custom_view = self.env['ir.ui.view.custom'].search([('user_id', '=', self.env.uid), ('ref_id', '=', 1438)], limit=1)
        dashboard_view_code = user_dashboard_custom_view.arch
        if dashboard_view_code:
            dashboard_view_code = dashboard_view_code.split('<action')

            dashboard_items = self.env['dashboard.item'].search([])

            # Create Dashboard Items
            for action_code in dashboard_view_code:
                if '/>' in action_code:
                    action_code = action_code.split('/>')
                    action_code = action_code[0]
                elif '</action>' in action_code:
                    action_code = action_code.split('>')
                    action_code = action_code[0]

                if 'view_mode' in action_code:
                    action_code = '<action' + action_code

                    create_dashboard_item = True
                    # Check if action Code exist in items
                    for item in dashboard_items:
                        item_code = item.x_view_code
                        if item_code in action_code:
                            create_dashboard_item = False
                            break

                    if create_dashboard_item:
                        action_name = action_code.split('"')
                        for value in range(len(action_name)):
                            if 'string' in action_name[value]:
                                action_name = action_name[value + 1]
                                break

                        action_mode = action_code.split()
                        for value in action_mode:
                            if 'view_mode' in value:
                                action_mode = value.split('"')
                                action_mode = action_mode[1]
                                break

                        values = {
                            'x_name': str(action_name) + " [" + str(action_mode).title() + " View]",
                            'x_view_name': action_name,
                            'x_view_mode': action_mode,
                            'x_view_code': action_code,
                            'x_user_ids': [(4, self.env.uid)]
                        }
                        self.env['dashboard.item'].create(values)

    def _update_dashboard_item_users(self):
        user_list = self.env['res.users'].sudo().search([])
        dashboard_items = self.env['dashboard.item'].search([])
        for dashboard_item in dashboard_items:
            for user in user_list:
                user_custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', user.id),('ref_id', '=', 1438)], limit=1)
                if user_custom_view:
                    if dashboard_item.x_view_code in user_custom_view.arch:
                        dashboard_item.x_user_ids = [(4, user.id)]
                    if not dashboard_item.x_view_code in user_custom_view.arch:
                        dashboard_item.x_user_ids = [(3, user.id)]

    def _create_and_update_user_dashboard(self):
        user_list = self.env['res.users'].sudo().search([])
        dashboard_users_list = self.env['user.dashboard'].sudo().search([]).mapped('x_user_id')
        custom_view_users_list = self.env['ir.ui.view.custom'].sudo().search([('ref_id', '=', 1438)]).mapped('user_id')

        for user in user_list:
            if user in dashboard_users_list and user in custom_view_users_list:
                user_dashboard = self.env['user.dashboard'].sudo().search([('x_user_id', '=', user.id)])
                user_dashboard.get_user_data()
            elif not user in dashboard_users_list and user in custom_view_users_list:
                user_custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', user.id), ('ref_id', '=', 1438)], limit=1)
                values = {
                    'x_user_id': user.id,
                    'x_user_dashboard_code': user_custom_view.arch
                }
                user_dashboard = self.env['user.dashboard'].sudo().create(values)
                user_dashboard.get_user_data()
            elif not user in dashboard_users_list and not user in custom_view_users_list:
                values = {
                    'user_id': user.id,
                    'ref_id': 1438,
                    'arch': '<form string="My Dashboard" js_class="board">\n' \
                            '    <board style="1">\n' \
                            '        <column>\n' \
                            '\n' \
                            '        </column><column>\n' \
                            '\n' \
                            '        </column><column>\n' \
                            '\n' \
                            '        </column>\n' \
                            '    </board>\n' \
                            '</form>',
                }
                self.env['ir.ui.view.custom'].sudo().create(values)


class View(models.Model):
    _inherit = 'ir.ui.view'

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.name, rec.xml_id)))
        return res

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #     recs = self.browse()
    #     if not recs:
    #         recs = self.search([('name', operator, name)] + args, limit=limit)
    #     return recs.name_get()


class DynamicDateRange(models.Model):
    _name = "dynamic.date.range"
    _description = "Dynamic Date Range"
    _rec_name = 'x_name'
    _order = 'x_name'

    x_name = fields.Char(string="Name", required=True, readonly=True, copy=False, default='New')
    state = fields.Selection(string="Status", required=True, readonly=True, copy=False, tracking=True, default='new',
                               selection=[
                                   ('new', 'New'),
                                   ('added', 'Added'),
                                   ('cancel', 'Cancelled'),
                               ], )
    x_period = fields.Selection(string="Period",
                                selection=[
                                    ('current_year', 'Current Year'),
                                    ('previous_year', 'Previous Year'),
                                    ('current_fiscal_year', 'Current Fiscal Year'),
                                    ('previous_fiscal_year', 'Previous Fiscal Year'),
                                ],
                                required=True, )

    x_date_from = fields.Date(string="Date From", required=False, compute="update_date_range", store=True, )
    x_date_to = fields.Date(string="Date To", required=False, compute="update_date_range",  store=True, )
    x_search_view = fields.Many2one(comodel_name="ir.ui.view",
                                    string="ControlPanelView",
                                    required=True,
                                    domain="[('type', '=', 'search'), ('mode', '=', 'primary')]", )
    x_view_external_id = fields.Char(string="View External ID", required=False, related='x_search_view.xml_id')

    x_view_model = fields.Many2one(comodel_name="ir.model", string="View Model", required=False, compute="get_view_model", store=True, )
    x_model_date_field = fields.Many2one(comodel_name="ir.model.fields",
                                         string="Model Date Field",
                                         required=True,
                                         domain="[('model_id', '=', x_view_model)]", )

    @api.depends('x_period')
    def update_date_range(self):
        for record in self:
            if record.x_period == 'current_year':
                record.x_date_from = datetime.datetime.now().strftime('%Y-01-01')
                record.x_date_to = datetime.datetime.now().strftime('%Y-12-31')
            elif record.x_period == 'previous_year':
                record.x_date_from = datetime.datetime(datetime.datetime.now().year - 1, 1 ,1)
                record.x_date_to = datetime.datetime(datetime.datetime.now().year - 1, 12 ,31)
            elif record.x_period == 'current_fiscal_year':
                if datetime.datetime.now().month < 7:
                    record.x_date_from = datetime.datetime(datetime.datetime.now().year - 1, 7 ,1)
                    record.x_date_to = datetime.datetime.now().strftime('%Y-06-30')
                else:
                    record.x_date_from = datetime.datetime.now().strftime('%Y-07-01')
                    record.x_date_to = datetime.datetime(datetime.datetime.now().year + 1, 6 ,30)
            elif record.x_period == 'previous_fiscal_year':
                if datetime.datetime.now().month < 7:
                    record.x_date_from = datetime.datetime(datetime.datetime.now().year - 2, 7 ,1)
                    record.x_date_to = datetime.datetime(datetime.datetime.now().year - 1, 6 ,30)
                else:
                    record.x_date_from = datetime.datetime(datetime.datetime.now().year - 1, 7 ,1)
                    record.x_date_to = datetime.datetime.now().strftime('%Y-06-30')

    @api.depends('x_search_view')
    def get_view_model(self):
        for record in self:
            record.x_view_model = self.env['ir.model'].search([('model', '=', record.x_search_view.model)]).id

    @api.model
    def create(self, vals):
        if vals.get('x_name', 'New') == 'New':
            vals['x_name'] = self.env['ir.sequence'].next_by_code('dynamic.date.range') or 'New'
        result = super(DynamicDateRange, self).create(vals)
        return result

    def get_domain(self):
        for record in self:
            if record.x_period == 'current_year':
                filter_domain = "[('" + record.x_model_date_field.name + "', '&lt;', (context_today() + relativedelta(years = 1)).strftime('%%Y-01-01')), " \
                              "('" + record.x_model_date_field.name + "', '&gt;=', time.strftime('%%Y-01-01'))]"
            elif record.x_period == 'previous_year':
                filter_domain = "[('" + record.x_model_date_field.name + "', '&gt;=', (context_today() - relativedelta(years = 1)).strftime('%%Y-01-01')), " \
                              "('" + record.x_model_date_field.name + "', '&lt;', time.strftime('%%Y-01-01'))]"
            elif record.x_period == 'current_fiscal_year':
                if datetime.datetime.now().month < 7:
                    filter_domain = "[('" + record.x_model_date_field.name + "', '&gt;=', (context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')), " \
                                  "('" + record.x_model_date_field.name + "', '&lt;', time.strftime('%%Y-07-01'))]"
                else:
                    filter_domain = "[('" + record.x_model_date_field.name + "', '&lt;', (context_today() + relativedelta(years = 1)).strftime('%%Y-07-01')), " \
                                  "('" + record.x_model_date_field.name + "', '&gt;=', time.strftime('%%Y-07-01'))]"
            elif record.x_period == 'previous_fiscal_year':
                if datetime.datetime.now().month < 7:
                    filter_domain = "[('" + record.x_model_date_field.name + "', '&gt;=', (context_today() - relativedelta(years = 2)).strftime('%%Y-07-01')), " \
                                  "('" + record.x_model_date_field.name + "', '&lt;', (context_today() - relativedelta(years = 1)).strftime('%%Y-07-01'))]"
                else:
                    filter_domain = "[('" + record.x_model_date_field.name + "', '&gt;=', (context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')), " \
                                  "('" + record.x_model_date_field.name + "', '&lt;', time.strftime('%%Y-07-01'))]"
            return filter_domain

    def remove_filter_from_search_view(self):
        for record in self:
            view_name = record.x_name.lower()
            view_name = view_name.replace(' ', '.')
            view_name = record.x_search_view.name + '.auto.filter.' + view_name

            self.env['ir.ui.view'].search([('name', '=', view_name)]).unlink()
            record.state = 'cancel'

    def update_filter_in_search_view(self):
        for record in self:

            # ---------- Update Filter ----------
            view_name = record.x_name.lower()
            view_name = view_name.replace(' ', '.')
            view_name = record.x_search_view.name + '.auto.filter.' + view_name

            view_rec = self.env['ir.ui.view'].search([('name', '=', view_name)])
            if not view_rec:
                raise UserError(_('Filter not found!'))

            arch_base = view_rec.arch_base
            arch_base_domain = arch_base.split('domain="')
            arch_base_domain = arch_base_domain[1].split('"/>')
            arch_base_domain = arch_base_domain[0]

            new_domain = record.get_domain()

            arch_base = arch_base.replace(arch_base_domain, new_domain)
            view_rec.update({
                'arch_base': arch_base,
            })

            # ---------- Update Saved Searches ----------

            #  convert domain from  [('filed_name', '&gt;=', argument), ('filed_name', '&lt;', argument)]
            #  into this            ("filed_name", ">=", argument), ("filed_name", "<", argument)
            old_domain = arch_base_domain.replace('[', '')
            old_domain = old_domain.replace(']', '')
            old_domain = old_domain.replace('\'', '\"')
            old_domain = old_domain.replace('&gt;', '>')
            old_domain = old_domain.replace('&lt;', '<')
            #  convert domain from  [('filed_name', '&gt;=', argument), ('filed_name', '&lt;', argument)]
            #  into this            ("filed_name", ">=", argument), ("filed_name", "<", argument)
            new_domain = new_domain.replace('[', '')
            new_domain = new_domain.replace(']', '')
            new_domain = new_domain.replace('\'', '\"')
            new_domain = new_domain.replace('&gt;', '>')
            new_domain = new_domain.replace('&lt;', '<')

            saved_searches = self.env['ir.filters'].search([('name', 'ilike', record.x_name), ('model_id', '=', record.x_view_model.model)])
            for filter in saved_searches:
                filter_domain = filter.domain
                filter.domain = filter_domain.replace(old_domain, new_domain)

            # ---------- Update Dashboard Items & Dashboard & User Dashboards----------
            #  convert domain from  ("filed_name", ">=", argument), ("filed_name", "<", argument)
            #  into this            ['filed_name', '&gt;=', '%Y-%m-%d'], ['filed_name', '&lt;', '%Y-%m-%d']
            old_domain = old_domain.replace('\"', '\'')
            old_domain = old_domain.replace('>', '&gt;')
            old_domain = old_domain.replace('<', '&lt;')

            if "time.strftime('%%Y-01-01')" in old_domain:
                old_domain = old_domain.replace("time.strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime.now().strftime('%Y-01-01') + "\'")
            if "time.strftime('%%Y-07-01')" in old_domain:
                old_domain = old_domain.replace("time.strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime.now().strftime('%Y-07-01') + "\'")
            if "(context_today() + relativedelta(years = 1)).strftime('%%Y-01-01')" in old_domain:
                old_domain = old_domain.replace("(context_today() + relativedelta(years = 1)).strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year + 1, 1 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 1)).strftime('%%Y-01-01')" in old_domain:
                old_domain = old_domain.replace("(context_today() - relativedelta(years = 1)).strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 1, 1 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() + relativedelta(years = 1)).strftime('%%Y-07-01')" in old_domain:
                old_domain = old_domain.replace("(context_today() + relativedelta(years = 1)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year + 1, 7 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')" in old_domain:
                old_domain = old_domain.replace("(context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 1, 7 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 2)).strftime('%%Y-07-01')" in old_domain:
                old_domain = old_domain.replace("(context_today() - relativedelta(years = 2)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 2, 7 ,1).strftime('%Y-%m-%d') + "\'")

            old_domain = old_domain.replace('(', '[')
            old_domain = old_domain.replace(')', ']')
            #  convert domain from  ("filed_name", ">=", argument), ("filed_name", "<", argument)
            #  into this            ['filed_name', '&gt;=', '%Y-%m-%d'], ['filed_name', '&lt;', '%Y-%m-%d']
            new_domain = new_domain.replace('\"', '\'')
            new_domain = new_domain.replace('>', '&gt;')
            new_domain = new_domain.replace('<', '&lt;')

            if "time.strftime('%%Y-01-01')" in new_domain:
                new_domain = new_domain.replace("time.strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime.now().strftime('%Y-01-01') + "\'")
            if "time.strftime('%%Y-07-01')" in new_domain:
                new_domain = new_domain.replace("time.strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime.now().strftime('%Y-07-01') + "\'")
            if "(context_today() + relativedelta(years = 1)).strftime('%%Y-01-01')" in new_domain:
                new_domain = new_domain.replace("(context_today() + relativedelta(years = 1)).strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year + 1, 1 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 1)).strftime('%%Y-01-01')" in new_domain:
                new_domain = new_domain.replace("(context_today() - relativedelta(years = 1)).strftime('%%Y-01-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 1, 1 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() + relativedelta(years = 1)).strftime('%%Y-07-01')" in new_domain:
                new_domain = new_domain.replace("(context_today() + relativedelta(years = 1)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year + 1, 7 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')" in new_domain:
                new_domain = new_domain.replace("(context_today() - relativedelta(years = 1)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 1, 7 ,1).strftime('%Y-%m-%d') + "\'")
            if "(context_today() - relativedelta(years = 2)).strftime('%%Y-07-01')" in new_domain:
                new_domain = new_domain.replace("(context_today() - relativedelta(years = 2)).strftime('%%Y-07-01')",
                                                "\'" + datetime.datetime(datetime.datetime.now().year - 2, 7 ,1).strftime('%Y-%m-%d') + "\'")

            new_domain = new_domain.replace('(', '[')
            new_domain = new_domain.replace(')', ']')

            dashboard_items = self.env['dashboard.item'].search([('x_name', 'ilike', record.x_name)])
            for dashboard_item in dashboard_items:
                old_item_code = dashboard_item.x_view_code
                if record.x_name in old_item_code:
                    item_model = old_item_code.split(" \'model\': \'")
                    item_model = item_model[1].split('\'')
                    item_model = item_model[0]
                    if record.x_view_model.model == item_model:
                        dashboard_item.x_view_code = old_item_code.replace(old_domain, new_domain)
                        custom_views = self.env['ir.ui.view.custom'].sudo().search([('arch', 'ilike', old_item_code), ('ref_id', '=', 1438)])
                        for custom_view in custom_views:
                            custom_view.arch = custom_view.arch.replace(old_item_code, dashboard_item.x_view_code)
                        user_dashboards = self.env['user.dashboard'].sudo().search([('x_user_dashboard_code', 'ilike', old_item_code)])
                        for user_dashboard in user_dashboards:
                            user_dashboard.x_user_dashboard_code = user_dashboard.x_user_dashboard_code.replace(old_item_code, dashboard_item.x_view_code)
                        user_dashboards = self.env['user.dashboard'].sudo().search([('x_current_user_dashboard_code', 'ilike', old_item_code)])
                        for user_dashboard in user_dashboards:
                            user_dashboard.x_current_user_dashboard_code = user_dashboard.x_current_user_dashboard_code.replace(old_item_code, dashboard_item.x_view_code)

    def add_filter_in_search_view(self):
        for record in self:
            filter_name = record.x_name.lower()
            filter_name = filter_name.replace(' ', '.')

            new_view_name = record.x_search_view.name + '.auto.filter.' + filter_name

            base_filter_name = record.x_search_view.arch_base
            base_filter_name = base_filter_name.split('<filter')
            base_filter_name = base_filter_name[1].split('name=')
            base_filter_name = base_filter_name[1].split('\"')
            base_filter_name = base_filter_name[1]

            filter_name = filter_name.replace('.', '_')

            arch_base = "<?xml version=\"1.0\"?>" \
                        "\n<data>" \
                        "\n   <xpath expr=\"//filter[@name='" + base_filter_name + "']\" position=\"before\">" \
                        "\n       <filter name=\"" + filter_name +  "\" string=\"" + record.x_name +  "\" domain=\"" + record.get_domain() + "\"/>" \
                        "\n       <separator/>" \
                        "\n   </xpath>" \
                        "\n</data>"

            values = {
                'name': new_view_name,
                'type': 'search',
                'model': record.x_search_view.model,
                'priority': 99,
                'active': True,
                'inherit_id': record.x_search_view.id,
                'mode': 'extension',
                'arch_base': arch_base,
            }
            self.env['ir.ui.view'].create(values)
            record.state = 'added'

