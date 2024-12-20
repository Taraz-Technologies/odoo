# -*- coding: utf-8 -*-

{
    'name': 'OctoPart Connector',
    'version': '13.0.1.0.0',
    'summary': 'OctoPart Connector',
    'sequence': '10',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/octopart_connector.xml',
        'views/octopart_settings_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
