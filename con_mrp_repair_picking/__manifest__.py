# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Show mrp repairs option in stock picking',
    'version': '1.1',
    'category': 'MRP Repairs',
    'sequence': 10,
    'summary': 'MRP Repairs',
    'depends': [
        'mrp_repair'
    ],
    'description':
    """
        Show mrp repairs option in stock picking
    """,
    'data': [
        'views/stock_picking.xml',
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
