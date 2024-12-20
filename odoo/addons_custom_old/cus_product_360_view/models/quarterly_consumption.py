from odoo import api, fields, models
import datetime


class QuarterlyConsumption(models.Model):
    _name = "quarterly.consumption"
    _description = "Quarterly Consumption"
    _rec_name = "x_product_id"
    _order = "x_quarter"

    x_product_id = fields.Many2one(comodel_name='product.template', string='Product')
    x_date = fields.Date(string='Date', required=False)
    x_date_from = fields.Date(string='Date From', compute='_compute_quarter_data', store=True)
    x_date_to = fields.Date(string='Date To', compute='_compute_quarter_data', store=True)
    x_quarter = fields.Char(string='Quarter', compute='_compute_quarter_data', store=True)
    x_quantity = fields.Float(
        string="Consumed Quantity", digits=(12, 4), compute='_compute_quarter_data', store=True
    )
    x_consumption_history_ids = fields.Many2many(
        comodel_name='manufacturing.history', string='Consumption History', compute='_compute_quarter_data', store=True
    )
    x_scrap_history_ids = fields.Many2many(
        comodel_name='stock.scrap', string='Scrap History', compute='_compute_quarter_data', store=True
    )
    x_sale_order_history_ids = fields.Many2many(
        comodel_name='sale.history', string='Sale History', compute='_compute_quarter_data', store=True
    )

    @api.depends('x_date')
    def _compute_quarter_data(self):
        for rec in self:
            rec.x_quarter, rec.x_date_from, rec.x_date_to = rec.compute_quarter(rec.x_date)

            consumption_history_ids = []
            scrap_history_ids = []
            sale_order_history_ids = []
            if rec.x_date_from and rec.x_date_to:
                consumption_history_ids = rec.x_product_id.x_consumption_history_ids.filtered(
                    lambda c: rec.x_date_from <= c.x_date <= rec.x_date_to
                ).ids
                scrap_history_ids = rec.x_product_id.x_scrap_history_ids.filtered(lambda s: s.date_done).filtered(
                    lambda s: rec.x_date_from <= s.date_done.date() <= rec.x_date_to
                ).ids
                sale_order_history_ids = rec.x_product_id.x_sale_order_history_ids.filtered(
                    lambda s: rec.x_date_from <= s.x_order_date <= rec.x_date_to
                ).ids

            rec.x_consumption_history_ids = [(6, 0, consumption_history_ids)]
            rec.x_scrap_history_ids = [(6, 0, scrap_history_ids)]
            rec.x_sale_order_history_ids = [(6, 0, sale_order_history_ids)]

            quantity = sum(rec.x_consumption_history_ids.mapped('x_quantity_done'))
            quantity += sum(rec.x_scrap_history_ids.mapped('scrap_qty'))
            quantity += sum(rec.x_sale_order_history_ids.mapped('x_qty_delivered'))
            rec.x_quantity = quantity

    def compute_quarter(self, date):
        if not date:
            return [False, False, False]
        month = int(date.strftime('%m'))
        year = int(date.strftime('%Y'))
        quarter = date.strftime('%Y')
        date_from = False
        date_to = False
        if 1 <= month <= 3:
            quarter += ' Q1'
            date_from = datetime.date(year, 1, 1)
            date_to = datetime.date(year, 3, 31)
        elif 4 <= month <= 6:
            quarter += ' Q2'
            date_from = datetime.date(year, 4, 1)
            date_to = datetime.date(year, 6, 30)
        elif 7 <= month <= 9:
            quarter += ' Q3'
            date_from = datetime.date(year, 7, 1)
            date_to = datetime.date(year, 9, 30)
        elif 10 <= month <= 12:
            quarter += ' Q4'
            date_from = datetime.date(year, 10, 1)
            date_to = datetime.date(year, 12, 31)
        return [quarter, date_from, date_to]



