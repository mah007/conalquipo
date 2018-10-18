# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo Project customizations',
    'version': '1.1',
    'category': 'Project Management',
    'sequence': 10,
    'summary': 'Projects, Works',
    'depends': ['con_base', 'project', 'sale', 'con_stock', 'delivery',
                'hr_timesheet', 'con_account'],
    'description':
    """
        Project Management for works
    """,
    'data': [
        'data/email_template.xml',
        'wizards/views/project_product_available.xml',
        'views/project.xml',
        'views/project_task.xml',
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
