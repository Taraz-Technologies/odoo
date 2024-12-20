# models/cable_assembly_bulk_duplication.py
from odoo import models, fields, api

class CableAssemblyBOMLineBulkDuplication(models.TransientModel):
    _name = 'cable.assembly.bom.line.bulk.duplication'
    _description = 'Wizard: Duplicate Cable Assembly BOMs in Bulk'

    duplication_count = fields.Integer(
        string='Number of Copies',
        required=True,
        default=1,
        help="Specify how many copies you want to create for each selected record."
    )

    def action_confirm(self):
        """
        Duplicates the selected records based on the duplication count.
        """
        records = self.env['cable.assembly.bom.line'].browse(self._context.get('active_ids'))

        for record in records:
            for _ in range(self.duplication_count):
                record.copy()
        return {}