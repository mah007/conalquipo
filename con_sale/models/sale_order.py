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
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ~ Please if you need add new option in this fields use the following
    # method: field_name = fields.Selection(selection_add=[('a', 'A')]
    order_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')],
                                  string="Type", default="rent")

    purchase_ids = fields.One2many('purchase.order', 'sale_order_id',
                                   string='Purchase Orders')

    @api.onchange('state')
    def onchange_state(self):
        for purchase_id in self.purchase_ids:
            if self.state in ['done', 'cancel']:
                purchase_id.write({'state': self.state})
            if self.state == 'sale':
                purchase_id.button_confirm()

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._add_picking_owner()
        for purchase_id in self.purchase_ids:
                purchase_id.button_confirm()
        return res

    @api.multi
    def _add_picking_owner(self):

        for pk in self.picking_ids:
            for ml in pk.move_lines:
                owner = self.product_subleased(ml.product_id)
                for mvl in ml.move_line_ids:
                    if owner:
                        mvl.write({'owner_id': owner.id})

        return True

    @api.multi
    def product_subleased(self, product):

        for line in self.order_line:
            if line.product_id == product and line.product_subleased:
                return line.owner_id
        return False

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(grouped, final)

        for inv in self.invoice_ids:
            for inv_ids in inv.invoice_line_ids:
                owner = self.product_subleased(inv_ids.product_id)
                _logger.info(owner)
                if owner:
                    inv_ids.write({'owner_id': owner.id})
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    READONLY_STATES_OWNER = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line
        for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['bill_uom'] = self.bill_uom.id
        res['bill_uom_qty'] = self.bill_uom_qty
        return res

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        for line in self:
                qty_invoiced = 0.0
                for invoice_line in line.invoice_lines:
                    if invoice_line.invoice_id.state != 'cancel':
                        data = {
                            'out_invoice': lambda qty_invoice:
                            qty_invoice +
                            invoice_line.uom_id._compute_quantity(
                                invoice_line.quantity, line.product_uom,
                                rent=True),
                            'out_refund': lambda qty_invoiced:
                            qty_invoiced -
                            invoice_line.uom_id._compute_quantity(
                                invoice_line.quantity, line.product_uom,
                                rent=True)
                        }
                        qty_invoiced = data.get(invoice_line.invoice_id.type,
                                                lambda: 0)(qty_invoiced)
                line.qty_invoiced = qty_invoiced

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order", default='sale')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure')

    owner_id = fields.Many2one('res.partner', string='Supplier',
                               states=READONLY_STATES_OWNER,
                               change_default=True, track_visibility='always')
    product_subleased = fields.Boolean(string="Subleased", default=False)

    bill_uom_qty = fields.Float('Quantity',
                                digits=dp.get_precision(
                                    'Product Unit of Measure'))

    @api.onchange('owner_id')
    def onchange_owner_id(self):
        if self.owner_id:
            self.product_subleased = True

    @api.model
    def create(self, values):

        line = super(SaleOrderLine, self).create(values)

        if line.owner_id:
            purchase = {
                'partner_id': line.owner_id.id,
                'company_id': line.company_id.id,
                'currency_id':
                    line.owner_id.property_purchase_currency_id.id or
                    self.env.user.company_id.currency_id.id,
                'origin': line.order_id.name,
                'payment_term_id':
                    line.owner_id.property_supplier_payment_term_id.id,
                'date_order': datetime.strptime(
                    line.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT),
                'fiscal_position_id': line.order_id.fiscal_position_id,
            }
            po = self.env['purchase.order'].create(purchase)

            self.env['purchase.order.line'].create({
                'name': line.product_id.name,
                'product_qty': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'price_unit': line.price_unit,
                'date_planned': datetime.strptime(
                    line.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT),
                'taxes_id': [(6, 0, line.tax_id.ids)],
                'order_id': po.id,
            })

            line.order_id.write({'purchase_ids': [(4, po.id)]})

        return line


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    bill_uom_qty = fields.Float('Quantity of Sale',
                                digits=dp.get_precision(
                                    'Product Unit of Measure'))
