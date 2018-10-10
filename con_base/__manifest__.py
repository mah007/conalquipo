# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Conalquipo's Base module modifications",
    'version': '1.1',
    'category': 'Base',
    'sequence': 10,
    'summary': 'Base',
    'depends': [
        'base', 'sale', 'l10n_co_topology'
    ],
    'description':
    """
        Base module modification

        - res.country.sectors: Adds colommbian sectors.
    """,
    'data': [
        'sequences/client_sequence.xml',
        'security/ir.model.access.csv',
        'data/module_category.xml',
        'data/res_company_data.xml',
        'data/messages.xml',
        'data/groups.xml',
        'data/res_lang_data.xml',
        'data/res_users.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/res_users.xml',
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
