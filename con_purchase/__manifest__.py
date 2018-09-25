# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase module modifications',
    'version': '1.1',
    'category': 'Purchase',
    'sequence': 10,
    'summary': 'Purchase',
    'depends': [
        'account', 'project', 'sale',
        'purchase'
    ],
    'description':
    """
        Purchase module modification

        - Adds sale_order_id, order_type field to purchase.order
          model.
        - Adds bill_uom, bill_uom_qty, sale_order_line_id
          field to purchase.order.line model.
    """,
    'data': [
        'views/purchase_view.xml'
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
