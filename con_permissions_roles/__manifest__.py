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
    'name': "Odoo CON permissions and roles",

    'summary': """
        Conalequipos's Odoo permissions and roles.
    """,

    'description': """
        Conalequipo's Odoo permissions and roles.
    """,

    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'website': "http://www.ias.com.co",
    'category': 'Security',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'data/module_category.xml',
        'data/groups.xml'
    ],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
