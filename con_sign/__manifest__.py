# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website sign module modifications',
    'version': '1.1',
    'category': 'Website sign',
    'sequence': 10,
    'summary': 'Website sign',
    'depends': [
        'sign', 'sale'
    ],
    'description':
    """
        Website sign module modification

        - Adds sale_id field to signature.request model
    """,
    'data': [
        'data/sign_template_data.xml',
        'views/sign_request.xml'
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
