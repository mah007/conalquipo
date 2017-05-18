# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Shipping',
    'version': '1.1',
    'category': 'Sale',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': ['base_setup', 'base', 'delivery', 'fleet', 'mail'],
    'description':
    """
        Work information for shipping.
    """,
    'data': ['views/shipping.xml'],
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
