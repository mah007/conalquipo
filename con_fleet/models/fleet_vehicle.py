# -*- coding: utf-8 -*-

from odoo import fields, models


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


class LicenseCategory(models.Model):
    """
    This model create a database table for manage the license category for
    example:
        * A1
        * A2
        * B1
    """
    _name = 'license.category'
    _description = "license category"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Determine the display order", default=10,
                              invisible=True)
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    license_category = fields.Many2one('license.category',
                                       string='license category')
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