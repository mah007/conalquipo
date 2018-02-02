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

from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class VehicleType(models.Model):
    """
    This model create a database table for manage the vehicles types for
    example:
        * Motorcicle
        * Car
        * Bus
    """
    _name = 'fleet.vehicle.type'
    _description = "Vehicle Type"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Determine the display order", default=10,
                              invisible=True)
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    holder = fields.Many2one('res.partner', 'Holder',
                             track_visibility='onchange')
    mark = fields.Char(string="Mark", track_visibility='onchange')
    reference = fields.Char(string="Reference", track_visibility='onchange')
    type = fields.Many2one('fleet.vehicle.type', string='Type',
                           track_visibility='onchange')
    model = fields.Integer(string="Model", track_visibility='onchange')
    num_motor = fields.Char(string="Number Motor", track_visibility='onchange')
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
