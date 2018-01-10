# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'BOM on Invoice Report',
    'category': 'Warehouse',
    'summary': 'Module to display the BOM products & serial number on the invoice report',
    'website': 'www.niboo.be',
    'version': '10.0.1.0',
    'description': """
- Display the BOM products on the invoice report
        """,
    'author': 'Niboo',
    'depends': [
        'account',
        'stock',
    ],
    'data': [
        'views/report_invoice.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'application': False,
}
