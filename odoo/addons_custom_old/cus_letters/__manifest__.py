# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Letter Reports',
    'version': '13.0.1.0.0',
    'summary': 'Letter Reports',
    'sequence': '10',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['base', 'note', 'sale', 'purchase'],
    'data': [
        'data/ir_sequence_data.xml',
        'reports/res_letter_report.xml',
        'reports/res_letter_report_templates.xml',
        'security/ir.model.access.csv',
        'views/letter_reports_views.xml',
        'views/menus.xml',
        'views/models_help_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
