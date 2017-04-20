# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Show projects customers',
    'version': '1.1',
    'category': 'Partners',
    'sequence': 10,
    'summary': 'Show projects customers',
    'depends': [
        'base', 'project',
    ],
    'description':
    """
        Show projects customers
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
