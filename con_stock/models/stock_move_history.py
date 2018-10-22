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
