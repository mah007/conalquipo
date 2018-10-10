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
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order', ondelete='cascade')
    order_type = fields.Selection(
        [('rent', 'Rent'), ('purchase', 'Purchase')],
        string="Type", default="purchase")

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self._add_product_with_components()
        return res

    @api.multi
    def _add_product_with_components(self):
        for po in self:
            for ln in po.order_line:
                if ln.product_id.components:
                    for pk in po.picking_ids:
                        for mv in pk.move_lines:
                            mv.copy({
                                'product_id': ln.product_id.id,
                                'product_uom_qty': ln.product_qty,
                                'picking_id': pk.id,
                                'not_explode': True,
                            })
                            break
        return True


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    bill_uom = fields.Many2one(
        'uom.uom', string='Unit of Measure to Purchase')
    bill_uom_qty = fields.Float(
        'Quantity to Purchase', digits=dp.get_precision(
            'Product Unit of Measure'))
    sale_order_line_id = fields.Many2one(
        'sale.order.line', 'Sale Order Line', ondelete='set null',
        index=True, readonly=True)

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'bill_uom_qty')
    def _compute_amount(self):
        for line in self:
            quantity = 0.0
            if line.bill_uom_qty > 0:
                quantity = line.bill_uom_qty
            else:
                quantity = line.product_qty

            taxes = line.taxes_id.compute_all(
                line.price_unit,
                line.order_id.currency_id,
                quantity,
                product=line.product_id,
                partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('invoice_lines.invoice_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'in_invoice':
                        qty += inv_line.uom_id._compute_quantity(
                            inv_line.qty_shipped, line.product_uom)
                    elif inv_line.invoice_id.type == 'in_refund':
                        qty -= inv_line.uom_id._compute_quantity(
                            inv_line.qty_shipped, line.product_uom)
            line.qty_invoiced = qty
