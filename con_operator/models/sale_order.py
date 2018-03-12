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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    operators_services = fields.Integer(string="Operator Services")

    @api.multi
    @api.onchange('order_line')
    def order_line_change(self):
        """On Changed function on line orders.

          This function count the line that have a operator and update the
          field operators_service with a integer value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              None: Not return any value, only update the operator_service
              fields on sale order.

        """
        if self.order_line:
            operators = self.order_line.filtered(lambda line: line.add_operator)
            _logger.info("Operators %s" % operators)
            self.operators_services = len(operators)



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
        """Overloaded on changed function for product_id.

          This overload check if the line have a operator and update the
          field mess_operated with a boolean value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the product information.

        """
        result = super(SaleOrderLine, self).product_id_change()
        if self.product_id.is_operated:
            self.mess_operated = True

        return result

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
            move = self.env['stock.move'].search([('sale_line_id', '=', self.id)])
            for line in move.move_line_ids:
                line.write({'assigned_operator': self.assigned_operator})

    @api.model
    def create(self, values={}):
        """Overload create function.

          This change create a extra line for all the products that have a
          assigned operator:

          Args:
              self (record): Encapsulate instance object.
              values (dict): Dictionary with the field's values.

          Returns:
              Int: Return the record id created.

        """
        record = super(SaleOrderLine, self).create(values)
        if values.get('service_operator'):
            new_line = values.copy()
            new_line.update({
                'product_id': values['service_operator'],
                'name': 'Attach Operator over %s'%(values['name']),
                'product_operate': values['product_id'],
            })
            new_line.pop('service_operator')
            # ~ Create new record for operator
            super(SaleOrderLine, self).sudo().create(new_line)
        _logger.info("Record Values on %s"%record)
        return record
