# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Shipping',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'Sale',
    'sequence': 10,
    'summary': 'Delivery',
    'depends': ['base_setup', 'base', 'delivery', 'fleet', 'mail',
                'stock'],
    'description':
    """
        Work information for shipping.
    """,
    'data': ['views/shipping.xml',
             'reports/report_stockpicking.xml'
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
