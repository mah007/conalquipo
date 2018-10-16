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
        'crm', 'project', 'purchase', 'repair', 'delivery',
        'fleet', 'web_grid', 'sale_timesheet', 'hr_contract', 'sign', 'repair',
        'l10n_co_edi', 'l10n_co_reports', 'website',
        # Community addons
        'stock_real_availability', 'web_export_view',
        'web_widget_color', 'report_qweb_element_page_visibility',
        'partner_firstname',
        # IAS's addons
        'l10n_co_topology',
        # Conalquipo's addons
        'con_web',
        'con_repair',
        'con_fleet',
        'con_delivery',
        'con_hr',
        'con_hr_timesheet',
        'con_sign',
        'con_base',
        'con_purchase',
        # Check
        'con_stock',
        'con_product',
        'con_sale',
        'con_project',
        'con_account',
    ],
    'data': [],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
