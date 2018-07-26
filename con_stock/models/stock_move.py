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
    product_count = fields.Float(
        compute='_compute_product_count',
        string="On work",
        track_visibility='onchange')
    parent_sale_line = fields.Many2one(
        'sale.order.line',
        string='Parent sale line')

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        # Update parent_sale_line
        if res.sale_line_id.parent_line:
            res.update({
                'parent_sale_line': res.sale_line_id.parent_line.id})
        return res

    def _compute_product_count(self):
        """
        Method to count the products on works
        """
        for record in self:
            product_qty_in = 0.0
            product_qty_out = 0.0
            picking = self.env[
                'stock.picking'].search(
                    [['partner_id', '=', record.picking_id.partner_id.id],
                     ['location_dest_id.usage', 'in',
                      ['customer', 'internal']],
                     ['project_id', '=', record.picking_id.project_id.id]
                    ])
            for data in picking:
                moves = self.env[
                    'stock.move'].search(
                        [['picking_id', '=', data.id],
                         ['location_dest_id',
                          '=',
                          data.location_dest_id.id],
                         ['product_id', '=', record.product_id.id],
                         ['state', '=', 'done']])
                if moves:
                    for p in moves:
                        if not p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'customer' and \
                           p.picking_id.location_id.usage \
                           == 'internal':
                            product_qty_in += p.product_uom_qty
                        if p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'internal' and \
                           p.picking_id.location_id.usage \
                           == 'customer':
                            product_qty_out += p.product_uom_qty
            record.product_count = product_qty_in - product_qty_out

    @api.onchange('employee_id')
    def employee_id_change_task(self):
        if self.employee_id:
            task = self.env['project.task'].search(
                [('sale_line_id', '=', self._origin.sale_line_id.id)])
            if task:
                task.update({'user_id': self.employee_id.user_id.id})

    @api.model
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for data in self:
            task = self.env['project.task'].search(
                [('sale_line_id', '=', data.sale_line_id.id)])
            if task:
                task.write({'user_id': data.employee_id.user_id.id})
        return res

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
        for data in other:
            # Get the operators employees ids
            for data2 in data.product_id.product_tmpl_id.employee_ids:
                employee_list.append(data2.id)
            # Domain for employee operator for the product
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
        if res.product_id.is_operated:
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
