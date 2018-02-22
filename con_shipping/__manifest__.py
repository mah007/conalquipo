# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Shipping',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'Sale',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': ['base', 'delivery', 'fleet', 'mail', 'stock',
                'con_project_works', 'hr_contract', 'project'],
    'description':
    """
        Work information for shipping.
    """,
    'data': [
        'data/module_category.xml',
        'data/groups.xml',
        'views/shipping.xml',
        'reports/report_stockpicking.xml',
        'wizard/views/stock_picking_cancel_wizard.xml'
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
