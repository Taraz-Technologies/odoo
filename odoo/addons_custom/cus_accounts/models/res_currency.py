import datetime

from odoo import fields, models, api
from odoo.exceptions import UserError

import requests
import urllib3
import ssl
import json

from datetime import date, timedelta
from datetime import datetime


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    x_rate_buying = fields.Float(string="Buying", digits=0, default=1.0,
                                 help='The rate of the currency to the currency of rate 1')
    x_rate_selling = fields.Float(string="Selling", digits=0, default=1.0,
                                  help='The rate of the currency to the currency of rate 1')

    @api.onchange('name')
    def get_turkey_currency_rate(self):
        for rec in self:
            if rec.company_id.id != 2:
                return
            currency_date = rec.name.strftime("%d-%m-%Y")
            data_type = 'json'
            key = 'ITaJ8L7zgZ'
            headers = {'key': key}
            aggregationTypes = 'last'
            formulas = 0
            frequency = 1

            # USD Currency Rate
            series = 'TP.DK.USD.A.YTL'
            url = "https://evds2.tcmb.gov.tr/service/evds/" \
                  "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                  % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
            response = requests.get(url=url, headers=headers)
            rates = json.loads(response.content)
            usd_buying_value = float(rates['items'][0][series.replace('.', '_')])

            series = 'TP.DK.USD.S.YTL'
            url = "https://evds2.tcmb.gov.tr/service/evds/" \
                  "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                  % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
            response = requests.get(url=url, headers=headers)
            rates = json.loads(response.content)
            usd_selling_value = float(rates['items'][0][series.replace('.', '_')])

            if rec.currency_id.id == self.env.ref('base.TRY').id:
                rec.rate = usd_selling_value
                rec.x_rate_buying = usd_buying_value
                rec.x_rate_selling = usd_selling_value

            # EUR Currency Rate
            if rec.currency_id.id == self.env.ref('base.EUR').id:
                series = 'TP.DK.EUR.A.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                eur_buying_value = float(rates['items'][0][series.replace('.', '_')])

                series = 'TP.DK.EUR.S.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                eur_selling_value = float(rates['items'][0][series.replace('.', '_')])

                rec.rate = usd_selling_value / eur_selling_value
                rec.x_rate_buying = usd_buying_value / eur_buying_value
                rec.x_rate_selling = usd_selling_value / eur_selling_value

            # GBP Currency Rate
            if rec.currency_id.id == self.env.ref('base.GBP').id:
                series = 'TP.DK.GBP.A.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                gbp_buying_value = float(rates['items'][0][series.replace('.', '_')])

                series = 'TP.DK.GBP.S.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                gbp_selling_value = float(rates['items'][0][series.replace('.', '_')])

                rec.rate = usd_selling_value / gbp_selling_value
                rec.x_rate_buying = usd_buying_value / gbp_buying_value
                rec.x_rate_selling = usd_selling_value / gbp_selling_value

            # PKR Currency Rate
            if rec.currency_id.id == self.env.ref('base.PKR').id:
                series = 'TP.DK.PKR.A.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                pkr_buying_value = float(rates['items'][0][series.replace('.', '_')])

                series = 'TP.DK.PKR.S.YTL'
                url = "https://evds2.tcmb.gov.tr/service/evds/" \
                      "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
                      % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
                response = requests.get(url=url, headers=headers)
                rates = json.loads(response.content)
                pkr_selling_value = float(rates['items'][0][series.replace('.', '_')])

                rec.rate = usd_selling_value / pkr_selling_value
                rec.x_rate_buying = usd_buying_value / pkr_buying_value
                rec.x_rate_selling = usd_selling_value / pkr_selling_value

    @api.model
    def get_turkey_exchange_rates(self):
        currency_rate_date = date.today() + timedelta(days=1)
        currency_date = currency_rate_date.strftime("%d-%m-%Y")
        data_type = 'json'
        key = 'ITaJ8L7zgZ'
        headers = {'key': key}
        aggregationTypes = 'last'
        formulas = 0
        frequency = 1

        # USD Currency Rate
        series = 'TP.DK.USD.A.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        usd_buying_value = float(rates['items'][0][series.replace('.', '_')])

        series = 'TP.DK.USD.S.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        usd_selling_value = float(rates['items'][0][series.replace('.', '_')])

        # EUR Currency Rate
        series = 'TP.DK.EUR.A.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        eur_buying_value = float(rates['items'][0][series.replace('.', '_')])

        series = 'TP.DK.EUR.S.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        eur_selling_value = float(rates['items'][0][series.replace('.', '_')])

        # GBP Currency Rate
        series = 'TP.DK.GBP.A.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        gbp_buying_value = float(rates['items'][0][series.replace('.', '_')])

        series = 'TP.DK.GBP.S.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        gbp_selling_value = float(rates['items'][0][series.replace('.', '_')])

        # PKR Currency Rate
        series = 'TP.DK.PKR.A.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        pkr_buying_value = float(rates['items'][0][series.replace('.', '_')])

        series = 'TP.DK.PKR.S.YTL'
        url = "https://evds2.tcmb.gov.tr/service/evds/" \
              "series=%s&startDate=%s&endDate=%s&type=%s&aggregationTypes=%s&formulas=%s&frequency=%s" \
              % (series, currency_date, currency_date, data_type, aggregationTypes, formulas, frequency)
        response = requests.get(url=url, headers=headers)
        rates = json.loads(response.content)
        pkr_selling_value = float(rates['items'][0][series.replace('.', '_')])

        self.env['res.currency.rate'].create([{
            'currency_id': self.env.ref('base.EUR').id,
            'rate': usd_selling_value / eur_selling_value,
            'x_rate_buying': usd_buying_value / eur_buying_value,
            'x_rate_selling': usd_selling_value / eur_selling_value,
            'name': currency_rate_date,
            'company_id': 2,
        }, {
            'currency_id': self.env.ref('base.GBP').id,
            'rate': usd_selling_value / gbp_selling_value,
            'x_rate_buying': usd_buying_value / gbp_buying_value,
            'x_rate_selling': usd_selling_value / gbp_selling_value,
            'name': currency_rate_date,
            'company_id': 2,
        }, {
            'currency_id': self.env.ref('base.PKR').id,
            'rate': usd_selling_value / pkr_selling_value,
            'x_rate_buying': usd_buying_value / pkr_buying_value,
            'x_rate_selling': usd_selling_value / pkr_selling_value,
            'name': currency_rate_date,
            'company_id': 2,
        }, {
            'currency_id': self.env.ref('base.TRY').id,
            'rate': usd_selling_value,
            'x_rate_buying': usd_buying_value,
            'x_rate_selling': usd_selling_value,
            'name': currency_rate_date,
            'company_id': 2,
        }])
