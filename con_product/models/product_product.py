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


class ProductProduct(Model):
    _inherit = "product.product"

    @api.one
    def _get_default_loc(self):
        """
        This function get the default location configured on the stock
        location
        models and return to the `product_template` model else return
        False

        :return: Recordset or False
        """
        for data in self:
            if data.product_tmpl_id.type not in ['service', 'consu']:
                return self.env[
                    'stock.location'].search(
                        [('set_default_location', '=', True)],
                        limit=1) or False

    def _get_default_state(self):
        """
        This function get the default state configured on the product states
        models and return to the `product_template` model else return False

        :return: Recordset or False
        """
        for data in self:
            if data.type != 'service':
                data.state_id = self.env['product.states'].search([
                    ('default_value', '=', True)], limit=1) or False
            else:
                data.state_id = False

    def _get_default_color(self):
        """
        This function get the default state configured on the product states
        models and return to the `product_template` model else return False

        :return: Recordset or False
        """
        for data in self:
            if data.type != 'service' and data.location_id:
                data.color = data.location_id.color

    @api.onchange('location_id')
    def get_default_values(self):
        """
        This function brings the default location of the product from the
        state assigned to it.

        :return: None
        """
        if self.location_id.product_state:
            location_obj = self.env['stock.location']
            location = location_obj.search([('id', '=', self.location_id.id)])
            self.state_id = location.product_state.id
            self.color = location.color
        else:
            if self.location_id:
                raise UserError(_(
                    "The following location don't have a state asigned"))

    @api.onchange('state_id')
    def get_default_location(self):
        """
        This function brings the default location of the product from the
        state assigned to it.

        :return: None
        """
        if self.location_id.product_state:
            location_obj = self.env['stock.location']
            location = location_obj.search(
                [('location_id', '=', self.location_id.location_id.id),
                 ('product_state', '=', self.state_id.id)])
            self.location_id = location.id
        else:
            if self.location_id:
                raise UserError(_(
                    "The following location don't have a state asigned"))

    state_id = fields.Many2one('product.states', string="State",
                               compute="_get_default_state")
    color = fields.Char(string="Color",
                        help="Select the color of the state",
                        compute="_get_default_color")
    location_id = fields.Many2one(
        'stock.location', string="Actual location",
        default=_get_default_loc)

    @api.model
    def create(self, values):
        record = super(ProductProduct, self).create(values)
        pro_tmpl_obj = self.env['product.template']
        if values.get('product_tmpl_id'):
            pro_tmpl = pro_tmpl_obj.search(
                [('id', '=', values['product_tmpl_id'])])
            for pro in pro_tmpl:
                if pro.type != 'service':
                    record.location_id = pro.location_id.id
                    record.state_id = pro.state_id.id
                    record.color = pro.color
        return record
