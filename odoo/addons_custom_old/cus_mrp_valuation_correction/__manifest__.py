# -*- coding: utf-8 -*-

{
    'name': 'MPR Valuation Correction',
    'version': '13.0.1.0.0',
    'summary': 'MRP Valuation Error Detection & Correction',
    'sequence': '130',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['cus_mrp_kanban'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
