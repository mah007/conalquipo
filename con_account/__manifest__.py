# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account module modifications',
    'version': '1.1',
    'category': 'Account',
    'sequence': 10,
    'summary': 'Account',
    'depends': [
        'account',
    ],
    'description':
    """
        Account module modification

        - Adds sale_id field to signature.request model
    """,
    'data': [
        'views/account_invoice.xml'
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
