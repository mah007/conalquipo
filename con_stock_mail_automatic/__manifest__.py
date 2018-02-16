# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock moves email notifications',
    'version': '1.1',
    'category': 'Stock',
    'sequence': 10,
    'summary': 'Stock',
    'depends': [
        'stock', 'mail', 'contacts', 'delivery'
    ],
    'description':
    """
        Stock moves email notifications
    """,
    'data': [
        'views/email_template.xml',
        'views/cron_template.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
