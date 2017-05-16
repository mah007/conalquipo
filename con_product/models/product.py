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
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from odoo.models import Model, api, _
from odoo import fields


class ProductStates(Model):
    _name = "product.states"
    _description = "A model for store and manage the products states"

    name = fields.Char(string="Name",
                       help="The name for the state for example:"
                            "Fixing, Unavailable, sold, etc..")
    sequence = fields.Integer(string="Sequence",
                              help="The sequence priority the state"
                                   " will be ordered following this sequence")
    description = fields.Text(string="Description",
                              help="A little description about the state")
    default_value = fields.Boolean(string="Set as a default value"
                                          " when the product is created")
    unavailable = fields.Boolean(string="Make the product unavailable when "
                                        "the product have this state",
                                 help="Make the product unavailable when "
                                        "the product have this state")


class ProductTemplate(Model):
    _inherit = "product.template"

    def _get_default_state(self):
            return self.env['product.states'].search(
                [('default_value', '=', 'True')], limit=1) or False

    state_id = fields.Many2one('product.states', string="State",
                               default=_get_default_state)
    # ~ This field exist in product.template
    # but i don't found the used of this in the Odoo 10.0e code because
    # that i've decided create this field again.
    rental = fields.Boolean('Can be Rent')
    # ~


class ProductProduct(Model):
    _inherit = "product.product"

    def _get_default_state(self):
            return self.env['product.states'].search(
                [('default_value', '=', 'True')], limit=1) or False

    state_id = fields.Many2one('product.states', string="State",
                               default=_get_default_state)


class MrpBom(Model):
    _inherit = "mrp.bom"

    type = fields.Selection(selection_add=[('components', 'Components')])
