# -*- coding: utf-8 -*-

{
    'name': 'Exchange Rate',
    'version': '13.0.1.0.0',
    'summary': 'USD to PKR: Exchange Rate',
    'category': 'Currency',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['base', 'account', 'mail', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
