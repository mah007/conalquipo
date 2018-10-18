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
    'depends': ['base', 'sales_team', 'sale_management', 'stock',
                'delivery', 'product', 'con_account', 'hr',
                'report_qweb_element_page_visibility'],
    'data': ['security/ir.model.access.csv',
             # 'data/res_config.yml',
             'data/email_template.xml',
             'data/cron_template.xml',
             'data/product_pricelist.xml',
             'wizard/views/sale_order_advertisement_wizard.xml',
             'wizard/views/customer_portfolio_wizard.xml',
             'wizard/views/sale_order_cancellation.xml',
             'views/sale_order_view.xml',
             'views/sale_report_inherit.xml',
             # 'views/res_config_settings.xml',
             # 'views/sale_order_template.xml',
             'report/report_customer_portfolio.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
