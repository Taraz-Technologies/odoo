# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Scrum Methodology',
    'version': '13.0.1.0.0',
    'summary': 'Scrum Methodology: An Agile Way of Managing Software Development',
    'sequence': '10',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'data/scrum_task_stages.xml',
        'data/scrum_project_stages.xml',
        'views/scrum_task_views.xml',
        'views/scrum_project_views.xml',
        'views/menus.xml',
    ],
    'images': ['static/images/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
