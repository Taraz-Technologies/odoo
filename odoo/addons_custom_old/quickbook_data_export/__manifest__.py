# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'QuickBooks Data Export',
    'version': '13.0.1.0.0',
    'summary': 'Export Data for QuickBooks',
    'sequence': '40',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['customizations'],
    'data': [
        'security/ir.model.access.csv',
        'reports/reports.xml',
        'views/quickbooks_views.xml',
        'views/menus.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
