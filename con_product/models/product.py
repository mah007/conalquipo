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


class ProductStates(Model):
    _name = "product.states"
    _description = "A model for store and manage the products states"

    @api.multi
    @api.onchange('default_value')
    def get_default_value(self):
        active_states = self.search([('default_value', '=', True)])
        if active_states and self.default_value:
            raise UserError(_("The following state '%s' is the actual default"
                              " for all products") % active_states[0].name)

    name = fields.Char(string="Name",
                       help="The name for the state for example:"
                            "Fixing, Unavailable, sold, etc..")
    sequence = fields.Integer(string="Sequence",
                              help="The sequence priority the state"
                                   " will be ordered following this sequence")
    color = fields.Char(string="Color", default="#FFFFFF",
                        help="Select the color of the state")
    description = fields.Text(string="Description",
                              help="A little description about the state")
    default_value = fields.Boolean(string="Set as a default value"
                                          " when the product is created",
                                   default=False)
    unavailable = fields.Boolean(string="Make the product unavailable when "
                                        "the product have this state",
                                 help="Make the product unavailable when "
                                        "the product have this state")

    _sql_constraints = [
        ('name_sequence',
         'UNIQUE(sequence)',
         "The sequence must be unique and right now already exists"),
    ]

    @api.model
    def create(self, values):
        record = super(ProductStates, self).create(values)
        active_states = self.search([('default_value', '=', True),
                                     ('id', '!=', self.id)])
        if active_states and self.default_value:
            raise UserError(_("The following state '%s' is the actual default"
                              " for all products") % active_states[0].name)
        return record

    @api.multi
    def write(self, values):
        record = super(ProductStates, self).write(values)
        active_states = self.search([('default_value', '=', True),
                                     ('id', '!=', self.id)])
        if active_states and self.default_value:
            raise UserError(_("The following state '%s' is the actual default"
                              " for all products") % active_states[0].name)
        return record


class ProductTemplate(Model):
    _inherit = "product.template"

    @api.multi
    def _get_default_state(self):
            return self.env['product.states'].search(
                [('default_value', '=', True)], limit=1) or False

    @api.multi
    @api.onchange('state_id')
    def get_default_values(self):
        if self.state_id:
            self.color = self.state_id.color
            location_obj = self.env['stock.location']
            location = location_obj.search([('color', '=', self.color)])
            self.location_id = location.id

    state_id = fields.Many2one('product.states', string="State",
                               default=_get_default_state)
    color = fields.Char(string="Color", default="#FFFFFF",
                        help="Select the color of the state")
    location_id = fields.Many2one('stock.location', string="Actual location")
    rental = fields.Boolean('Can be Rent')
    components = fields.Boolean(string="Has components?",
                                help="if this field is true the bills "
                                     "of material of the product is treated "
                                     "as a set of components adding this "
                                     "product in the picking",
                                default=False)


class ProductProduct(Model):
    _inherit = "product.product"

    @api.multi
    def _get_default_state(self):
            return self.env['product.states'].search(
                [('default_value', '=', True)], limit=1) or False

    @api.multi
    @api.onchange('state_id')
    def get_default_values(self):
        if self.state_id:
            self.color = self.state_id.color
            location_obj = self.env['stock.location']
            location = location_obj.search([('color', '=', self.color)])
            self.location_id = location.id

    state_id = fields.Many2one('product.states', string="State",
                               default=_get_default_state)
    color = fields.Char(string="Color", default="#FFFFFF",
                        help="Select the color of the state")
    location_id = fields.Many2one('stock.location', string="Actual location")
