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

    sequence = fields.Integer(
        help="Determine the display order", default=10,
        invisible=True)
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
