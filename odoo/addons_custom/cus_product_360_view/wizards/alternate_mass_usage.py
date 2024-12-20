from odoo import api, fields, models

import re


class AlternateMassUsageEditingWizard(models.TransientModel):
    _name = "alternate.mass.usage.editing.wizard"
    _description = "Alternate Usage Mass Editing"

    x_taraz_part_id = fields.Many2one(comodel_name='taraz.part.number', string='Taraz Part # (Parent)', required=False)

    x_search_usage = fields.Char(string='Search Usage', required=False)
    x_usage_ids = fields.Many2many(comodel_name='mass.component.usage', string='Mass Usage')

    @api.model
    def default_get(self, fields_list):
        res = super(AlternateMassUsageEditingWizard, self).default_get(fields_list)
        res.update({'x_taraz_part_id': self.env.context.get('active_id')})
        return res

    @api.onchange('x_taraz_part_id', 'x_search_usage')
    def filter_component_usage(self):
        for rec in self:
            rec.unselect_all_usage()
            search_text = rec.x_search_usage
            usage_ids = rec.x_taraz_part_id.x_usage_ids.filtered(lambda l: l.x_usage_type == 'alternate')

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

            return rec.return_wizard_action()

    def unselect_all_usage(self):
        for rec in self:
            for line in rec.x_usage_ids:
                line.x_line_select = False

            return rec.return_wizard_action()

    def usage_auto_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'auto_use'
                    line_ids = self.env['component.usage'].search([
                        ('x_base_bom_line_id', '=', line.x_base_bom_line_id.id),
                        ('x_alternate_id', 'in', rec.x_taraz_part_id.x_alternate_ids.ids),
                        ('x_mass_editing', '=', 'enabled'),
                    ])
                    line_ids = line_ids.filtered(lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id)
                    line_ids.update({'x_usage': 'auto_use'})

            return rec.return_wizard_action()

    def usage_not_use(self):
        for rec in self:
            for line in rec.x_usage_ids:
                if line.x_line_select:
                    line.x_usage = 'not_use'
                    line_ids = self.env['component.usage'].search([
                        ('x_base_bom_line_id', '=', line.x_base_bom_line_id.id),
                        ('x_alternate_id', 'in', rec.x_taraz_part_id.x_alternate_ids.ids),
                        ('x_mass_editing', '=', 'enabled'),
                    ])
                    line_ids = line_ids.filtered(lambda l: l.x_bom_tool_id.x_base_bom_id.id == l.x_base_bom_id.id)
                    line_ids.update({'x_usage': 'not_use'})

            return rec.return_wizard_action()

    def return_wizard_action(self):
        action = self.env.ref('cus_product_360_view.action_alternate_mass_usage_editing').read()[0]
        form_view = [(self.env.ref('cus_product_360_view.view_alternate_mass_usage_editing_wizard_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.id
        return action
