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
    'depends': [# Odoo's addons
                'base', 'crm', 'project', 'document', 'sale', 'purchase',
                'stock', 'account', 'web_grid', 'hr_timesheet',
                'l10n_co',
                # Community addons
                'stock_real_availability', 'web_export_view',
                'web_widget_color',
                # Conalquipo's addons
                'con_base', 'con_delivery', 'con_hr_employee_driver',
                'con_hr_timesheet', 'con_mrp_repair_picking', 'con_operator',
                'con_product', 'con_project', 'con_project_translates',
                'con_purchase_translates', 'con_sale', 'con_set_location_color_wizard', 'con_shipping', 'con_stock',
                'con_stock_mail_automatic', 'con_web', 'con_website_sign', 
                'con_account', 'con_purchase'
    ],
    'data': [],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
