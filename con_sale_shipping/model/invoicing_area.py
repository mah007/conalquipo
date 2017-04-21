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

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class InvoicingArea(models.Model):
    _name = 'invoicing.area'
    _inherit = ['mail.thread']
    _description = "Invoicing Area"
    _order = 'sequence, id'
    _rec_name = 'name'

    sequence = fields.Integer(help="Determine the display order", default=10)

    code = fields.Char(string="Code", track_visibility='onchange')
    name = fields.Char(string="Name", track_visibility='onchange')
    state_id = fields.Many2one('res.country.state', string='State',
                                    track_visibility='onchange')
    country_municipality = fields.One2many('res.country.municipality',
                                           'invoicing_area_id',
                                           string='Municipality',
                                           track_visibility='onchange')

    @api.onchange('state_id')
    def onchange_states(self):

        self.country_municipality = [(6, 0, self.country_municipality.ids +
                                      self.country_municipality.mapped(
                                          'state_id.id'))]
