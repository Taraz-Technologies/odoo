{
    'name': 'Repair Customizations',
    'version': '13.0.1.0.0',
    'summary': 'Odoo Custom Model',
    'sequence': '10',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['sale', 'repair'],
    'data': [
        'views/repair_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}