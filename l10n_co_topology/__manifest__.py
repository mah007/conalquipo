# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Colombia topology (Municipalities and sectors",
    'version': '1.1',
    'category': 'Base',
    'sequence': 10,
    'summary': 'Base',
    'depends': [
        'base',
    ],
    'description':
    """
        Base module modification

        - res.country.municipality: Adds colommbian municipalities.
        - res.country.sectors: Adds colommbian sectors.
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/res.country.municipality.csv',
        'data/sectors.xml',
        'views/res_country_municipality.xml',
        'views/res_country_sector.xml',
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
