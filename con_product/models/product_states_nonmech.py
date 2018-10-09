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
from odoo import fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductStatesNonMech(Model):
    _name = "product.states.nonmech"
    _description = "A model for store non mech product states"
    _rec_name = "state_name"
    _order = "qty"

    product_id = fields.Many2one(
        'product.product', string="Product parent")
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        related='product_id.product_tmpl_id')
    location_id = fields.Many2one(
        'stock.location',
        string="Location")
    state_name = fields.Many2one(
        'product.states', string="State")
    color = fields.Char(string="Color")
    qty = fields.Float(
        string="Quantity", compute="_compute_product_count")

    def _compute_product_count(self):
        """
        Method to count the products on locations
        """
        for record in self:
            quants = self.env[
                'stock.quant'].search(
                    [('product_id', '=', record.product_id.id),
                     ('location_id', '=', record.location_id.id)])
            for data in quants:
                record.qty = data.quantity
            if record.state_name.name == "Reserva":
                record.qty = record.product_tmpl_id.outgoing_qty
