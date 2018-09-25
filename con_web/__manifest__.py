# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Web module modifications',
    'version': '1.1',
    'category': 'Web',
    'sequence': 10,
    'summary': 'Web',
    'depends': [
        'web'
    ],
    'description':
    """
        Web module modification
        
        - Adds css modifications to the backend
    """,
    'data': [
        'views/webclient_templates.xml',
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
