# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Delivery module modifications',
    'version': '1.1',
    'category': 'Delivery',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': [
        'l10n_co_topology', 'delivery', 'stock',
    ],
    'description':
    """
        Delivery module modification

        - Adds municipality_ids modifications to the delivery.carrier model
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/delivery.xml',
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
