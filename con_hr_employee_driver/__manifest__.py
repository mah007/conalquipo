# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo HR Employee Driver',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'HR',
    'sequence': 10,
    'summary': 'HR',
    'depends': ['hr', 'hr_contract', 'fleet'],
    'description':
    """
        Work information for shipping.
    """,
    'data': ['views/hr_employee_driver.xml',
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
