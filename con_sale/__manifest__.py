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
    'name': 'Conalequipo Sale Customization',
    'version': '1.0',
    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'category': '',
    'description': """ Add field for Municipality and delivery cost in the
    sale order.""",
    'depends': ['base', 'sales_team', 'sale', 'website_quote', 'stock',
                'delivery', 'con_product', 'con_account',
                'con_project', 'con_website_sign', 'con_fleet'],
    'data': ['views/sale_order_view.xml',
             'wizard/views/sale_order_advertisement_wizard.xml'
            ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
