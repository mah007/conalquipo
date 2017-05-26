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
from odoo import fields


class StockLocation(Model):
    _inherit = "stock.location"

    set_product_state = fields.Boolean(
        string="Change the state to all products when arrive to this location")

    product_state = fields.Many2one('product.states', string="Set state")


class StockPicking(Model):
    _inherit = "stock.picking"

    def do_transfer(self):
        result = super(StockPicking, self).do_transfer()
        # ~ Change the product state when is moved to other location.
        for picking in self:
            for move in picking.move_lines:
                if move.product_id.rental:
                    move.product_id.state_id = \
                        move.location_dest_id.product_state.id
        return result


class StockMove(Model):
    _inherit = "stock.move"

    manual_create = fields.Boolean(string="Not Auto", default=False)
    not_explode = fields.Boolean(string="Don't explode",
                                 help="This flag don't repeat "
                                      "the method explode for this move",
                                 defualt=False)

    def action_explode(self):
        """ Explodes pickings """
        # in order to explode a move, we must have a picking
        # _type_id on that move because otherwise the move
        # won't be assigned to a picking and it would be
        #  weird to explode a move into several if they aren't
        # all grouped in the same picking.

        # ~ This validations is for the products with components
        if self.not_explode:
            return self

        if not self.picking_type_id:
            return self
        bom = self.env['mrp.bom'].sudo()._bom_find(product=self.product_id)
        if not bom or bom.type != 'phantom':
            return self
        phantom_moves = self.env['stock.move']
        processed_moves = self.env['stock.move']
        factor = self.product_uom._compute_quantity(
            self.product_uom_qty, bom.product_uom_id) / bom.product_qty
        boms, lines = bom.sudo().explode(self.product_id, factor,
                                         picking_type=bom.picking_type_id)
        for bom_line, line_data in lines:
            phantom_moves += self._generate_move_phantom(bom_line,
                                                         line_data['qty'])

        for new_move in phantom_moves:
            processed_moves |= new_move.action_explode()
        if not self.split_from and self.procurement_id:
            # Check if procurements have been made to wait for
            moves = self.procurement_id.move_ids
            if len(moves) == 1:
                self.procurement_id.write({'state': 'done'})
        if processed_moves and self.state == 'assigned':
            # Set the state of resulting moves according
            #  to 'assigned' as the original move is assigned
            processed_moves.write({'state': 'assigned'})
        # delete the move with original product which is not relevant anymore
        if self.manual_create:
            self.sudo().copy({'not_explode': True})

        self.sudo().unlink()
        return processed_moves
