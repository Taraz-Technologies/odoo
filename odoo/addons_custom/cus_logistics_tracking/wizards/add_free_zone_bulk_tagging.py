from odoo import models, fields, api

class FreeZoneBulkTagging(models.TransientModel):
    _name = 'free.zone.bulk.tagging'
    _description = 'Wizard: Add or Remove Tags in bulk'

    x_add_tags = fields.Many2many('custom.tags',
                                  relation='free_zone_bulk_tagging_custom_tags_rel1',
                                  column1='free_zone_bulk_tagging_id',
                                  column2='custom_tags_id',
                                  string='Add Tags'
                                  )

    x_remove_tags = fields.Many2many('custom.tags',
                                     relation='free_zone_bulk_tagging_custom_tags_rel2',
                                     column1='free_zone_bulk_tagging_id',
                                     column2='custom_tag_id',
                                     string='Remove Tags'
                                     )

    def action_confirm(self):
        records = self.env['free.zone.operations'].browse(self._context.get('active_ids'))

        for record in records:
            if self.x_add_tags:
                record.x_tag_ids = [(4, tag.id) for tag in self.x_add_tags]
            if self.x_remove_tags:
                record.x_tag_ids = [(3, tag.id) for tag in self.x_remove_tags]
        return {}
