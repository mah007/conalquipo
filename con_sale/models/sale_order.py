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

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ~ Please if you need add new option in this fields use the following
    # method: field_name = fields.Selection(selection_add=[('a', 'A')]
    order_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')],
                                  string="Type", default="sale")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res['uom_id'] = self.product_inv_uom.id
        return res

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type', string="Type Order")
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
