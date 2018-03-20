# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2017 IAS Ingenieria, Aplicaciones y Software, S.A.S.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Set massive location and colors wizard',
    'version': '1.1',
    'category': 'Product',
    'sequence': 10,
    'summary': 'Product',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'depends': [
        'stock', 'con_product', 'web_widget_color'
    ],
    'description': """
        Set massive location and colors wizard
    """,
    'data': [
        'wizards/set_location_wizard.xml',
        'views/stock.xml',
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
