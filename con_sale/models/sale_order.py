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
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ~ Please if you need add new option in this fields use the following
    # method: field_name = fields.Selection(selection_add=[('a', 'A')]
    order_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')],
                                  string="Type", default="sale")

    purchase_ids = fields.One2many('purchase.order', 'sale_order_id',
                                   string='Purchase Orders')
    state = fields.Selection(selection_add=[
        ('merged', _('Merged')),
    ])

    merged_in = fields.Char('Merged In')

    @api.onchange('state')
    def onchange_state(self):
        for purchase_id in self.purchase_ids:
            if self.state in ['done', 'cancel']:
                purchase_id.write({'state': self.state})
            if self.state == 'sale':
                purchase_id.button_confirm()

    @api.multi
    def action_confirm(self):

        if self.partner_id:
            order_id = self.search([('partner_id', '=', self.partner_id.id),
                                    ('state', '=', 'sale')], limit=1)
            if order_id:
                for line in self.order_line:
                    line_copy = line.copy({'order_id': order_id.id})
                    order_id.write({'order_line': [(4, line_copy.id)]})
                self.update({'state': 'merged',
                             'merged_in': order_id.name,
                             'confirmation_date': fields.Datetime.now()
                             })
                if self.env.context.get('send_email'):
                    self.force_quotation_send()
                res = True
            else:
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
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['bill_uom'] = self.bill_uom.id
        res['qty_shipped'] = self.product_uom_qty
        res['quantity'] = self.bill_uom_qty
        return res

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        for line in self:
                qty_invoiced = 0.0
                for invoice_line in line.invoice_lines:
                    if invoice_line.invoice_id.state != 'cancel':
                        dict = {
                            'out_invoice': lambda qty_invoice: qty_invoice + invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom, rent=True),
                            'out_refund': lambda qty_invoiced: qty_invoiced - invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom, rent=True)
                        }
                        qty_invoiced = dict.get(invoice_line.invoice_id.type, lambda: 0)(qty_invoiced)
                line.qty_invoiced = qty_invoiced

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order", default='sale')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure to Sale')

    owner_id = fields.Many2one('res.partner', string='Supplier',
                                states=READONLY_STATES_OWNER,
                                change_default=True, track_visibility='always')
    product_subleased = fields.Boolean(string="Subleased", default=False)

    bill_uom_qty = fields.Float('Quantity to Sale',
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
                'currency_id': line.owner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
                'origin': line.order_id.name,
                'payment_term_id': line.owner_id.property_supplier_payment_term_id.id,
                'date_order': datetime.strptime(line.order_id.date_order,
                                                DEFAULT_SERVER_DATETIME_FORMAT),
                'fiscal_position_id': line.order_id.fiscal_position_id,
            }
            po = self.env['purchase.order'].create(purchase)

            self.env['purchase.order.line'].create({
                'name': line.product_id.name,
                'product_qty': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'price_unit': line.price_unit,
                'date_planned': datetime.strptime(line.order_id.date_order,
                                                  DEFAULT_SERVER_DATETIME_FORMAT),
                'taxes_id': [(6, 0, line.tax_id.ids)],
                'order_id': po.id,
            })

            line.order_id.write({'purchase_ids': [(4, po.id)]})

        return line

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'bill_uom_qty')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id,
                                            line.bill_uom_qty,
                                            product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice',
                 'qty_invoiced', 'bill_uom_qty')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice,
                                   precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                            float_compare(line.qty_delivered,
                                          line.product_uom_qty,
                                          precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty,
                               precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty',
                 'order_id.state', 'bill_uom_qty')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.bill_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('price_total', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = line.price_total / line.bill_uom_qty if line.bill_uom_qty else 0.0

    @api.depends('price_subtotal', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_notax(self):
        for line in self:
            line.price_reduce_taxexcl = line.price_subtotal / line.bill_uom_qty if line.bill_uom_qty else 0.0

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
                  'tax_id', 'bill_uom_qty')
    def _onchange_discount(self):
        self.discount = 0.0
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return

        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        pricelist_context = dict(context_partner, uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(self.product_id, self.bill_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id, self.bill_uom_qty, self.product_uom, self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(new_list_price, self.order_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    @api.onchange('product_uom', 'product_uom_qty', 'bill_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.bill_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env[
                'account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id,
                self.company_id)

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id).price
        final_price, rule_id = self.order_id.pricelist_id.get_product_price_rule(self.product_id, self.bill_uom_qty or 1.0, self.order_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id, self.bill_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [
            ('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (
            self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0
            vals['bill_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('bill_uom_qty') or self.bill_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env[
                'account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id,
                self.company_id)
        self.update(vals)

        return result


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    qty_shipped = fields.Float('Quantity to be shipped',
                               digits=dp.get_precision(
                                   'Product Unit of Measure'))
