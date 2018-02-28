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

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class StockMoveComponents(models.Model):
    _inherit = "stock.move"

    button_pushed = fields.Boolean(
        string="Button pushed", default=False)   

    def get_components_button(self):
        if not self.product_id.components_ids:
            raise UserError(_("The following product '%s' dont"
                              " have components") % self.product_id.name)
        if self.product_id.components_ids and not self.button_pushed:
            for data in self.product_id.components_ids:
                name = data.product_child_id.product_tmpl_id.name
                uom = data.product_child_id.product_tmpl_id.uom_id.id
                self.env['stock.move'].create({
                    'name': _(
                        'Components:') + name,
                    'product_id': data.product_child_id.id,
                    'product_uom_qty': data.quantity,
                    'product_uom': uom,
                    'origin': self.origin,
                    'partner_id': self.partner_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.picking_id.id,
                    'state': self.state,
                    'group_id': self.group_id.id,
                    'rule_id': self.rule_id.id,
                    'picking_type_id': self.picking_type_id.id
                })
            self.button_pushed = True
        else:
            raise UserError(_("The following product '%s' already"
                              " has its components"
                              ) % self.product_id.name)

    @api.model
    def get_components_action(self):
        active_ids = self._context.get('active_ids')[0]
        move_obj = self.env['stock.move']
        move = move_obj.browse(active_ids)
        for moveid in move:
            _logger.warning(moveid)
            if moveid.product_id.components_ids and not move.button_pushed:
                for data in moveid.product_id.components_ids:
                    name = data.product_child_id.product_tmpl_id.name
                    uom = data.product_child_id.product_tmpl_id.uom_id.id
                    move_obj.create({
                        'name': _(
                            'Components:') + name,
                        'product_id': data.product_child_id.id,
                        'product_uom_qty': data.quantity,
                        'product_uom': uom,
                        'origin': moveid.origin,
                        'partner_id': moveid.partner_id.id,
                        'location_id': moveid.location_id.id,
                        'location_dest_id': moveid.location_dest_id.id,
                        'picking_id': moveid.picking_id.id,
                        'state': moveid.state,
                        'group_id': move.group_id.id,
                        'rule_id': moveid.rule_id.id,
                        'picking_type_id': moveid.picking_type_id.id
                    })
                move.button_pushed = True