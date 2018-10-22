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
    'name': "Conalquipo's stock customizations",

    'summary': """
        Conalequipos's Project information for each customer on Stock form.
    """,

    'description': """
        Conalequipos's Project information for each customer on Stock form.
        - Set massive location and colors wizard
    """,

    'author': "Ingeniería Aplicaciones y Software",
    'website': "http://www.ias.com.co",
    'category': 'stock',
    'version': '0.1',
    'depends': ['base', 'project', 'stock', 'project', 'sale_stock',
                'base', 'delivery', 'con_delivery', 'repair',
                'hr', 'con_sale', 'con_location_states'],
    'data': ['security/ir.model.access.csv',
             # 'data/res_config.yml',
             'data/ir_module_category.xml',
             'data/res_groups.xml',
             'data/stock_warehouse.xml',
             'data/ir_cron.xml',
             'data/mail_template.xml',
             'wizards/views/set_location_wizard.xml',
             'wizards/views/stock_picking_cancel_wizard.xml',
             'wizards/views/stock_picking_equipment_change_wizard.xml',
             'reports/report_stockpicking.xml',
             'views/shipping_templates.xml',
             'views/stock_location.xml',
             'views/stock_move.xml',
             'views/stock_move_line.xml',
             'views/stock_picking.xml',
             'views/stock_menu.xml'],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
