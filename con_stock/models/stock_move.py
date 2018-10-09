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


class StockMoveHistory(Model):
    _name = "stock.move.history"

    picking_id = fields.Many2one("stock.picking", string="Picking")
    partner_id = fields.Many2one("res.partner", string="Partner")
    project_id = fields.Many2one("project.project", string="Project")
    product_id = fields.Many2one("product.product", string="Product")
    code = fields.Selection(
        [('incoming', 'DEV'), ('outgoing', 'REM'),
         ('internal', 'INI')], 'Type of Operation',
        default='internal')
    product_count = fields.Float(string="On work")
    quantity_done = fields.Float(string="Qty done")
    quantity_project = fields.Float(
        string="Qty Project", compute='_compute_quantity_project', store=False)
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Line')
    move_id = fields.Many2one('stock.move', string="Move")
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'move_history_id', help="Invoice Lines")
    date = fields.Datetime(compute='_compute_date', store=True, help="Date")

    @api.depends('move_id.date_expected', 'picking_id.advertisement_date')
    def _compute_date(self):
        """
        Method compute date
        """
        for record in self:
            if record.picking_id.advertisement_date:
                record.date = record.picking_id.advertisement_date
            else:
                record.date = record.move_id.date_expected

    def _compute_quantity_project(self):
        """Method calc quantity in project"""
        for record in self:
            pick_out = self.search([('product_id', '=', record.product_id.id),
                                    ('project_id', '=', record.project_id.id),
                                    ('partner_id', '=', record.partner_id.id),
                                    ('code', '=', 'outgoing'),
                                    ('date', '<=', record.date),
                                    ('picking_id.state', '=', 'done'),
                                    ('move_id.parent_sale_line', '=', False)])
            pick_out = pick_out.filtered(
                lambda h: h.move_id.location_dest_id.usage == 'customer')

            pick_in = self.search([('product_id', '=', record.product_id.id),
                                   ('project_id', '=', record.project_id.id),
                                   ('partner_id', '=', record.partner_id.id),
                                   ('code', '=', 'incoming'),
                                   ('date', '<=', record.date),
                                   ('picking_id.state', '=', 'done'),
                                   ('move_id.parent_sale_line', '=', False)])
            pick_in = pick_in.filtered(
                lambda h: h.move_id.returned and h.move_id.location_dest_id.return_location) # noqa
            quantity = sum(pick_out.mapped('quantity_done')) - sum(
                pick_in.mapped('quantity_done'))

            record.quantity_project = quantity


class StockMove(Model):
    _inherit = "stock.move"

    project_id = fields.Many2one(
        'project.project', 'Works',
        related='picking_id.project_id', store=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner')
    child_product = fields.Boolean(
        string="Child product", default=False)
    mrp_repair_id = fields.Many2one(
        'repair', string='Repair request')
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
    qty_history = fields.Float(
        compute='_compute_product_history',
        string="History on work",
        track_visibility='onchange', store=True)
    advertisement_date = fields.Date(
        string="Advertisement date",
        related="picking_id.advertisement_date", store=True)

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
                     ['project_id', '=', record.picking_id.project_id.id]])
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

    @api.depends('quantity_done')
    def _compute_product_history(self):
        for rec in self:
            if rec.picking_id.picking_type_id.code == 'outgoing':
                current_qty = (rec.product_count - rec.quantity_done)
                _logger.info("Outgoing")
                _logger.info("Current Qty: {}".format(current_qty))
                rec.qty_history = current_qty if current_qty > 0 else 0
            elif rec.picking_id.picking_type_id.code == 'incoming':
                current_qty = ((rec.quantity_done * 2) - rec.product_count)
                _logger.info("Incoming")
                _logger.info("Current Qty: {}".format(current_qty))
                rec.qty_history = current_qty if current_qty > 0 else 0

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
        # This block create a history entry
        history = self.env['stock.move.history']
        for order in res:
            if order.picking_id.picking_type_id.code != 'internal':
                date = order.picking_id.advertisement_date \
                    or order.date_expected
                m_histories = history.search(
                    [('partner_id', '=', order.picking_id.partner_id.id),
                     ('project_id', '=', order.picking_id.project_id.id),
                     ('product_id', '=', order.product_id.id),
                     ('date', '>=', date),
                     ])
                m_histories = m_histories.filtered(
                    lambda h: h.invoice_line_ids
                    and h.invoice_line_ids.filtered(
                        lambda b: b.invoice_id.state != 'cancel'))
                if m_histories:
                    raise UserError(_(
                        'The move of the product %s, can not be generated '
                        'for this period, since it is in the following '
                        'invoices: %s') % (
                            order.product_id.name,
                            ', '.join(list(set([li.invoice_id.name or li.invoice_id.origin for li in m_histories.mapped('invoice_line_ids')]))))) # noqa
                vals = {
                    'picking_id': order.picking_id.id,
                    'partner_id': order.picking_id.partner_id.id,
                    'project_id': order.picking_id.project_id.id,
                    'product_id': order.product_id.id,
                    'code': order.picking_id.picking_type_id.code,
                    'product_count': order.product_count,
                    'quantity_done': order.quantity_done,
                    'sale_line_id': order.sale_line_id.id,
                    'move_id': order.id,
                }
                _logger.info(
                    "Creating history entry on table stock.move.history")
                history.create(vals)
                _logger.info("History entry creation successful")
        # end of history entry
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

