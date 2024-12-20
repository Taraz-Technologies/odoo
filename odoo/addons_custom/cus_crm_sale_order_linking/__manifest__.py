# -*- coding: utf-8 -*-

{
    'name': 'CRM - SO (Linking)',
    'version': '13.0.1.0.0',
    'summary': 'CRM & Sale Order two way linking',
    'sequence': '40',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['customizations'],
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
