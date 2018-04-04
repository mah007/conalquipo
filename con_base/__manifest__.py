# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Base module modifications',
    'version': '1.1',
    'category': 'Base',
    'sequence': 10,
    'summary': 'Base',
    'depends': [
        'base', 'delivery',
    ],
    'description':
    """
        Base module modification

        - res.partner: Adds client code.
        - res.partner: Extends l10n_co_document_type field to add NIT.
        - res.company: Adds Iso Logo.
        - res.company: Adds footer logo.
        - res.country.state: Adds colombian states.
        - res.country.municipality: Adds colombian municipalities.
    """,
    'data': [
        'data/res.country.state.csv',
        'data/res.country.municipality.csv',
        'sequences/client_sequence.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/res_country_municipality.xml',
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
