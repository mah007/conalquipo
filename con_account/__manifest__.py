# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account module modifications',
    'version': '1.1',
    'category': 'Account',
    'sequence': 10,
    'summary': 'Account',
    'depends': [
        'account', 'account_accountant', 'account_asset', 'project', 'sale',
    ],
    'description':
    """
        Account module modification

        - Adds owner_id, bill_uom, qty_shipped field to account.invoice model.
        - Adds project_id, invoice_type field to account.invoice.line model.
    """,
    'data': [
        'views/account_invoice.xml',
        'views/account_invoice_period.xml',
        'report/report_invoice_inherit.xml',
        'wizards/views/account_invoice_state.xml',
        'data/account_payment_term.xml',
        'data/account_reconcile_model.xml',
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
