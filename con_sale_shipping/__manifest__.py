# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Conalequipo Sale Shipping',
    'version': '1.0',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': '',
    'description': """ Add Municipality.""",
    'depends': ['base_setup', 'base', 'delivery', 'sales_team', 'sale',
                'web_planner', 'mail', 'report'],
    'data': [
        'views/municipality.xml',
        'views/sale_order.xml',
        'views/vehicle.xml',
        'views/invoicing_area.xml'
    ],
    'demo': [''],
    'test': [''],
    'installable': True,
    'post_init_hook': '_auto_install_l10n',
}
