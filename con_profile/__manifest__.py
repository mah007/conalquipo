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
    'name': "Odoo CON Profile",

    'summary': """
        Conalequipos's Odoo Installation profile.
    """,

    'description': """
        Conalequipo's Odoo Installation profile.
    """,

    'author': 'IAS Ingenieria, Aplicaciones y Software, S.A.S',
    'website': "http://www.ias.com.co",
    'category': 'Base Profile',
    'version': '0.1',
    'depends': [
        # Odoo's addons
        'base', 'crm', 'project', 'document', 'sale', 'purchase',
        'stock', 'account', 'repair', 'delivery', 'fleet',
        'web_grid', 'hr_timesheet', 'l10n_co', 'l10n_co_edi',
        'l10n_co_reports', 'sale_timesheet', 'hr_contract',
        # Community addons
        'stock_real_availability', 'web_export_view',
        'web_widget_color', 'report_qweb_element_page_visibility',
        'partner_firstname',
        # Conalquipo's addons
        'con_base',
        'con_web',
        'con_product',
        'con_stock',
        'con_hr',
        'con_hr_timesheet',
        'con_sign',
        'con_purchase',
        'con_repair',
        'con_delivery',
        'con_fleet',
    ],
    'data': [],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
