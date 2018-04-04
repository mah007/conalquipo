# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Delivery module modifications',
    'version': '1.1',
    'category': 'Delivery',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': [
        'delivery', 'con_base'
    ],
    'description':
    """
        Delivery module modification

        - Adds municipality_ids modifications to the delivery.carrier model
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
