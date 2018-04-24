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

from odoo.models import Model, api, _
from odoo import fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class StockMove(Model):
    _inherit = "stock.move"

    project_id = fields.Many2one(
        'project.project', string='Works')
    partner_id = fields.Many2one(
        'res.partner', string='Partner')
    child_product = fields.Boolean(
        string="Child product", default=False)
    mrp_repair_id = fields.Many2one(
        'mrp.repair', string='Repair request')
    employee_ids = fields.Many2many(
        'hr.employee', string='Operators',
        related="product_id.employee_ids", readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Operator')
    description = fields.Char(
        string='Description')
    returned = fields.Integer('returned')

    def _action_done(self, merge=True):
        res = super(StockMove, self)._action_done()
        for order in self:
            if order.state == 'done' and order.returned:
                move = order.env['stock.move'].search(
                    [('id', '=', order.returned)], limit=1)
                if move:
                    move.write(
                        {'origin_returned_move_id': order.id})
        return res

    def get_components_info(self):
        """
        Button to get info components of a product
        """
        other = self.env['stock.move'].search([
            ('picking_id', '=', self.picking_id.id),
            ('origin', '=', self.origin)])
        for pr in other:
            if pr.sale_line_id and not pr.description:
                code_line = pr.sale_line_id.name
                pr.write({'description': code_line})

    @api.model
    def getemployee(self):
        # Domain for the operators
        employee_list = []
        other = self.env['stock.move'].search([
            ('picking_id', '=', self.picking_id.id),
            ('origin', '=', self.origin)])
        _logger.warning(other)
        for data in other:
            # Get the operators employees ids
            for data2 in data.product_id.product_tmpl_id.employee_ids:
                employee_list.append(data2.id)
            # Domain for employee operator for the product
            _logger.warning('ACAAAAAAAAAA')
            _logger.warning(employee_list)
            _logger.warning(self)
            return [('id', 'in', employee_list)]


class StockMoveLine(Model):
    _inherit = "stock.move.line"

    project_id = fields.Many2one(
        'project.project', string='Works')
    partner_id = fields.Many2one(
        'res.partner', string='Partner')
    assigned_operator = fields.Many2one(
        'hr.employee', string="Assigned Operator")

    @api.model
    def create(self, vals):
        res = super(StockMoveLine, self).create(vals)

        if res.product_id.is_operated \
                and res.move_id.sale_line_id.service_operator:
            res.picking_id.update({'mess_operated': True})

        return res

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):
        if self.assigned_operator:
            mess_operated = False
            for line in self.move.move_line_ids:
                if not line.assigned_operator:
                    mess_operated = True
            self.move.picking_id.write({'mess_operated': mess_operated})
