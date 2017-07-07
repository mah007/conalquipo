# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 Tiny SPRL (<http://www.ias.com.co>).
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
    'name': 'Product availability',
    'version': '1.1',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': 'Products',
    'sequence': 10,
    'summary': 'Adds custom states to products that'
               ' can be changed at specific times of the workflow.',
    'depends': [
        'base', 'stock', 'product', 'mrp', 'sale', 'purchase'
    ],
    'description':
    """
        Adds custom states to products that can be changed
         at specific times of the workflow.
    """,
    'data': [
        'views/product.xml',
        'views/product_states.xml',
        'views/stock_location.xml',
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
