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
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')],
                                  string="Type", default="rent")

    purchase_ids = fields.One2many('purchase.order', 'sale_order_id',
                                   string='Purchase Orders')
    state = fields.Selection(selection_add=[
        ('merged', _('Merged')),
    ])

    sale_order_id = fields.Many2one('sale.order', 'Merged In')

    sale_order_ids = fields.One2many('sale.order', 'sale_order_id',
                                     string='Sale Orders related')

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
                                    ('state', '=', 'sale'),
                                    ('project_id', '=', self.project_id.id)
                                    ], limit=1)
            if order_id:
                for line in self.order_line:
                    line_copy = line.copy({'order_id': order_id.id})
                    order_id.write({'order_line': [(4, line_copy.id)]})
                self.update({'state': 'merged',
                             'sale_order_id': order_id.id,
                             'confirmation_date': fields.Datetime.now()
                             })
                if self.env.context.get('send_email'):
                    self.force_quotation_send()
                res = True
            else:
                res = super(SaleOrder, self).action_confirm()

        self.function_add_picking_owner()
        for purchase_id in self.purchase_ids:
                purchase_id.button_confirm()
        return res

    @api.multi
    def function_add_picking_owner(self):
        # This function adds the owner of the product to the
        # corresponding line in the  output inventory movement

        for pk in self.picking_ids:
            for ml in pk.move_lines:
                owner = self.function_product_subleased(ml.product_id)
                for mvl in ml.move_line_ids:
                    if owner:
                        mvl.write({'owner_id': owner.id})

    @api.multi
    def function_product_subleased(self, product):
        # This function adds the owner of the product to the  corresponding
        #  line on the invoice.

        for line in self.order_line:
            if line.product_id == product and line.product_subleased:
                return line.owner_id
        return False

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(grouped, final)

        for inv in self.invoice_ids:
            for inv_ids in inv.invoice_line_ids:
                owner = self.function_product_subleased(inv_ids.product_id)
                _logger.info(owner)
                if owner:
                    inv_ids.write({'owner_id': owner.id})
                inv_ids.invoice_type = self.order_type
        return res

    @api.multi
    def action_advertisement(self):

        wizard_id = self.env['sale.order.advertisement.wizard'].create(
            vals={'partner_id': self.partner_id.id,
                  'project_id': self.project_id.id,
                  'sale_order_id': self.id,
                  'location_id': self.project_id.stock_location_id.id,
                  })
        return {
            'name': 'Advertisement Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.advertisement.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    READONLY_STATES_OWNER = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order")
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure to Sale')

    owner_id = fields.Many2one('res.partner', string='Supplier',
                               states=READONLY_STATES_OWNER,
                               change_default=True, track_visibility='always')
    product_subleased = fields.Boolean(string="Subleased", default=False)

    bill_uom_qty = fields.Float('Quantity to Sale',
                                digits=dp.get_precision('Product Unit'
                                                        ' of Measure'))

    purchase_order_line = fields.One2many('purchase.order.line',
                                          'sale_order_line_id',
                                          string="Purchase Order Line",
                                          readonly=True, copy=False)

    @api.onchange('owner_id')
    def onchange_owner_id(self):
        # This function changes to true or false the field product_subleased
        # depending on whether or not there is owner in the order line

        if self.owner_id:
            self.product_subleased = True
        else:
            self.product_subleased = False

    @api.multi
    def function_management_buy(self, line):
        # This function creates the purchase or rental orders associated with
        # this sale, if a purchase order already exists, the same supplier only
        # adds a line to this order otherwise it creates the complete order
        existing_purchase = False
        for purchase in line.order_id.purchase_ids:
            if purchase.partner_id.id == line.owner_id.id and \
                    purchase.state == line.order_id.state:
                    self.function_purchase_line_create(line, purchase)
                    existing_purchase = True

        if not existing_purchase:
            po = self.function_purchase_create(line)
            self.function_purchase_line_create(line, po)
            line.order_id.write({'purchase_ids': [(4, po.id)]})

    @api.multi
    def function_purchase_create(self, line):
        # This function forms the purchase data and creates it
        # return: the new purchase
        purchase = {
            'partner_id': line.owner_id.id,
            'company_id': line.company_id.id,
            'currency_id':
                line.owner_id.property_purchase_currency_id.id or
                self.env.user.company_id.currency_id.id,
            'origin': line.order_id.name,
            'payment_term_id':
                line.owner_id.property_supplier_payment_term_id.id,
            'date_order': datetime.strptime(line.order_id.date_order,
                                            DEFAULT_SERVER_DATETIME_FORMAT),
            'fiscal_position_id': line.order_id.fiscal_position_id,
            'order_type': 'rent',
        }
        po = self.env['purchase.order'].create(purchase)
        return po

    @api.multi
    def function_purchase_line_create(self, line, purchase):
        # This function forms the data of the purchase line and creates it
        pol = self.env['purchase.order.line'].create({
            'name': line.product_id.name,
            'product_qty': line.product_uom_qty,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom.id,
            'price_unit': line.price_unit,
            'date_planned': datetime.strptime(
                line.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT),
            'taxes_id': [(6, 0, line.tax_id.ids)],
            'order_id': purchase.id,
            'bill_uom': line.bill_uom.id,
            'bill_uom_qty': line.bill_uom_qty,
            'sale_order_line_id': line.id
        })
        line.write({'purchase_order_line': [(4, pol.id)]})

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line
        for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        quantity = 0.0
        if self.bill_uom_qty > 0:
            quantity = self.bill_uom_qty
        else:
            quantity = res['quantity']

        res['bill_uom'] = self.bill_uom.id
        res['qty_shipped'] = self.product_uom_qty
        res['quantity'] = quantity
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

    @api.model
    def create(self, values):

        line = super(SaleOrderLine, self).create(values)
        if line.owner_id:
            self.function_management_buy(line)
        return line

    @api.multi
    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        for rec in self:
            if values.get('owner_id') and not rec.purchase_order_line:
                rec.function_management_buy(rec)
            if rec.purchase_order_line and values.get('product_uom_qty'):
                values['product_qty'] = values.get('product_uom_qty')
                rec.purchase_order_line.write(values)
        return res

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'bill_uom_qty')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            quantity = 0.0
            if line.bill_uom_qty > 0:
                quantity = line.bill_uom_qty
            else:
                quantity = line.product_uom_qty

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price, line.order_id.currency_id, quantity,
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
        - no: if the SO is not in status 'sale' or 'done', we consider that
        there is nothing to invoice. This is also hte default value if the
        conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to
        metho _get_to_invoice_qty()` for more information on how this quantity
        is calculated.
        - upselling: this is possible only for a product invoiced on ordered
        quantities for which we delivered more than expected. The could arise
        if, for example, a project took more time than expected but we decided
        not to invoice the extra cost to the client. This occurs onyl in state
        'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity
        ordered.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice,
                                   precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' \
                    and line.product_id.invoice_policy == 'order' \
                    and float_compare(line.qty_delivered,
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
        Compute the quantity to invoice. If the invoice policy is order, the
        quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            qty = 0.0
            if line.bill_uom_qty > 0:
                qty = line.bill_uom_qty
            else:
                qty = line.product_uom_qty

            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = \
                        (line.qty_delivered - line.qty_invoiced)
            else:
                line.qty_to_invoice = 0

    @api.depends('price_total', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = line.price_total / line.bill_uom_qty\
                if line.bill_uom_qty else 0.0

    @api.depends('price_subtotal', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_notax(self):
        for line in self:
            if line.bill_uom_qty:
                line.price_reduce_taxexcl =\
                    (line.price_subtotal / line.bill_uom_qty)
            else:
                line.price_reduce_taxexcl = 0.0

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
                  'tax_id', 'bill_uom_qty')
    def _onchange_discount(self):
        self.discount = 0.0
        discount_policy = self.order_id.pricelist_id.discount_policy
        res_group = self.env.user.has_group('sale.group_discount_per_so_line')
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                discount_policy == 'without_discount' and res_group):
            return

        context_partner = dict(self.env.context,
                               partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order)
        pricelist_context = dict(context_partner, uom=self.product_uom.id)
        qty = 0.0
        if self.bill_uom_qty > 0:
            qty = self.bill_uom_qty
        else:
            qty = self.product_uom_qty
        price, rule_id = self.order_id.pricelist_id.with_context(
            pricelist_context).get_product_price_rule(self.product_id,
                                                      qty or 1.0,
                                                      self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(
            context_partner)._get_real_price_currency(
            self.product_id, rule_id, qty, self.product_uom,
            self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price,
                # which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(
                    currency_id).with_context(context_partner).compute(
                    new_list_price, self.order_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id
                                        ).price
        final_price, rule_id = \
            self.order_id.pricelist_id.get_product_price_rule(
                self.product_id, self.bill_uom_qty or 1.0,
                self.order_id.partner_id)
        context_partner = dict(self.env.context,
                               partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order)
        base_price, currency_id = self.with_context(
            context_partner)._get_real_price_currency(
            self.product_id, rule_id, self.bill_uom_qty, self.product_uom,
            self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(
                currency_id).with_context(context_partner).compute(
                base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_uom', 'product_uom_qty', 'bill_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),
                bill_uom_qty=self.bill_uom_qty,
                bill_uom=self.bill_uom,
                owner_id=self.owner_id,
                start_date=self.start_date,
                end_date=self.end_date,
                product_subleased=self.product_subleased,
            )
            self.price_unit = self.env[
                'account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id,
                self.tax_id, self.company_id)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    qty_shipped = fields.Float(
        'Quantity to be shipped',
        digits=dp.get_precision('Product Unit of Measure'))
