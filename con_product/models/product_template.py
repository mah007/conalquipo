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


class ProductTemplate(Model):
    _inherit = "product.template"

    @api.onchange('type')
    def get_type(self):
        if self.type in ['service', 'consu']:
            self.location_id = False
            self.state_id = False
            self.color = False
        else:
            self.location_id = self.env[
                'stock.location'].search(
                    [('set_default_location', '=', True)], limit=1) or False

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

    @api.one
    def _get_default_loc(self):
        """
        This function get the default location configured
        on the stock location
        models and return to the `product_template`
        model else return False

        :return: Recordset or False
        """
        for location in self:
            if location.type not in ['service', 'consu']:
                return self.env[
                    'stock.location'].search(
                        [('set_default_location', '=', True)],
                        limit=1) or False

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

    def _get_default_color(self):
        """
        This function get the default state configured on the product states
        models and return to the `product_template` model else return False

        :return: Recordset or False
        """
        for data in self:
            if data.type != 'service' and data.location_id:
                data.color = data.location_id.color

    @api.onchange('replenishment_charge')
    def replenishment_charge_validation(self):
        """
        Validation for replenishment_charge: Needs to be service type
        """
        if self.replenishment_charge and \
           not self.replenishment_charge.type == "service":
            raise UserError(_(
                "This product needs to be a service type"))

    state_id = fields.Many2one(
        'product.states', string="State",
        compute="_get_default_state")
    color = fields.Char(
        string="Color",
        help="Select the color of the state",
        compute="_get_default_color")
    location_id = fields.Many2one(
        'stock.location', string="Actual location",
        default=_get_default_loc)
    rental = fields.Boolean('Can be Rent')
    components = fields.Boolean(string="Has components?",
                                help="if this field is true the bills "
                                     "of material of the product is treated "
                                     "as a set of components adding this "
                                     "product in the picking",
                                default=False)
    components_ids = fields.One2many(
        'product.components', 'product_id', string='Components')
    product_origin = fields.Many2one(
        'stock.location',
        string="Location Origin",
        domain=[('usage', '=', 'internal')])
    replenishment_charge = fields.Many2one(
        'product.template', string='Replenishment charge')
    min_qty_rental = fields.Integer(string='Min Qty rental')
    multiples_uom = fields.Boolean(
        string="Has multiples uom?",
        default=False)
    uoms_ids = fields.One2many(
        'product.multiples.uom', 'product_id', string='Multiples UOMs')
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employee',
        search='hr_employee', track_visibility='onchange')
    is_operated = fields.Boolean(
        string='Is Operated')
    sale_uom = fields.Many2one(
        'uom.uom',
        string='Sale UoM')
    for_shipping = fields.Boolean(
        string='Use for shipping?')
    non_mech = fields.Boolean(
        string='Not mechanical?')
    states_nonmech_ids = fields.One2many(
        'product.states.nonmech', 'product_tmpl_id', string='Location')
    more_information = fields.Text(
        'More information', translate=True)
    layout_sec_id = fields.Many2one(
        'sale.layout_category', string="Section")

    @api.onchange('multiples_uom')
    def _compute_multiples_uom(self):
        if self.multiples_uom:
            self.sale_uom = False

    @api.onchange('non_mech')
    def _compute_locations(self):
        if self.non_mech:
            line_ids = []
            reserved_qty = []
            self.states_nonmech_ids = [(5,)]
            self.location_id = False
            self.state_id = False
            self.color = False
            product = self.env[
                'product.product'].search(
                    [('product_tmpl_id', '=', self._origin.id)])
            quants = self.env[
                'stock.quant'].search(
                    [('product_id', '=', product.id)])
            if quants:
                for data in quants:
                    pro = data.product_id.product_tmpl_id.id
                    loc = data.location_id
                    state = data.location_id.product_state.id
                    color = data.location_id.color
                    if loc.usage not in ['view', 'inventory', 'virtual']:
                        val = {
                            'product_id': pro,
                            'location_id': loc.id,
                            'state_name': state,
                            'color': color,
                            'qty': data.quantity
                        }
                        line_ids.append((0, 0, val))
                        if data.location_id.product_state.name \
                                == 'Existencias':
                            reserved_qty.append(data.reserved_quantity)
            # Just for reserved location
            if reserved_qty:
                reserved_location = self.env[
                    'stock.location'].search(
                        [('product_state.name', '=', 'Reserva')])
                for data_reserved in reserved_location:
                    val = {
                        'product_id': product.id,
                        'location_id': data_reserved.id,
                        'state_name': data_reserved.product_state.id,
                        'color': data_reserved.color,
                        'qty': sum(reserved_qty)
                    }
                    line_ids.append((0, 0, val))
            self.states_nonmech_ids = [
                i for n, i in enumerate(
                    line_ids) if i not in line_ids[n + 1:]]
        else:
            self.states_nonmech_ids = [(5,)]
            self.location_id = self._get_default_loc()
