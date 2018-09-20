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
                             'end_date_invoice': self.end_date_invoice})

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
                if timesheet.create_date >= \
                        init_date_invoice and \
                                timesheet.create_date <= \
                                end_date_invoice:
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
            self, domain=[], reference=False, invoice_id=False, move_type=''):
        result = []
        if not domain:
            return {}

        self.ensure_one()

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

        moves = self.env['stock.move'].search(domain)
        date_end = None
        date_init = None
        date_move = None

        for mv in moves:
            qty = 0.0
            if reference == 'DEV':
                date_end = fields.Date.from_string(
                    mv.advertisement_date)
                date_init = fields.Date.from_string(
                    self.order_id.end_date_invoice)
                date_move = fields.Date.from_string(
                    mv.advertisement_date)
                # Get delta days
                delta = date_init - date_end

            elif reference == 'REM':
                end_move = self.env['stock.move']

                import pdb;
                pdb.set_trace()

                date_end = fields.Date.from_string(
                    self.order_id.end_date_invoice)
                date_init = fields.Date.from_string(
                    mv.date_expected)

                has_return = self.env['stock.move'].search(
                    [('product_id', '=', self.product_id.id),
                     ('project_id', '=', self.order_id.project_id.id),
                     ('partner_id', '=', self.order_id.partner_id.id),
                     ('advertisement_date', '>=', mv.date_expected),
                     ('advertisement_date', '<=', self.order_id.end_date_invoice),
                     ('sale_line_id', '=', self.id),
                     ('parent_sale_line', '=', False),
                     ('location_dest_id.return_location', '=', True),
                     ('picking_id.state', '=', 'done')])


                has_delivery = self.env['stock.move'].search(
                    [('product_id', '=', self.product_id.id),
                     ('project_id', '=', self.order_id.project_id.id),
                     ('partner_id', '=', self.order_id.partner_id.id),
                     ('date_expected', '>=', mv.date_expected),
                     ('date_expected', '<=', self.order_id.end_date_invoice),
                     ('sale_line_id', '=', self.id),
                     ('parent_sale_line', '=', False),
                     ('location_dest_id.return_location', '=', True),
                     ('picking_id.state', '=', 'done')])

                if has_return or has_delivery:
                    closet_to = min(has_return + has_delivery)
                    date_end = fields.Date.from_string(
                        closet_to.advertisement_date or
                        closet_to.date_expected)

                date_move = fields.Date.from_string(
                    mv.date_expected)
                # Get delta days
                delta = date_end - date_init

            elif reference == 'INI':
                date_end = fields.Date.from_string(
                    self.order_id.end_date_invoice)
                date_init = fields.Date.from_string(
                    self.order_id.init_date_invoice)
                date_move = fields.Date.from_string(
                    self.order_id.init_date_invoice)

                future_return = self.env['stock.move'].search(
                    [('product_id', '=', self.product_id.id),
                     ('project_id', '=', self.order_id.project_id.id),
                     ('partner_id', '=', self.order_id.partner_id.id),
                     ('advertisement_date', '>=',
                      self.order_id.init_date_invoice),
                     ('advertisement_date', '>=',
                      self.order_id.end_date_invoice),
                     ('sale_line_id', '=', self.id),
                     ('parent_sale_line', '=', False),
                     ('location_dest_id.return_location', '=', True),
                     ('picking_id.state', '=', 'done')])

                if future_return:
                    date_end = fields.Date.from_string(
                        future_return.advertisement_date)

                past_return = self.env['stock.move'].search(
                    [('product_id', '=', self.product_id.id),
                     ('project_id', '=', self.order_id.project_id.id),
                     ('partner_id', '=', self.order_id.partner_id.id),
                     ('advertisement_date', '<=',
                      self.order_id.init_date_invoice),
                     ('sale_line_id', '=', self.id),
                     ('parent_sale_line', '=', False),
                     ('location_dest_id.return_location', '=', True),
                     ('picking_id.state', '=', 'done')])

                if past_return:
                    continue

                # Get delta days
                delta = date_end - date_init

            if mv.returned and \
                    mv.location_dest_id.return_location \
                    and mv.picking_id.state == 'done':
                move_type = 'incoming'

            elif mv.location_dest_id.usage \
                    == 'customer' and mv.picking_id.state \
                    == 'done':
                move_type = 'outgoing'


            # Get tasks values
            qty = self.get_qty_tasks(
                self.order_id.init_date_invoice,
                date_end, mv, delta)
            # Get product count history
            history = self.get_history(mv, move_type)
            # Create returned product invoice
            inv_line = {
                "date_move": date_move,
                'invoice_id': invoice_id,
                "name": self.product_id.name,
                "account_id": account.id,
                "price_unit": self.price_unit,
                "document": reference if reference == 'INI'
                           else mv.picking_id.name,
                'sequence': self.sequence,
                'origin': self.order_id.name,
                "uom_id": self.product_uom.id,
                "product_id": self.product_id.id,
                "bill_uom": self.bill_uom.id,
                "discount": self.discount,
                "qty_remmisions": history.quantity_done
                if move_type ==  'outgoing' else 0.00,
                "qty_returned": history.quantity_done
                if move_type ==  'incoming' else 0.00,
                "date_init": date_init.day if move_type == 'outgoing' else
                date_end.day,
                "date_end": date_end.day if move_type == 'outgoing' else
                date_init.day,
                "num_days": delta.days + 1,
                "quantity": qty,
                "parent_sale_line": self.parent_line.id,
                "products_on_work": history.product_count,
                "invoice_line_tax_ids":
                    [(6, 0, self.tax_id.ids)],
                "layout_category_id":
                    self.layout_category_id.id,
                'account_analytic_id': self.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'sale_line_ids': [(6, 0, [self.id])]
                if move_type == 'outgoing' else False,
            }

            if history.product_count == 0.0:
                inv_line['price_unit'] = 0.0

            result.append(inv_line)
        _logger.warning(result)
        return result

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
             ('date_expected', '>=', self.order_id.init_date_invoice),
             ('date_expected', '<=', self.order_id.end_date_invoice),
             ('advertisement_date', '=', False),
             ('sale_line_id', '=', self.id),
             ('parent_sale_line', '=', False)], 'REM'),

            ([('product_id', '=', self.product_id.id),
             ('project_id', '=', self.order_id.project_id.id),
             ('partner_id', '=', self.order_id.partner_id.id),
             ('advertisement_date', '>=', self.order_id.init_date_invoice),
             ('advertisement_date', '<=', self.order_id.end_date_invoice),
             ('sale_line_id', '=', self.id),
             ('parent_sale_line', '=', False),
             ('location_dest_id.return_location', '=', True),
             ('picking_id.state', '=', 'done')], 'DEV'),

            ([('product_id', '=', self.product_id.id),
             ('project_id', '=', self.order_id.project_id.id),
             ('partner_id', '=', self.order_id.partner_id.id),
             ('date_expected', '<', self.order_id.init_date_invoice),
             ('advertisement_date', '=', False),
             ('parent_sale_line', '=', False)], 'INI'),
        ]

        _logger.warning(search_op)

        if self.order_id.order_type not in ['rent']:
            invoice_lines = super(SaleOrderLine, self).invoice_line_create(
                invoice_id, qty)
        else:
            vals = []
            invoice_lines = self.env['account.invoice.line']
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            # Get REM
            for line in self:

                if not float_is_zero(qty, precision_digits=precision):
                    for op in search_op:
                        vals = line._prepare_invoice_line_from_stock(
                            domain=op[0], reference=op[1],
                            invoice_id=invoice_id)
                        for val in vals:
                            invoice_lines |= self.env['account.invoice.line']\
                                .create(val)
        return invoice_lines

