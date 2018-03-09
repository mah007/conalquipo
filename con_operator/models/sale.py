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
import logging


_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('order_line')
    def order_line_change(self):
        if self.order_line:
            i = len(self.order_line)
            line = self.order_line[i-1]
            if line.service_operator:
                _logger.info("!!!!!!!!!!!!!!!! %s ", line)
                values = {
                    'product_id': line.service_operator.id,
                    'name': line.service_operator.name,
                    'product_uom': line.service_operator.uom_id.id,
                    'product_uom_qty': 1,
                    'service_operator': False,
                    'mess_operated': False,
                    'add_operator': False,
                    'owner_id': False,
                    'owner_id': False,
                    'order_id': line.order_id,
                    'product_operate': line.product_id.id,
                    'invoice_status': 'no',
                    'bill_uom': False, 'discount': 0,
                    'product_subleased': False, 'product_updatable': True,
                    'qty_invoiced': 0, 'route_id': False,
                    'analytic_tag_ids': [[6, False, []]], 'bill_uom_qty': 0,
                    'qty_delivered': 0, 'end_date': False,
                    'order_type': 'rent',
                    'invoice_lines': [[6, False, []]],
                    'product_packaging': False,
                    'price_subtotal': 40000,
                    'state': 'draft',
                    'product_qty': 1,
                    'qty_delivered_updateable': False,
                    'customer_lead': 0,
                    'start_date': False,
                    'qty_to_invoice': 0, 'tax_id': [[6, False, [9]]],
                    'price_unit': 40000,

                }
                new_line = self.order_line.new(values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    add_operator = fields.Boolean('Add Operator')
    mess_operated = fields.Boolean('Message Operated', default=False)
    service_operator = fields.Many2one('product.product',
                                       string='Service Operator',
                                       domain=[('sale_ok', '=', True),
                                               ('type', '=', 'service')],
                                       change_default=True, ondelete='restrict')
    product_operate = fields.Many2one('product.product',
                                      string='Product Operate',
                                      domain=[('sale_ok', '=', True),
                                              ('type', '=', 'service')],
                                      change_default=True, ondelete='restrict')
    assigned_operator = fields.Many2one('res.users', string="Assigned Operator")

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):

        result = super(SaleOrderLine, self).product_id_change()
        if self.product_id.is_operated:
            self.mess_operated = True

        return result

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):

        if self.assigned_operator:
            self.mess_operated = False
            move = self.env['stock.move'].search([('sale_line_id', '=', self.id)])
            for line in move.move_line_ids:
                line.write({'assigned_operator': self.assigned_operator})

    @api.model
    def new(self, values={}, ref=None):
        record = super(SaleOrderLine, self).new(values)

        if values.get('service_operator'):
            _logger.info("+++++++++++ %s ", values)

        return record
