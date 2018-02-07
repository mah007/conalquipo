# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo Purchase Customizations',
    'version': '1.1',
    'category': 'Purchase',
    'sequence': 10,
    'summary': 'Purchase, Stock',
    'depends': ['base', 'purchase', 'stock', 'con_client_code', 'sale',
                'con_sale',
                'delivery'],
    'description':
    """
        Customizations for conalquipo purchase process.
    """,
    'data': [
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
