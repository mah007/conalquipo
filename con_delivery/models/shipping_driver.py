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
from collections import Counter

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ShippingDriver(models.Model):
    """
    Model that link the driver's information from Employees nad set the job
    title on the shipping this model create the following fields on Odoo
    database:
        driver_ids: int
            A link over `hr.employee` model with track visibility.
        job_title: str (Selection Field)
            Contain the selection job title of the shipping for each
            assigned employee.
        stock_picking_id: int
            A link over `stock.picking` model with track visibility.

    If you need add a new value on type_hr please use the option
    selection_add available for the field in the Odoo ORM.
    """
    _name = 'shipping.driver'
    _description = 'Shipping driver'

    driver_ids = fields.Many2one(
        'hr.employee',
        string='Employee',
        ondelete='cascade', index=True,
        copy=False, track_visibility='onchange')
    job_title = fields.Selection(
        [('driver', 'Driver'),
         ('assistant', 'Assistant')],
        string='HR Type', default='driver')
    stock_picking_id = fields.Many2one(
        'stock.picking', string='Stock Picking',
        ondelete='cascade',
        index=True, copy=False,
        track_visibility='onchange')
    identification_id = fields.Char(
        string='Identification No',
        related="driver_ids.identification_id",
        store=True)

    @api.onchange('job_title')
    def onchange_job_title(self):
        if self.job_title == 'driver' and self.driver_ids:
            if self.driver_ids.contract_id.is_driver:
                lc_driver = self.driver_ids.contract_id.license_category
                lc_vehicle = self.stock_picking_id.vehicle_id.license_category
                if lc_driver.id != lc_vehicle.id:
                    raise UserError(_(
                        "The category of the driver's license of this "
                        "employee does not coincide with the category "
                        "required by the vehicle assiging this order"))
            else:
                raise UserError(_("This employee does not possess "
                                  "driving skills"))
