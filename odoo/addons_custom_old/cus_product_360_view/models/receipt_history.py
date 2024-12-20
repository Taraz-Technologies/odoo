from odoo import api, fields, models
import logging

_logger = logging.getLogger("*__addons_custom__*")


class ReceiptHistory(models.Model):
    _name = "receipt.history"
    _description = "Receipt History"
    _rec_name = "x_product_id"

    x_purchase_history_id = fields.Many2one(comodel_name='purchase.history', string='Purchase History')
    x_order_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')
    x_receipt_id = fields.Many2one(comodel_name='stock.picking', string='Receipt', required=False)
    x_receipt_date = fields.Date(string='Receipt Date')

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_received_qty = fields.Float(string='Received', required=False)
    x_product_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM')


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_receipt_history_id = fields.Many2one(comodel_name='receipt.history', string='Receipt History',
                                           required=False, compute="update_receipt_history", store=True)

    @api.depends('picking_id.state', 'picking_id.scheduled_date', 'picking_id.date_done', 'picking_id.note',
                 'product_id', 'quantity_done', 'product_uom')
    def update_receipt_history(self):
        for rec in self:
            if rec.picking_id.picking_type_code != 'incoming':
                return
            elif rec.state == 'cancel' and rec.x_receipt_history_id:
                rec.x_receipt_history_id.unlink()
            elif rec.state != 'cancel' and rec.purchase_line_id and rec.picking_id:
                rec.purchase_line_id.update_purchase_history()
                receipt_date = rec.picking_id.scheduled_date.date() if rec.picking_id.scheduled_date else False
                receipt_date = rec.picking_id.date_done.date() if rec.picking_id.date_done else receipt_date
                vals = {
                    'x_order_id': rec.purchase_line_id.order_id.id,
                    'x_receipt_id': rec.picking_id.id,
                    'x_receipt_date': receipt_date,
                    'x_product_id': rec.purchase_line_id.product_id.product_tmpl_id.id,
                    'x_received_qty': rec.quantity_done if 'WH/IN/' in rec.picking_id.name else -rec.quantity_done,
                    'x_product_uom_id': rec.product_uom.id,
                }
                if rec.x_receipt_history_id:
                    rec.x_receipt_history_id.update(vals)
                else:
                    rec.x_receipt_history_id = self.env['receipt.history'].create(vals)
                if rec.purchase_line_id.x_purchase_history_id:
                    purchase_history_id = rec.purchase_line_id.x_purchase_history_id
                    purchase_history_id.x_receipt_history_ids = [(4, rec.x_receipt_history_id.id)]

    def _action_cancel(self):
        self.x_receipt_history_id.unlink()
        return super(StockMove, self)._action_cancel()

    def unlink(self):
        self.x_receipt_history_id.unlink()
        return super(StockMove, self).unlink()
