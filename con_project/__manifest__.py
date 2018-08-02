# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo Project customizations',
    'version': '1.1',
    'category': 'Project Management',
    'sequence': 10,
    'summary': 'Projects, Works',
    'depends': ['con_base', 'project', 'sale',
                'delivery', 'hr_timesheet', 'stock'],
    'description':
    """
        Project Management for works
    """,
    'data': [
        'views/project.xml',
        'views/project_task.xml',
        'wizards/views/project_product_available.xml',
        'reports/project_product_report.xml',
        'data/email_template.xml',
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
