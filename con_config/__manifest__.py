# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Conalequipo Config',
    'version': '1.0',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': '',
    'description': """ Add Municipality.""",
    'depends': ['base', 'delivery', 'sales_team', 'sale'],
    'data': [
        'views/municipality.xml',
        'views/sale_order.xml'
    ],
    'demo': [''],
    'test': [''],
    'installable': True,
}
