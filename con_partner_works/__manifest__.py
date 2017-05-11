# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner works',
    'version': '1.1',
    'category': 'Partners',
    'sequence': 10,
    'summary': 'Partners, Works',
    'depends': ['base'],
    'description':
    """
        Work information for partners\n
        Extend the class partner and added new fields for work information
        and country address format.
    """,
    'data': [
        'views/res_partner.xml',
        'views/municipality.xml',
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
