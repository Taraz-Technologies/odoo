# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Quality',
    'version': '13.0.1.0.0',
    'summary': 'Product Quality Control',
    'sequence': '100',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['cus_production_planner'],
    'data': [
        'security/ir.model.access.csv',
        'views/quality_control_view.xml',
        'views/serial_products_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
