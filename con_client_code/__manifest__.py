# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Code for partners',
    'version': '1.1',
    'category': 'Partners',
    'sequence': 10,
    'summary': 'Partners',
    'depends': [
        'base'
    ],
    'description':
    """
        Assign code for partners
    """,
    'data': [
        'views/res_partner.xml',
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
