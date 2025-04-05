# -*- coding: utf-8 -*-
{
    'name': 'Platform Service Inventory',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'PS Inventory details - Chewy/ Yoda and SSD Drives',
    'author': 'Omprakash Zeabalane',
    'website': 'http://www.yourcompany.com',
    'depends': ['base','mail'],  # List of dependencies (e.g., base, sale, stock, etc.)
    'data': [
        'security/ir.model.access.csv',
        'views/ps_inventory_hosts_view.xml',
        'views/ps_inventory_drives_view.xml',
        'views/ps_login_templates_view.xml',
        'views/ps_inventory_remove_signup.xml',
        'views/ps_inventory_users_view.xml',
        'data/ps_inventory_remove_menu.xml',
        'views/ps_inventory_menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'ps_inventory/static/src/**/*',
        ]
    },
    'icon': '/ps_inventory/static/src/img/PS.jpg', 
    'installable': True,
    'application': True,  # Set True if it's an app to be listed in the Apps menu
    'auto_install': False,
    'license': 'LGPL-3',
}
