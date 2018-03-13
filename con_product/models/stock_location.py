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

from odoo.models import Model
from odoo import fields, api
import logging
_logger = logging.getLogger(__name__)


class StockLocation(Model):
    _inherit = "stock.location"

    @api.multi
    @api.depends('product_state')
    def _get_color(self):
        for a in self:
            if a.product_state:
                a.color = a.product_state.color

    set_product_state = fields.Boolean(
        string="Change the state to all products when arrive to this location")
    product_state = fields.Many2one('product.states', string="Set state")
    color = fields.Char(string="Color", compute=_get_color, store=True)


class StockPicking(Model):
    _inherit = "stock.picking"

    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        # ~ Change the product state when is moved to other location.
        for picking in self:
            for move in picking.move_lines:
                if move.product_id.rental:
                    move.product_id.write(
                        {'state_id': move.location_dest_id.product_state.id,
                         'color': move.location_dest_id.color,
                         'location_id': move.location_dest_id.id})
                    move.product_id.product_tmpl_id.write(
                        {'state_id': move.location_dest_id.product_state.id,
                         'color': move.location_dest_id.color,
                         'location_id': move.location_dest_id.id})
        return result


class StockInventory(Model):
    _inherit = "stock.inventory"

    def action_done(self):
        result = super(StockInventory, self).action_done()
        # ~ Change the product state when is moved to other location.
        for data in self:
            for line in data.line_ids:
                if line.product_id.rental:
                    line.product_id.write(
                        {'state_id': line.location_id.product_state.id,
                         'color': line.location_id.color,
                         'location_id': line.location_id.id})
                    line.product_id.product_tmpl_id.write(
                        {'state_id': line.location_id.product_state.id,
                         'color': line.location_id.color,
                         'location_id': line.location_id.id})
        return result