# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Management for works',
    'version': '1.1',
    'category': 'Project Management',
    'sequence': 10,
    'summary': 'Projects, Works',
    'depends': ['base', 'project', 'con_client_code', 'sale', 'con_sale',
                'delivery'],
    'description':
    """
        Project Management for works
    """,
    'data': [
        'views/project.xml',
        'views/sale_order.xml',
        'views/municipality.xml',
        'wizard/views/project_product_available.xml',
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
