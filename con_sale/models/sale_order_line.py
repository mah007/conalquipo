# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 (<http://www.ias.com.co>).
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
import time
from datetime import datetime, timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT, float_compare,
                        float_is_zero)

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    READONLY_STATES_OWNER = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _compute_uoms(self):
        """
        Compute availables uoms for product
        """
        uom_list = []
        for data in self:
            uoms = data.product_id.product_tmpl_id.uoms_ids
            if data.product_id:
                if uoms:
                    for p in uoms:
                        uom_list.append(p.uom_id.id)
                    data.compute_uoms = uom_list
                else:
                    data.compute_uoms = \
                        [data.product_id.product_tmpl_id.sale_uom.id]

    layout_category_id = fields.Many2one(
        'sale.layout_category', string='Section')
    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order")
    bill_uom = fields.Many2one(
        'uom.uom',
        string='UMS')
    compute_uoms = fields.Many2many(
        'uom.uom',
        compute='_compute_uoms',
        store=False)
    owner_id = fields.Many2one('res.partner', string='Supplier',
                               states=READONLY_STATES_OWNER,
                               change_default=True, track_visibility='always')
    product_subleased = fields.Boolean(string="Subleased", default=False)
    bill_uom_qty = fields.Float(
        'Sale Unit',
        digits=dp.get_precision('Product Unit'
                                ' of Measure'))
    bill_uom_qty_executed = fields.Float(
        'Executed',
        digits=dp.get_precision('Product Unit'
                                ' of Measure'))
    purchase_order_line = fields.One2many('purchase.order.line',
                                          'sale_order_line_id',
                                          string="Purchase Order Line",
                                          readonly=True, copy=False)
    stock_move_status = fields.Text(
        string="Stock move status", compute="_compute_move_status",
        store=True)
    # Components
    product_components = fields.Boolean('Have components?')
    product_uoms = fields.Boolean('Multiple uoms?')
    is_component = fields.Boolean('Component')
    is_extra = fields.Boolean('Extra')
    parent_component = fields.Many2one(
        'product.product', 'Parent component')
    components_ids = fields.One2many(
        'sale.product.components', 'sale_line_id', string='Components')
    # Operators
    add_operator = fields.Boolean('Add Operator')
    mess_operated = fields.Boolean('Message Operated', default=False)
    product_operate = fields.Many2one('product.product',
                                      string='Product Operate',
                                      domain=[('sale_ok', '=', True),
                                              ('type', '=', 'service')],
                                      change_default=True, ondelete='restrict')
    assigned_operator = fields.Many2one(
        'res.users', string="Assigned Operator")
    parent_line = fields.Many2one(
        'sale.order.line', 'Parent line')
    min_sale_qty = fields.Float('MQty')
    # Fleet
    delivery_direction = fields.Selection([('in', 'collection'),
                                           ('out', 'delivery')],
                                          string="Delivery Type")
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier")
    picking_ids = fields.Many2many(
        'stock.picking', 'order_line_picking_rel',
        'picking_id', 'sale_order_line_id',
        string="Pickings",
        help="Linked picking to the delivery cost")
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string="Vehicle",
        help="Linked vehicle to the delivery cost")
    salesman_id = fields.Many2one(
        related='order_id.user_id',
        store=True,
        string='Salesperson',
        readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain=[],
        change_default=True,
        ondelete='restrict', required=False)

    @api.multi
    def name_get(self):
        res = []
        if self._context.get('special_display', False):
            for rec in self:
                vehicle = "{} {}".format(rec.vehicle_id.model_id.name,
                                         rec.vehicle_id.license_plate)
                name = "{} - {} - {}".format(rec.name, rec.price_unit, vehicle)
                res.append((rec.id, name))
        else:
            res = super(SaleOrderLine, self).name_get()
        return res

    @api.one
    @api.constrains('start_date', 'end_date')
    def validate_dates(self):
        """
        Start date and end date validation
        """
        if self.end_date and self.start_date:
            d1 = fields.Date.from_string(self.start_date)
            d2 = fields.Date.from_string(self.end_date)
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date"))

    @api.onchange('start_date', 'end_date')
    def _check_dates(self):
        """
        Start date and end date validation
        """
        if self.end_date and self.start_date:
            d1 = fields.Date.from_string(self.start_date)
            d2 = fields.Date.from_string(self.end_date)
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date"))

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):
        """On Changed function on assigned_operator that update the field
        when is change from the move_line linked to the picking order.

          Args:
              self (record): Encapsulate instance object.

          Returns:
              None: Not return any value, only update the operator_service
              fields on sale order.

        """
        if self.assigned_operator:
            self.mess_operated = False
            move = self.env['stock.move'].search(
                [('sale_line_id', '=', self.id)])
            for line in move.move_line_ids:
                line.update({'assigned_operator': self.assigned_operator})

    def _timesheet_create_task_prepare_values(self):
        """Overloaded function for preparate fields values to create the new
        task.

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the task information.

        """
        result = super(SaleOrderLine,
                       self)._timesheet_create_task_prepare_values()
        result.update({'product_id': self.product_operate.id})
        return result

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        """Overloaded on changed function for product_id.

          This overload check if the line have a componentes and update the
          field product_components with a boolean value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the product information.

        """
        result = super(SaleOrderLine, self).product_id_change()
        self.product_components = False
        self.product_uoms = False
        self.components_ids = [(5,)]
        self.uoms_ids = [(5,)]
        products_ids = []
        uoms_list = []
        components_ids = self.product_id.product_tmpl_id.components_ids
        uoms_ids = self.product_id.product_tmpl_id.uoms_ids
        if components_ids:
            self.product_components = True
            for p in components_ids:
                values = {}
                values['quantity'] = p.quantity
                values['product_id'] = p.product_child_id.id
                values['extra'] = p.extra
                products_ids.append((0, 0, values))
        if uoms_ids:
            self.product_uoms = True
            for p in uoms_ids:
                uoms_list.append(p.uom_id.id)
            result['domain'] = {
                'bill_uom': [('id', 'in', uoms_list)]}
        else:
            self.bill_uom = self.product_id.product_tmpl_id.sale_uom.id
            self.bill_uom_qty = self.product_uom_qty
            result['domain'] = {
                'bill_uom': [
                    ('id',
                     'in',
                     [self.product_id.product_tmpl_id.sale_uom.id])]}
        if self.product_id.is_operated:
            self.mess_operated = True
        else:
            self.mess_operated = False
            self.add_operator = False
            self.service_operator = None
        self.components_ids = products_ids
        self.layout_category_id = \
            self.product_id.product_tmpl_id.layout_sec_id.id
        return result

    def _compute_move_status(self):
        """
        Get the products stock move status
        """
        for data in self:
            move = self.env[
                'stock.move'].search([
                    ('product_id', '=', data.product_id.id),
                    ('sale_line_id', '=', data.id)])
            for m in move:
                data.stock_move_status = m.state

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
        res['bill_uom'] = self.bill_uom.id
        # res['qty_shipped'] = self.product_uom_qty
        return res

    @api.model
    def create(self, values):
        # Overwrite sale order line create
        line = super(SaleOrderLine, self).create(values)
        # Check owner
        if line.owner_id:
            self.function_management_buy(line)
        # Create in lines extra products for components
        if line.components_ids:
            for data in line.components_ids:
                if data.extra:
                    qty = data.quantity * line.product_uom_qty
                    new_line_extra = {
                        'product_id': data.product_id.id,
                        'name': 'Extra ' + '%s' % (
                            line.product_id.default_code or ''),
                        'parent_component': line.product_id.id,
                        'parent_line': line.id,
                        'order_id': line.order_id.id,
                        'product_uom_qty': qty,
                        'layout_category_id':
                        line.product_id.product_tmpl_id.layout_sec_id.id,
                        'bill_uom_qty': qty,
                        'owner_id': data.owner_id.id,
                        'is_extra': True,
                        'bill_uom':
                        data.product_id.product_tmpl_id.uom_id.id
                    }
                    self.create(new_line_extra)
                else:
                    qty = data.quantity * line.product_uom_qty
                    new_line_components = {
                        'product_id': data.product_id.id,
                        'name': 'Comp ' + '%s' % (
                            line.product_id.default_code or ''),
                        'parent_component': line.product_id.id,
                        'parent_line': line.id,
                        'order_id': line.order_id.id,
                        'product_uom_qty': qty,
                        'bill_uom_qty': qty,
                        'price_unit': 0.0,
                        'owner_id': data.owner_id.id,
                        'layout_category_id':
                        line.product_id.product_tmpl_id.layout_sec_id.id,
                        'is_component': True,
                        'bill_uom':
                        data.product_id.product_tmpl_id.uom_id.id
                    }
                    self.create(new_line_components)
        # Dates validations
        if line.end_date and line.start_date:
            d1 = fields.Date.from_string(line.start_date)
            d2 = fields.Date.from_string(line.end_date)
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date"))
        # Fleet
        if line.is_delivery:
            line.update({
                'price_unit': line.order_id.delivery_price})
        if line.is_component:
            line.update({
                'price_unit': 0.0})
        # Create task on sale lines
        if line.bill_uom.id and line.bill_uom.id not in \
            self.env.user.company_id.default_uom_task_id._ids \
            and not \
                line.is_delivery and not line.is_component \
                and not line.task_id:
            task_values = {
                'name': "Task for: " +
                str(line.order_id.project_id.name) +
                " - " +
                str(line.product_id.name) +
                " - " +
                str(line.bill_uom.name),
                'project_id': line.order_id.project_id.id,
                'sale_line_id': line.id,
                'product_id': line.product_id.id,
                'partner_id': line.order_id.partner_id.id,
                'company_id': self.company_id.id,
                'email_from': line.order_id.partner_id.email,
                'user_id': False,
                'uom_id': line.bill_uom.id,
                'planned_hours': line.bill_uom_qty,
                'remaining_hours': line.bill_uom_qty,
            }
            task = self.env[
                'project.task'].create(task_values)
            line.write({'task_id': task.id})
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
            # Write lines extra products for componentes
            if rec.components_ids:
                for data in rec.components_ids:
                    if data.extra:
                        component = self.env['sale.order.line'].search(
                            [('is_component', '=', True),
                             ('parent_component', '=', rec.product_id.id),
                             ('order_id', '=', rec.order_id.id),
                             ('product_id', '=', data.product_id.id)])
                        qty = data.quantity * rec.product_uom_qty
                        new_line_component = {
                            'product_id': data.product_id.id,
                            'name': 'Component ' + '%s' % (
                                rec.product_id.name),
                            'parent_component': rec.product_id.id,
                            'order_id': rec.order_id.id,
                            'product_uom_qty': qty,
                            'bill_uom_qty': qty,
                            'is_component': True,
                            'layout_category_id':
                            rec.product_id.product_tmpl_id.layout_sec_id.id,
                            'bill_uom':
                            data.product_id.product_tmpl_id.uom_id.id
                        }
                        component.write(new_line_component)
                    else:
                        extra = self.env['sale.order.line'].search(
                            [('is_extra', '=', True),
                             ('parent_component', '=', rec.product_id.id),
                             ('order_id', '=', rec.order_id.id),
                             ('product_id', '=', data.product_id.id)])
                        qty = data.quantity * rec.product_uom_qty
                        new_line_extra = {
                            'product_id': data.product_id.id,
                            'name': 'Extra ' + '%s' % (
                                rec.product_id.name),
                            'parent_component': rec.product_id.id,
                            'order_id': rec.order_id.id,
                            'product_uom_qty': qty,
                            'bill_uom_qty': qty,
                            'is_extra': True,
                            'layout_category_id':
                            rec.product_id.product_tmpl_id.layout_sec_id.id,
                            'bill_uom':
                            data.product_id.product_tmpl_id.uom_id.id
                        }
                        extra.write(new_line_extra)
            # Dates validations
            if rec.end_date and rec.start_date:
                d1 = fields.Date.from_string(rec.start_date)
                d2 = fields.Date.from_string(rec.end_date)
                if d2 < d1:
                    raise UserError(
                        _("The end date can't be less than start date"))
        return res

    @api.depends(
        'discount', 'price_unit',
        'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            quantity = line.bill_uom_qty * line.product_uom_qty
            if quantity == 0.0 or False:
                line.update({
                    'bill_uom_qty': 1,
                    'product_uom_qty': 1
                })
            price = line.price_unit
            price_discount = line.price_unit * (
                1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price_discount, line.order_id.currency_id, quantity,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id)
            line.update({
                'price_unit': price,
                'price_tax': sum(
                    t.get(
                        'amount', 0.0) for t in taxes.get(
                            'taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty',
                 'order_id.state')
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

    @api.depends('price_total', 'bill_uom_qty', 'product_uom_qty')
    def _get_price_reduce_tax(self):
        data = 1.0
        for line in self:
            if not line.bill_uom_qty > 0.0:
                line.bill_uom_qty = data
            else:
                data = line.bill_uom_qty
            line.price_reduce_taxinc = \
                line.price_total / data

    @api.depends('price_subtotal', 'bill_uom_qty', 'product_uom_qty')
    def _get_price_reduce_notax(self):
        data = 1.0
        for line in self:
            if line.bill_uom_qty:
                if not line.bill_uom_qty > 0.0:
                    line.bill_uom_qty = data
                else:
                    data = line.bill_uom_qty
                line.price_reduce_taxexcl = \
                    line.price_subtotal / data
            else:
                line.price_reduce_taxexcl = 0.0

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
                  'tax_id', 'bill_uom_qty')
    def _onchange_discount(self):
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
            return product.with_context(
                pricelist=self.order_id.pricelist_id.id).price
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

    @api.onchange('product_uom')
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

    @api.onchange('bill_uom')
    def price_bill_qty(self):
        """
        Get price for specific uom of product
        """
        product_muoms = self.product_id.product_tmpl_id.multiples_uom
        if not product_muoms:
            self.price_unit = self.product_id.product_tmpl_id.list_price
            self.min_sale_qty = \
                self.product_id.product_tmpl_id.min_qty_rental
            self.bill_uom_qty = \
                self.product_id.product_tmpl_id.min_qty_rental
        else:
            for uom_list in self.product_id.product_tmpl_id.uoms_ids:
                if self.bill_uom.id == uom_list.uom_id.id:
                    self.price_unit = uom_list.cost_byUom
                    self.min_sale_qty = uom_list.quantity
                    self.bill_uom_qty = uom_list.quantity

    @api.multi
    def _action_launch_procurement_rule(self):
        res = super(SaleOrderLine, self)._action_launch_procurement_rule()
        self._propagate_picking_project()
        return res

    @api.multi
    def _propagate_picking_project(self):
        """
        This function write the `project_id` of the `sale_order` on the Stock
        Picking Order.

        :return: True
        """
        for order in self.mapped('order_id'):
            for picking in order.picking_ids:
                picking.write({'project_id': order.project_id.id})
        return True
