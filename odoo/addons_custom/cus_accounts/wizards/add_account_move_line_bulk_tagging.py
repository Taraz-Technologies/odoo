from odoo import models, fields, api

class AccountBulkTagging(models.TransientModel):
    _name = 'account.move.line.bulk.tagging'
    _description = 'Wizard: Add or Remove Tags in bulk'

    x_add_tags = fields.Many2many('custom.tags',
                                  relation='account_move_line_bulk_tagging_custom_tags_rel1',
                                  column1='account_move_line_bulk_tagging_id',
                                  column2='custom_tags_id',
                                  string='Add Tags'
                                  )

    x_remove_tags = fields.Many2many('custom.tags',
                                     relation='account_move_line_bulk_tagging_custom_tags_rel2',
                                     column1='account_move_line_bulk_tagging_id',
                                     column2='custom_tag_id',
                                     string='Remove Tags'
                                     )

    def action_confirm(self):
        records = self.env['account.move.line'].browse(self._context.get('active_ids'))

        for record in records:
            if self.x_add_tags:
                record.x_custom_tag_ids = [(4, tag.id) for tag in self.x_add_tags]
            if self.x_remove_tags:
                record.x_custom_tag_ids = [(3, tag.id) for tag in self.x_remove_tags]
        return {}
