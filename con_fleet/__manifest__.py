# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo Fleet customizations',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'Fleet',
    'sequence': 10,
    'summary': 'Fleet',
    'depends': ['con_base', 'fleet', 'stock'],
    'description':
    """
        Conalquipo Fleet customizations
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle.xml',
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
