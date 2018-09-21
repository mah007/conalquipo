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
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    init_date_invoice = fields.Date(
        string='Init Date')
    end_date_invoice = fields.Date(
        string='End Date')

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order.
         This method may be
        overridden to implement custom invoice generation
        (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({'init_date_invoice': self.init_date_invoice,
                             'end_date_invoice': self.end_date_invoice,
                             'invoice_type': self.order_type})

        return invoice_vals

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by
            (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if self.env['account.invoice'].search(
                ['|', '|', '&',
                 ('init_date_invoice', '<=', self.init_date_invoice),
                 ('end_date_invoice', '>=', self.init_date_invoice),
                 '&',
                 ('init_date_invoice', '<=', self.end_date_invoice),
                 ('end_date_invoice', '>=', self.end_date_invoice),
                 '&',
                 ('init_date_invoice', '>=', self.init_date_invoice),
                 ('end_date_invoice', '<=', self.end_date_invoice),
                 ('partner_id', '=', self.partner_id.id),
                 ('project_id', '=', self.project_id.id),
                 ('state', '!=', 'cancel')]):
            raise UserError(
                'You are trying to create an invoice in a period and invoice.')
        values = super(SaleOrder, self).action_invoice_create(grouped, final)
        return values


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def get_qty_tasks(self, init_date_invoice, end_date_invoice,
                      moves, delta):
        """
        Return the quantity of the tasks on
        executed by the products.
        """
        qty = 0.0
        # Get tasks values
        if not self.is_extra and \
                not self.is_component and \
                self.bill_uom.id not in \
                self.company_id.default_uom_task_id._ids:
            task = self.env['project.task'].search(
                [('sale_line_id', '=', self.id)])
            for timesheet in task.timesheet_ids:
                date = fields.Date.from_string(timesheet.date)
                if date >= init_date_invoice and \
                        date <= end_date_invoice:
                    qty += timesheet.unit_amount
        elif self.bill_uom.id == self.env.ref('product.product_uom_day').id:
            qty = delta.days + 1
        else:
            qty = moves.product_uom_qty
        return qty

    def get_history(self, move, move_type="outgoing"):
        """
        Return the product outgoing histoy of the
        moves
        """
        history = self.env[
            'stock.move.history'].search(
            [('sale_line_id', '=', self.id),
             ('move_id', '=', move.id),
             ('code', '=', move_type)])
        return history

    @api.multi
    def _prepare_invoice_line_from_stock(
            self, history, invoice_id=False, move_type=''):
        self.ensure_one()
        result = []
        picking_list = []

        account = self.product_id.property_account_income_id or\
            self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product:'
                              ' "%s" (id:%d) - or for its category: "%s".') %
                            (self.product_id.name, self.product_id.id,
                             self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or\
            self.order_id.partner_id.property_account_position_id

        if fpos:
            account = fpos.map_account(account)

        date_init = fields.Date.from_string(
            self.order_id.init_date_invoice)
        date_end = fields.Date.from_string(
            self.order_id.end_date_invoice)
        date_current = date_init
        date_next = date_end

        next = 0
        if history[0].code == 'incoming' and history[0].move_id.advertisement_date:  # noqa
            create_date = fields.Date.from_string(
                history[0].move_id.advertisement_date)
        else:
            create_date = fields.Date.from_string(
                history[0].move_id.date_expected)

        if create_date < date_init and history[0].quantity_project > 0:
            try:
                if history[1].code == 'incoming' and history[1].move_id.advertisement_date:  # noqa
                    date_next = fields.Date.from_string(
                        history[1].move_id.advertisement_date)
                else:
                    date_next = fields.Date.from_string(
                        history[1].move_id.date_expected)
                if date_next > date_current:
                    date_next -= timedelta(days=1)
            except:
                date_next = date_end

            delta = date_next - date_current
            qty = self.get_qty_tasks(
                date_current, date_next,
                history[0].move_id, delta)
            inv_line = {
                "date_move": create_date,
                'invoice_id': invoice_id,
                "name": self.product_id.name,
                "account_id": account.id,
                "price_unit": self.price_unit,
                "document": 'INI',
                'sequence': self.sequence,
                'origin': self.order_id.name,
                "uom_id": self.product_uom.id,
                "product_id": self.product_id.id,
                "bill_uom": self.bill_uom.id,
                "discount": self.discount,
                "qty_remmisions": 0.00,
                "qty_returned": 0.00,
                "date_init": date_current.day,
                "date_end": date_next.day,
                "num_days": delta.days + 1,
                "quantity": qty,
                "parent_sale_line": self.parent_line.id,
                "products_on_work": history[0].quantity_project,
                "invoice_line_tax_ids":
                    [(6, 0, self.tax_id.ids)],
                "layout_category_id":
                    self.layout_category_id.id,
                'account_analytic_id': self.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'sale_line_ids': False,
            }
            result.append(inv_line)
            history = history[1:]

        for mv in history:
            qty = 0.0
            next += 1
            create_date = fields.Date.from_string(mv.create_date)
            if mv.code == 'incoming' and mv.move_id.advertisement_date:
                create_date = fields.Date.from_string(
                    mv.move_id.advertisement_date)
            else:
                create_date = fields.Date.from_string(
                    mv.move_id.date_expected)
            date_current = create_date

            try:
                if history[next].code == 'incoming' and history[next].move_id.advertisement_date:  # noqa
                    date_next = fields.Date.from_string(
                        history[next].move_id.advertisement_date)
                else:
                    date_next = fields.Date.from_string(
                        history[next].move_id.date_expected)
                if date_next > date_current:
                    date_next -= timedelta(days=1)
            except:
                date_next = date_end

            if mv.code == 'incoming' and mv.quantity_project <= 0.0:
                date_next = date_current

            delta = date_next - date_current

            # Get tasks values
            qty = self.get_qty_tasks(
                date_current, date_next, mv.move_id, delta)
            # Create returned product invoice
            inv_line = {
                "date_move": create_date,
                'invoice_id': invoice_id,
                "name": self.product_id.name,
                "account_id": account.id,
                "price_unit": self.price_unit,
                "document": mv.move_id.picking_id.name,
                'sequence': self.sequence,
                'origin': self.order_id.name,
                "uom_id": self.product_uom.id,
                "product_id": self.product_id.id,
                "bill_uom": self.bill_uom.id,
                "discount": self.discount,
                "qty_remmisions": mv.quantity_done if mv.code == 'outgoing' else 0.00,  # noqa
                "qty_returned": mv.quantity_done if mv.code == 'incoming' else 0.00,  # noqa
                "date_init": date_current.day,
                "date_end": date_next.day,
                "num_days": delta.days + 1,
                "quantity": qty,
                "parent_sale_line": self.parent_line.id,
                "products_on_work": mv.quantity_project,
                "invoice_line_tax_ids":
                    [(6, 0, self.tax_id.ids)],
                "layout_category_id":
                    self.layout_category_id.id,
                'account_analytic_id': self.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'sale_line_ids': [(6, 0, [self.id])]
                if mv.code == 'outgoing' else False,
                'move_history_id': mv.id,
            }

            if mv.quantity_project == 0.0:
                inv_line['price_unit'] = 0.0
            result.append(inv_line)
            # Pickings for deliveries
            picking_list.append(mv.picking_id)
        # Create dict for deliveries
        for pck in list(set(picking_list)):
            delivery = self.get_delivery_invoice(
                pck, invoice_id, account)
            if delivery:
                result.append(delivery)
        return result

    @api.multi
    def get_delivery_invoice(self, picking, invoice_id, account):
        """
        Create deliveries
        """
        # Get vehicle price
        product = picking.carrier_id.product_id
        document = "ACAR: " + picking.name
        if picking.delivery_cost:
            for delivery in picking.delivery_cost:
                if self.env['account.invoice.line'].search(
                        [('document', '=', document),
                         ('invoice_id', '=', invoice_id)]):
                    return
                # if delivery.invoice_lines:
                #     continue
                inv_line = {
                    "date_move": picking.advertisement_date or
                    picking.scheduled_date,
                    "invoice_id": invoice_id,
                    "product_id": product.id,
                    "name": product.name + ':' + picking.name or
                    _('Not linked move'),
                    "account_id": account.id,
                    "document": "ACAR: " + picking.name or False,
                    "price_unit": delivery.price_unit,
                    "bill_uom": product.sale_uom.id,
                    "uom_id": product.uom_id.id,
                    'sale_line_ids': [(6, 0, [self.id])],
                    "invoice_line_tax_ids":
                        [(6, 0, self.tax_id.ids)],
                    "layout_category_id":
                        product.product_tmpl_id.layout_sec_id.id,
                    'origin': picking.name,
                    'discount': 0.00,
                }
            return inv_line

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be
        positive (invoice) or negative (refund).
            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """

        search_op = [
            ([('product_id', '=', self.product_id.id),
              ('project_id', '=', self.order_id.project_id.id),
              ('partner_id', '=', self.order_id.partner_id.id),
              ('code', '!=', 'internal'),
              ('date', '<', self.order_id.init_date_invoice),
              ('date', '>=', self.order_id.project_id.work_date_creation),
              ('move_id.parent_sale_line', '=', False)], 'INI'),

            ([('product_id', '=', self.product_id.id),
              ('project_id', '=', self.order_id.project_id.id),
              ('partner_id', '=', self.order_id.partner_id.id),
              ('code', '!=', 'internal'),
              ('date', '>=', self.order_id.init_date_invoice),
              ('date', '<=', self.order_id.end_date_invoice),
              ('move_id.parent_sale_line', '=', False)], 'ALL'),
        ]

        if self.order_id.order_type not in ['rent']:
            invoice_lines = super(SaleOrderLine, self).invoice_line_create(
                invoice_id, qty)
        else:
            invoice_lines = self.env['account.invoice.line']
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            # Get REM
            for line in self:
                vals = []
                if line.product_id in self.env['account.invoice'].browse(
                        invoice_id).invoice_line_ids.mapped('product_id'):
                    continue

                if not float_is_zero(qty, precision_digits=precision):
                    history = []
                    for op in search_op:

                        if op[1] == 'INI':
                            moves = self.env['stock.move.history'].search(
                                op[0], order="date, id")
                            moves = moves.filtered(lambda h: h.picking_id.state == 'done' and (  # noqa
                                (h.code == 'outgoing' and h.move_id.location_dest_id.usage == 'customer') or  # noqa
                                (h.code == 'incoming' and h.move_id.returned and h.move_id.location_dest_id.return_location)  # noqa
                            ))

                            if moves:
                                history += moves[-1]
                        else:
                            moves = self.env['stock.move.history'].search(
                                op[0], order="create_date, id asc")
                            moves = moves.filtered(
                                lambda h: (not h.invoice_line_ids or len([li for li in h.invoice_line_ids if li.invoice_id.state == 'cancel']) == len(h.invoice_line_ids)) and h.picking_id.state == 'done' and (  # noqa
                                (h.code == 'outgoing' and h.move_id.location_dest_id.usage == 'customer') or  # noqa
                                (h.code == 'incoming' and h.move_id.returned and h.move_id.location_dest_id.return_location)  # noqa
                            ))
                            if moves:
                                history += [mh for mh in moves]

                        if history:
                            history = sorted(history, key=lambda h: (h.move_id.advertisement_date or h.move_id.date_expected))  # noqa
                            vals = line._prepare_invoice_line_from_stock(
                                history, invoice_id=invoice_id)
                for val in vals:
                    invoice_lines |= self.env['account.invoice.line']\
                        .create(val)

                for line in self.filtered(
                        lambda sol: sol.product_id.type == 'service' and
                        not sol.product_id.for_shipping):
                    if not float_is_zero(qty, precision_digits=precision):
                        vals = line._prepare_invoice_line(qty=qty)
                        vals.update({'invoice_id': invoice_id,
                                     'sale_line_ids': [(6, 0, [line.id])]})
                        invoice_lines |= self.env[
                            'account.invoice.line'].create(vals)

        return invoice_lines
