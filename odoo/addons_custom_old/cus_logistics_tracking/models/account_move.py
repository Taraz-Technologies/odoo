from odoo import api, fields, models, _
import logging

_logger = logging.getLogger("*__addons_custom__*")


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_consolidation_id = fields.Many2one(comodel_name='consolidation.tracking', string='Consolidation', required=False)
    x_consolidation_ref = fields.Char(related="x_consolidation_id.x_consolidation_ref")
    x_shipping_invoice_name = fields.Char(related="x_consolidation_id.x_shipping_invoice_name")
    x_shipping_invoice = fields.Binary(related="x_consolidation_id.x_shipping_invoice")

    x_picking_count = fields.Integer(compute="_compute_picking_count")
    x_attach_pickings = fields.Boolean(related="journal_id.x_attach_pickings")

    x_landed_cost_state = fields.Selection(
        selection=[
            ('pending', 'Not a Landed Costs Bill or ROs are not validated'),
            ('normal', 'Landed Costs are created'),
            ('blocked', 'Landed Costs are not created'),
            ('done', 'Landed Costs are validated')],
        string='LC',
        copy=False,
        default='pending',
        required=True,
        compute="_compute_landed_cost_state",
        store=True,
        tracking=True,
        readonly=False)

    x_free_zone_operation_id = fields.Many2one(
        comodel_name='free.zone.operations',
        string='Free Zone Operation',
        required=False)

    x_operation_type = fields.Selection(selection=[
        ('free', 'FZ Operation'), ('otb', 'OTB Operation'),
    ], string='Operation (FZ/OTB)', help="Free Zone or OTB Operation")

    x_attachment_name = fields.Char(
        string='Download File Name')
    x_attachment = fields.Binary(
        string='FZ File',
        copy=False,
        tracking=True,)
    x_form_field_01 = fields.Char(
        string='Form No.',
        copy=False,
        tracking=True)
    x_form_field_02 = fields.Selection(
        string='İŞLEM YÖNÜ',
        selection=[
            ("from_turkey", "Bölgeye Türkiye'den Mal-Hizmet Girişi"),
            ("from_abroad", "Bölgeye Yurt Dışından Mal-Hizmet Girişi"), ],
        copy=False,
        tracking=True)
    x_form_field_03 = fields.Selection(
        string='İŞLEM KONUSU',
        selection=[
            ("Ticari-Mal", "Ticari-Mal"),
            ("Ticari Olmayan-Demirbaş", "Ticari Olmayan-Demirbaş"),
            ("Ticari Olmayan-Sarf Malzemesi", "Ticari Olmayan-Sarf Malzemesi"),
            ("Ticari Olmayan-Yatırım ve Tesis", "Ticari Olmayan-Yatırım ve Tesis"),
            ("Ticari Olmayan-Hizmet Alımı", "Ticari Olmayan-Hizmet Alımı"), ],
        copy=False,
        tracking=True)
    x_form_field_04 = fields.Selection(
        string='İŞLEM TÜRÜ',
        selection=[
            ("Kesin Alış/Satış", "Kesin Alış/Satış"),
            ("Diğer İşlem Türleri-5000$ Altı", "Diğer İşlem Türleri-5000$ Altı"), ],
        copy=False,
        tracking=True)
    x_form_field_05 = fields.Char(
        string='SEVKİYAT ŞEKLİ',
        copy=False,
        tracking=True)
    x_form_field_06 = fields.Char(
        string='TAŞIT CİNSİ',
        copy=False,
        tracking=True)
    x_form_field_07 = fields.Float(
        string='Mal Bedeli Toplamları',
        copy=False,
        tracking=True)
    x_form_field_08 = fields.Float(
        string='CIF Toplamı',
        copy=False,
        tracking=True)
    x_form_field_09 = fields.Date(
        string='GİRİŞ / ÇIKIŞ Tarih',
        copy=False,
        tracking=True)
    x_form_field_10 = fields.Float(
        string='Brüt Ağırlık Toplamı',
        copy=False,
        tracking=True)
    x_form_field_11 = fields.Date(
        string='Formu Tarih',
        copy=False,
        tracking=True)
    x_form_field_12 = fields.Float(
        string='KAP',
        copy=False,
        tracking=True)
    x_form_field_13 = fields.Many2one(
        comodel_name='res.currency',
        string='Mal Bedeli Toplamları Currency',
        copy=False,
        tracking=True)
    x_form_field_14 = fields.Many2one(
        comodel_name='res.currency',
        string='CIF Toplamı Currency',
        copy=False,
        tracking=True)

    def pull_form_data_from_picking(self):
        for rec in self:
            if rec.picking_id:
                rec.picking_id.push_form_data_to_account_moves()
            elif rec.x_picking_ids:
                rec.x_picking_ids[0].push_form_data_to_account_moves()
            else:
                move_ids_without_package = self.env['stock.move'].search([('id', '=', rec.stock_move_id.id)])
                if move_ids_without_package:
                    move_ids_without_package[0].picking_id.push_form_data_to_account_moves()

    @api.depends(
        'invoice_line_ids', 'invoice_line_ids.is_landed_costs_line',
        'landed_costs_ids', 'landed_costs_ids.state',
        'x_picking_ids', 'x_picking_ids.state'
    )
    def _compute_landed_cost_state(self):
        for rec in self:
            if not any(rec.invoice_line_ids.mapped('is_landed_costs_line')) \
                    or any(picking_id.state != 'done' for picking_id in rec.x_picking_ids) or rec.type != 'in_invoice':
                rec.x_landed_cost_state = 'pending'
            elif any(rec.invoice_line_ids.mapped('is_landed_costs_line'))\
                    and not rec.landed_costs_ids\
                    and all(picking_id.state == 'done' for picking_id in rec.x_picking_ids):
                rec.x_landed_cost_state = 'blocked'
            elif any(rec.invoice_line_ids.mapped('is_landed_costs_line'))\
                    and any(state != 'done' for state in rec.landed_costs_ids.mapped('state'))\
                    and all(picking_id.state == 'done' for picking_id in rec.x_picking_ids):
                rec.x_landed_cost_state = 'normal'
            elif any(rec.invoice_line_ids.mapped('is_landed_costs_line'))\
                    and all(state == 'done' for state in rec.landed_costs_ids.mapped('state'))\
                    and all(picking_id.state == 'done' for picking_id in rec.x_picking_ids):
                rec.x_landed_cost_state = 'done'

    @api.depends('name', 'partner_id', 'ref', 'x_picking_ids')
    def _compute_folder_name(self):
        for rec in self:
            if rec.type not in ('in_invoice', 'out_invoice'):
                continue

            if rec.x_sale_order:
                rec.x_folder_name = '%s - %s' % (rec.x_sale_order.name, rec.name.replace('/', '-'))
            elif rec.x_related_invoice_ids:
                origin = ','.join(rec.x_related_invoice_ids.mapped('x_sale_order').mapped('name'))
                rec.x_folder_name = '%s - Related %s' % (origin, rec.name.replace('/', '-'))
            elif rec.x_picking_ids:
                origin = ','.join(rec.x_picking_ids.mapped('origin'))
                if any(is_landed_costs_line for is_landed_costs_line in rec.invoice_line_ids.mapped('is_landed_costs_line')):
                    rec.x_folder_name = '%s - LC %s' % (origin, rec.name.replace('/', '-'))
                else:
                    rec.x_folder_name = '%s - Related %s' % (origin, rec.name.replace('/', '-'))
            elif rec.purchase_id:
                rec.x_folder_name = '%s - %s' % (rec.purchase_id.name, rec.name.replace('/', '-'))
            elif rec.invoice_origin:
                rec.x_folder_name = '%s - %s' % (rec.invoice_origin.replace("['", '').replace("']", ''), rec.name.replace('/', '-'))
            else:
                rec.x_folder_name = rec.name.replace('/', '-')

            if rec.partner_id.parent_id:
                partner_name = rec.partner_id.parent_id.name.split(' ')[0]
                rec.x_folder_name += ' - %s - %s' % (partner_name, rec.partner_id.parent_id.country_id.name)
            elif rec.partner_id:
                partner_name = rec.partner_id.name.split(' ')[0]
                rec.x_folder_name += ' - %s - %s' % (partner_name, rec.partner_id.country_id.name)
            if rec.ref:
                rec.x_folder_name += ' - %s' % rec.ref

            rec.x_folder_name = rec.x_folder_name.replace('.', ',')

    @api.onchange('x_related_po_s', 'x_sale_ids')
    def update_picking_ids(self):
        for rec in self:
            rec.x_picking_ids = rec.x_related_po_s.mapped('picking_ids').ids or rec.x_sale_ids.mapped('picking_ids').ids

    @api.depends('x_picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.x_picking_count = len(rec.x_picking_ids)
            if rec.type == 'in_invoice':
                for picking in rec.x_picking_ids:
                    picking.x_bill_ids = [(4, rec.id)]

    def action_view_pickings(self):
        for rec in self:
            action = self.env.ref('cus_logistics_tracking.view_bill_related_pickings_action').read()[0]
            action['domain'] = [('id', 'in', rec.x_picking_ids.ids)]
            return action

    # def write(self, values):
    #     if values.get('x_picking_ids') is not None:
    #         old_values = self.x_picking_ids
    #
    #         try:
    #             new_values = self.env['stock.picking'].browse(values['x_picking_ids'][0][2])
    #         except IndexError:
    #             new_values = self.env['stock.picking'].browse([])
    #
    #         for val in old_values:
    #             if val.id not in new_values.ids:
    #                 val.x_bill_ids = [(3, self.id)]
    #
    #         for val in new_values:
    #             if val.id not in old_values.ids:
    #                 val.x_bill_ids = [(4, self.id)]
    #
    #     return super(AccountMove, self).write(values)

    def unlink(self):
        for rec in self:
            rec.x_picking_ids = []
        return super(AccountMove, self).unlink()
