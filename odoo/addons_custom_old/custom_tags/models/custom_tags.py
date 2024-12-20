from openpyxl.styles.builtins import comma

from odoo import fields, models, api


class CustomTags(models.Model):
    _name = "custom.tags"
    _description = "Custom Tags"
    _rec_name = 'x_name'

    x_name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')


    def _track_many2many_changes(self, record, field_name, old_values=None, new_values=None):
        """ Custom method to track Many2many field changes """
        added = set(new_values or []) - set(old_values or [])
        removed = set(old_values or []) - set(new_values or [])

        if added or removed:
            changes = []

            # Handle additions
            if added:
                added_records = self.env['custom.tags'].browse(added)
                for added_record in added_records:
                    changes.append(f"<li>Added: {added_record.x_name}</li>")

            # Handle removals
            if removed:
                removed_records = self.env['custom.tags'].browse(removed)
                for removed_record in removed_records:
                    changes.append(f"<li>Removed: {removed_record.x_name}</li>")

            # Combine changes into a single message with HTML list
            if changes:
                message = f"Tags Updated:\n<ul>{''.join(changes)}</ul>"
                record.message_post(body=message, subtype='mail.mt_note')