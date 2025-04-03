# -*- coding: utf-8 -*-
{
    'name': 'Platform Service Inventory',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'PS Inventory details - Chewy/ Yoda',
    'author': 'Omprakash Zeabalane',
    'website': 'http://www.yourcompany.com',
    'depends': ['base','mail'],  # List of dependencies (e.g., base, sale, stock, etc.)
    'data': [
        'security/ir.model.access.csv',
        'views/ps_inventory_view.xml',
        'views/ps_inventory_users_view.xml',
        'views/ps_login_templates_view.xml'
        # 'views/ps_inventory_remove.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'ps_inventory/static/src/**/*',
        ]
    },
    'installable': True,
    'application': True,  # Set True if it's an app to be listed in the Apps menu
    'auto_install': False,
    'license': 'LGPL-3',
}
