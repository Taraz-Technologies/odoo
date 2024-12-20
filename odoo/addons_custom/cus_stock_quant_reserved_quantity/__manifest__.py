{
    'name': 'Stock Quant Reserved Quantity',
    'version': '13.0.1.0.0',
    'summary': 'Adds button in stock quant to update reserved quantity',
    'sequence': '10',
    'category': 'Customization',
    'author': 'Taraz Technologies Pvt. Ltd.',
    'maintainer': 'Taraz Technologies Pvt. Ltd.',
    'company': 'Taraz Technologies Pvt. Ltd.',
    'website': 'https://www.taraztechnologies.com/',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_quant_views.xml',
        'wizards/stock_quant_reserved_quantity_views.xml',
    ],
    'installable': True,
}
