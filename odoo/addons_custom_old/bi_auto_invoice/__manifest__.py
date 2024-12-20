# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
	'name': 'Auto Invoice from Picking(Shipment/Delivery)',
	'version': '13.0.1.0',
	'category': 'Accounting',
	'summary': 'App Automatic invoice from picking Automatic invoice from delivery order Automatic invoice from shipment auto invoice on received products auto invoice on received goods auto invoice from delivery auto invoice validate from picking auto invoice from DO',
	'description': """
	odoo Automatic invoice from picking Automatic invoice from delivery order Automatic invoice from shipment
	odoo picking invoice invoice picking odoo invoice from picking odoo picking from invoice
	odoo invoice generation when picking get done create invoice from picking invoice created when picking done
	odoo auto invoice creation when stock transffered Auto invoice generation from picking
	odoo Auto delivery invoice Auto invoice delivery order Auto invoice generation when delivery get done
	odoo Auto create invoice from delivery order Auto invoice created when delivery done auto invoice creation when delivery transffered.
	odoo Auto invoice generation from delivery order Auto delivery order invoice Auto invoice generation when delivery order get done
	Auto invoice created when delivery order done auto invoice creation when delivery order transffered.
	odoo Auto shipment invoice Auto invoice shipment order Auto invoice generation when shipment get done Auto create invoice from shipment order
	odoo Auto invoice created when shipment done auto invoice creation when shipment transffered Auto invoice generation from shipment order
	odoo Auto incoming shipment order invoice Auto invoice generation when shipment order get done 
	odoo Auto invoice created when shipment order done auto invoice creation when shipment order transffered.
	odoo automatic invoice creation from delivery order odoo automatic invoice creation from picking automatic invoice validate from delivery order
	odoo automatic invoice validate from picking automatic invoice send from delivery order automatic invoice send from picking
	automatic invoice create and validate from delivery order automatic invoice create and validate from picking auto invoice create and validate from delivery order 
	autoinvoice validate and send from picking automatic invoice validate send from delivery order automatic invoice generate and send from picking

This app automatically create invoice when Receive the Products
This odoo apps automatically create invoice from Picking when picking(Shipment/Delivery) get Done. This module also comes with multiple configuration option 
i.e Auto Validate invoice from Picking Auto send invoice by Email when Picking Done. 
Whenever Delivery order or picking will done this module create customer invoice/vendor bills automatically same as sales and purchase order product price with delivered and received quantity. 
If you activate auto validate option then when delivery/shipment get done its automatically creates customer/supplier invoice and validate it automatically. Same for send by email option, 
If you activate Send by Email option then when delivery/shipment get done its automatically creates customer/supplier invoice and Send it same as send by email funcation. 
User can have option to activate both option together and in this case when picking will become done it will create invoice , validate it and send it to customer/supplier.
     odoo invoice on goods invoice on received products invoice on received goods create invoice goods
     odoo auto invoice on received products auto invoice on received goods create invoice goods odoo auto invoice on recieved product 

""",
	'author': 'BrowseInfo',
	'website': 'https://www.browseinfo.in',
	'price': 35.00,
	'currency': "EUR",
	'depends': ['sale_management','purchase','stock',],
	'data': [
				'views/inherited_account_invoice.xml',
				'views/inherited_stock_picking.xml',
				'views/res_config_inherit.xml',
			],
	'demo': [],
	'js': [],
	'qweb': [],
	'installable': True,
	'auto_install': False,
	"images":['static/description/Banner.png'],
	'live_test_url':'https://youtu.be/X_89VH6BkZ4',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: