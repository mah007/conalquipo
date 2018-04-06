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
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    qty_shipped = fields.Float(
        'Quantity to be shipped',
        digits=dp.get_precision('Product Unit of Measure'))


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    project_id = fields.Many2one('project.project', string="Work")
    invoice_type = fields.Selection([('rent', 'Rent'),
                                     ('purchase', 'Purchase'),
                                     ('sale', 'Sale')],
                                    string="Type", default="sale")

    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0,
                         precision_rounding=line.product_uom.rounding) <= 0:
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
            'account_id': invoice_line.with_context(
                {'journal_id': self.journal_id.id,
                 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.compute(
                line.price_unit,  self.currency_id, round=False),
            'quantity': quantity,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            'qty_shipped': qty,
            'bill_uom': line.bill_uom.id,
        }
        self.invoice_type = line.order_id.order_type
        account = invoice_line.get_invoice_line_account(
            'in_invoice', line.product_id, line.order_id.fiscal_position_id,
            self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data
