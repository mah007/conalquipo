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


class StockMoveComponents(models.Model):
    _inherit = "stock.move"

    button_pushed = fields.Boolean(string="Button pushed")

    def get_components(self):
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
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.picking_id.id
                })
            self.button_pushed = True
        else:
            raise UserError(_("The following product '%s' already"
                              " has its components"
                              ) % self.product_id.name)
