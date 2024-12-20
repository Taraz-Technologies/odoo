{
    'name': 'MRP Children',
    'version': '13.0.1.0.0',
    'summary': 'Odoo Custom Model',
    'sequence': '110',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'license': 'LGPL-3',
    'depends': [
        'cus_mrp_workorder',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
