# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Management for works',
    'version': '1.1',
    'category': 'Project Management',
    'sequence': 10,
    'summary': 'Projects, Works',
    'depends': ['con_base', 'con_delivery', 'project', 'sale', 'con_sale',
                'delivery'],
    'description':
    """
        Project Management for works
    """,
    'data': [
        'views/project.xml',
        'views/sale_order.xml',
        'wizards/views/project_product_available.xml',
        'reports/project_product_report.xml',
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
