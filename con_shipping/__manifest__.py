# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Shipping',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'Sale',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': ['base', 'con_delivery', 'fleet', 'mail', 'stock',
                'con_project', 'con_stock', 'hr_contract', 'project', 'web'],
    'description':
    """
        Work information for shipping.
    """,
    'data': [
        'data/module_category.xml',
        'data/groups.xml',
        'views/shipping.xml',
        'reports/report_stockpicking.xml',
        'wizard/views/stock_picking_cancel_wizard.xml',
        'wizard/views/stock_picking_equipment_change_wizard.xml',
        'views/shipping_templates.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
