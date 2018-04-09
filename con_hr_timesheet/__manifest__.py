# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Conalquipo HR Timesheet',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'HR',
    'sequence': 10,
    'summary': 'HR',
    'depends': ['timesheet_grid', 'product'],
    'description':
    """
        HR Timesheet customizations.
        
        - Add product uom to timesheet.
    """,
    'data': ['views/hr_timesheet.xml',
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
