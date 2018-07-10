# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account module modifications',
    'version': '1.1',
    'category': 'Account',
    'sequence': 10,
    'summary': 'Account',
    'depends': [
        'account', 'project', 'con_base',
    ],
    'description':
    """
        Account module modification

        - Adds owner_id, bill_uom, qty_shipped field to account.invoice model.
        - Adds project_id, invoice_type field to account.invoice.line model.
    """,
    'data': [
        'views/account_invoice.xml',
        'report/report_invoice_inherit.xml',
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
