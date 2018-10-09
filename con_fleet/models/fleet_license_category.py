# -*- coding: utf-8 -*-

from odoo import fields, models


class LicenseCategory(models.Model):
    """
    This model create a database table for manage the license category for
    example:
        * A1
        * A2
        * B1
    """
    _name = 'fleet.license.category'
    _description = "License category"
    _order = 'sequence, id'

    sequence = fields.Integer(
        help="Determine the display order", default=10,
        invisible=True)
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
