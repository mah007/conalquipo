# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2018 IAS Ingenieria, Aplicaciones y Software, S.A.S.
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
    'name': 'Show mrp repairs option in stock move',
    'version': '1.1',
    'category': 'MRP Repairs',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'sequence': 10,
    'summary': 'MRP Repairs',
    'depends': [
        'stock', 'mrp_repair'
    ],
    'description':
    """
        Show mrp repairs option in stock move
    """,
    'data': [
        'views/stock_picking.xml',
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
