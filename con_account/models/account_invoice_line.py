# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2018 IAS (<http://www.ias.com.co>).
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
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _order = "date_move asc"

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one(
        'uom.uom', string='Unit of Measure of Sale')
    document = fields.Char(
        string='Document')
    date_move = fields.Date(
        string='Date')
    date_init = fields.Integer(
        string='Date init')
    date_end = fields.Integer(
        string='Date end')
    num_days = fields.Integer(
        string='Number days')
    qty_remmisions = fields.Float(
        string='Qty remmisions')
    qty_returned = fields.Float(
        string='Qty returned')
    products_on_work = fields.Float(
        string='Products on work')
    parent_sale_line = fields.Many2one(
        comodel_name='sale.order.line',
        string='Parent sale line')
    move_history_id = fields.Many2one(
        'stock.move.history',
        'Stock Move History', help="Stock Move History")
    layout_category_id = fields.Many2one(
        'sale.layout_category', string='Section')

    @api.one
    @api.depends(
        'price_unit', 'discount', 'invoice_line_tax_ids',
        'quantity', 'product_id', 'invoice_id.partner_id',
        'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        res = super(AccountInvoiceLine, self)._compute_price()
        if self.invoice_id.invoice_type in ['rent']:
            if self.products_on_work == 0.0:
                if self.product_id.type != 'product':
                    self.price_subtotal = self.quantity * self.price_unit
                else:
                    self.price_subtotal = 0.0
            else:
                self.price_subtotal = \
                    self.products_on_work * self.quantity * self.price_unit
        return res
