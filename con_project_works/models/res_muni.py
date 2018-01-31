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

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCountryMunicipality(models.Model):
    _name = 'res.country.municipality'

    _description = "Municipality"
    _order = 'sequence, id'

    ''''''
    sequence = fields.Integer(help="Determine the display order", default=10)
    name = fields.Char(string="Name")
    state_id = fields.Many2one('res.country.state', string='State')
    code = fields.Char(string="Code")
    invoicing_area_id = fields.Many2one('invoicing.area',
                                        string='Invoicing Area', index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    municipality_ids = fields.One2many('res.country.municipality',
                                       'delivery_carrier_id',
                                       string='Municipality', copy=True,
                                       track_visibility='onchange')

    @api.onchange('state_ids')
    def onchange_states(self):
        """
        Onchange function that update the country_ids and municipality_ids
        with the correct municipality and country based on the given
        State/Province.

        :return: None
        """
        self.country_ids = [(6, 0, self.country_ids.ids +
                             self.state_ids.mapped('country_id.id'))]
        self.municipality_ids = [(6, 0, self.municipality_ids.ids +
                                  self.municipality_ids.mapped('state_id.id'))
                                 ]
