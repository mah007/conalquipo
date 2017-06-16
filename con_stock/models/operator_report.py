# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _name = "operator.report"
    _description = "Operator Report"
    _auto = False
    _order = 'start_date'

    operator = fields.Char(string='Operator', readonly=True)
    availability = fields.Selection([('available', 'Available'),
                                     ('not_available', 'Not Available')],
                                    string="Availability", readonly=True)
    picking = fields.Many2one('stock.picking', 'Stock Picking', readonly=True)
    construction = fields.Many2one('res.partner', 'Construction', 
                                   readonly=True)
    product = fields.Many2one('product.product', 'Product', readonly=True)
    start_date = fields.Date(string="Start", readonly=True)
    end_date = fields.Date(string="End", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'operator_report')
        self._cr.execute("""
            create view operator_report as
            select min(sp.id) as id,
            sp.id as picking,
            sp.partner_id as construction,
            spd.product_id as product,
            he.name_related as operator, he.availability as availability,
            sol.start_date as start_date, sol.end_date as end_date
            from stock_picking sp
            left join sale_order so on (sp.origin=so.name)
            left join sale_order_line sol on (so.id=sol.order_id)
            left join stock_pack_detail_product spd on (sp.id=spd.picking_id)
            left join hr_employee he on (spd.operator_ids=he.id)
            left join product_product pp on (spd.product_id=pp.id)
            left join product_template pt on (pp.product_tmpl_id=pt.id)
            where pt.is_operated = true
            group by
            sp.id,
            sp.partner_id,
            sol.start_date,
            sol.end_date,
            spd.product_id,
            he.name_related,
            he.availability
        """)
