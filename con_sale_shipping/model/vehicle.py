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


class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = ['mail.thread']
    _description = "Vehicle"
    _order = 'sequence, id'
    _rec_name = 'license_plate'

    sequence = fields.Integer(help="Determine the display order", default=10)
    holder = fields.Many2one('res.partner', 'Holder',
                             track_visibility='onchange')
    license_plate = fields.Char(string="license Plate",
                                track_visibility='onchange')
    mark = fields.Char(string="Mark", track_visibility='onchange')
    reference = fields.Char(string="Reference", track_visibility='onchange')
    model = fields.Integer(string="Model", track_visibility='onchange')
    type = fields.Many2one('vehicle.type', string='Type',
                           track_visibility='onchange')
    color = fields.Char(string="Color", track_visibility='onchange')
    num_motor = fields.Char(string="Number Motor", track_visibility='onchange')
    num_chasis = fields.Char(string="Number Chasis",
                             track_visibility='onchange')
    capacity = fields.Char(string="Capacity", track_visibility='onchange')
    traffic = fields.Many2one('res.country.municipality', string='Traffic',
                              track_visibility='onchange')
    licence_date = fields.Date('Licence Date', track_visibility='onchange',
                               default=fields.Date.context_today)
    soat = fields.Date('SOAT', default=fields.Date.context_today,
                       track_visibility='onchange')
    tec_mechanic = fields.Date('Tec Mechanic', track_visibility='onchange',
                               default=fields.Date.context_today)
    gravamen = fields.Date('Gravamen', default=fields.Date.context_today,
                           track_visibility='onchange')
    bearing = fields.Date('Bearing', default=fields.Date.context_today,
                          track_visibility='onchange')
    affiliation = fields.Date('Affiliation', default=fields.Date.context_today,
                              track_visibility='onchange')
    state = fields.Many2one('vehicle.state', string='State',
                            track_visibility='onchange')


class VehicleType(models.Model):
    _name = 'vehicle.type'

    _description = "Vehicle Type"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Determine the display order", default=10,
                              invisible=True)
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")


class VehicleState(models.Model):
    _name = 'vehicle.state'

    _description = "Vehicle State"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Determine the display order", default=10,
                              invisible=True)
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
