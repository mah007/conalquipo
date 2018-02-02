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

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_is_zero, float_compare
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one('sale.order', string='Sale Order',
                                    ondelete='cascade')
    order_type = fields.Selection([('rent', 'Rent'), ('purchase', 'Purchase')],
                                  string="Type", default="purchase")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    bill_uom = fields.Many2one('product.uom', string='Unit of Measure to '
                                                     'Purchase')

    bill_uom_qty = fields.Float('Quantity to Purchase',
                                digits=dp.get_precision(
                                    'Product Unit of Measure'))

    sale_order_line_id = fields.Many2one('sale.order.line',
                                       'Sale Order Line',
                                       ondelete='set null', index=True,
                                       readonly=True)

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'bill_uom_qty')
    def _compute_amount(self):
        for line in self:
            quantity = 0.0
            if line.bill_uom_qty > 0:
                quantity = line.bill_uom_qty
            else:
                quantity = line.product_qty

            taxes = line.taxes_id.compute_all(line.price_unit,
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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_type = fields.Selection([('rent', 'Rent'),
                                     ('purchase', 'Purchase'),
                                     ('sale', 'Sale')],
                                    string="Type", default="sale")

    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        quantity = 0.0
        if line.bill_uom_qty > 0:
            quantity = line.bill_uom_qty
        else:
            quantity = line.product_qty
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
            'quantity': quantity,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            'qty_shipped': qty,
            'bill_uom': line.bill_uom.id,
        }
        self.invoice_type = line.order_id.order_type
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data
