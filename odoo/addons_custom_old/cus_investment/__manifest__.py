# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Investment',
    'version': '13.0.1.0.0',
    'summary': 'Investment Tracking',
    'sequence': '40',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['customizations'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/investment_return_views.xml',
        'views/investment_views.xml',
        'views/investor_views.xml',
        'views/menus.xml',
        'views/product_views.xml',
        'wizard/adjustment_wizard_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
