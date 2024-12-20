# -*- coding: utf-8 -*-

import requests
import lxml.html as lh
import datetime
from datetime import timedelta
from odoo import api, models, _
from odoo.exceptions import UserError


class ExchangeRate(models.Model):
    _name = 'exchange.rate'
    _description = 'Exchange Rate'

    @api.model
    def get_exchange_rate(self):
        url = 'https://www.urdupoint.com/business/foreign-exchange-rates-in-pakistan.html'
        # Create a handle, page, to handle the contents of the website
        page = requests.get(url)
        # Store the contents of the website under doc
        doc = lh.fromstring(page.content)
        # Parse data that are stored between <tr>..</tr> of HTML
        tr_elements = doc.xpath('//tr')
        usd_rate = 0
        eur_rate = 0
        gbp_rate = 0
        today_date = datetime.date.today()
        # USD Rate
        for tr_element in tr_elements:
            for cells in tr_element:
                if 'US Dollar' in cells.text_content():
                    for cell in tr_element:
                        usd_rate = cell.text_content()
                        if 'PKR' in usd_rate:
                            usd_rate = float(usd_rate.replace(' PKR', ''))
                            break
                    break

        currency = self.env['res.currency'].search([('id', '=', 165)])
        for record in currency:
            record.rate_ids = [(0, 0, {
                'name': today_date,
                'rate': usd_rate,
            })]
        # EUR Rate
        for tr_element in tr_elements:
            for cells in tr_element:
                if 'Euro' in cells.text_content():
                    for cell in tr_element:
                        eur_rate = cell.text_content()
                        if 'PKR' in eur_rate:
                            eur_rate = float(eur_rate.replace(' PKR', ''))
                            break
                    break

        eur_rate = round(usd_rate / eur_rate, 6) if usd_rate != 0 else eur_rate
        currency = self.env['res.currency'].search([('id', '=', 1)])
        for record in currency:
            record.rate_ids = [(0, 0, {
                'name': today_date,
                'rate': eur_rate,
            })]
        # GBP Rate
        for tr_element in tr_elements:
            for cells in tr_element:
                if 'UK Pound' in cells.text_content():
                    for cell in tr_element:
                        gbp_rate = cell.text_content()
                        if 'PKR' in gbp_rate:
                            gbp_rate = float(gbp_rate.replace(' PKR', ''))
                            break
                    break

        gbp_rate = round(usd_rate / gbp_rate, 6) if usd_rate != 0 else gbp_rate
        currency = self.env['res.currency'].search([('id', '=', 147)])
        for record in currency:
            record.rate_ids = [(0, 0, {
                'name': today_date,
                'rate': gbp_rate,
            })]

        if usd_rate == 0 or eur_rate == 0 or gbp_rate == 0:
            vals = {
                'priority': '1',
                'name': 'Date:' + str(today_date) + ': Currency Rate is not extracted today.',
                'project_id': 16,
                'user_id': 2,
                'x_start_task_on': today_date,
                'date_deadline': today_date,
                'x_user_participants': [17],
                'sequence': 0,
                'tag_ids': [self.env['project.tags'].search([('name', '=', 'Urgent')], limit=1).id],
            }
            task = self.env['project.task'].create(vals)
            task.x_user_stage_id = 231

        rates = self.env['res.currency.rate'].search([('currency_id', '=', 165)], limit=3).mapped('rate')
        rate = rates[0]
        check1 = True
        for item in rates:
            if rate != item:
                check1 = False
                break;

        rates = self.env['res.currency.rate'].search([('currency_id', '=', 1)], limit=3).mapped('rate')
        rate = rates[0]
        check2 = True
        for item in rates:
            if rate != item:
                check2 = False
                break;

        rates = self.env['res.currency.rate'].search([('currency_id', '=', 147)], limit=3).mapped('rate')
        rate = rates[0]
        check3 = True
        for item in rates:
            if rate != item:
                check3 = False
                break;

        if check1 or check2 or check3:
            vals = {
                'priority': '1',
                'name': 'Date:' + str(today_date) + ': Currency Rates are same for three days.',
                'project_id': 16,
                'user_id': 2,
                'x_start_task_on': today_date,
                'date_deadline': today_date,
                'x_user_participants': [17],
                'sequence': 0,
                'tag_ids': [self.env['project.tags'].search([('name', '=', 'Urgent')], limit=1).id],
            }
            task = self.env['project.task'].create(vals)
            task.x_user_stage_id = 231












