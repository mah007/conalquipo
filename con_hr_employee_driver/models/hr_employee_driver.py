# -*- coding: utf-8 -*-

from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    is_driver = fields.Boolean('Is Driver')
    license_category = fields.Many2one('license.category',
                                       string='license category')
    license_number = fields.Char('license number')


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
