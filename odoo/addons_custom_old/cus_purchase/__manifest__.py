# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Purchase Customizations',
    'version': '13.0.1.0.0',
    'summary': 'Odoo Custom Model',
    'sequence': '80',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['cus_logistics_tracking'],
    'data': [
        'security/ir.model.access.csv',
        'reports/purchase_quotation_templates.xml',
        'reports/reports.xml',
        'views/purchase_views.xml',
        'wizards/add_bulk_tagging.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
