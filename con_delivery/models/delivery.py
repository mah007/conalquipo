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


class DeliveryCarrierCost(models.Model):
    """
    This model create a table for managed the cost by each vehicle
    relational to the delivery carrier and make the followings links.

    Fields:
        vehicle (int): Many2one field linked to `flee.vehicle` model.
        delivery_carrier_id (int): Many2one field linked to
        `delivery.carrier` model.
    """
    _name = 'delivery.carrier.cost'

    vehicle = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Vehicle',
        ondelete='cascade',
        index=True, copy=False,
        track_visibility='onchange')
    cost = fields.Float(
        string='Cost',
        track_visibility='onchange')
    delivery_carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Delivery Carrier',
        ondelete='cascade',
        track_visibility='onchange')

    @api.model
    def create(self, values):
        record = super(DeliveryCarrierCost, self).create(values)
        if not record.vehicle:
            raise UserError(_("The vehicle is required on the line"))
        # if not record.cost:
        #     raise UserError(_("The cost is required on the line"))
        if record.cost < 0:
            raise UserError(_("The cost can't be negative"))
        return record

    @api.multi
    def write(self, values):
        record = super(DeliveryCarrierCost, self).write(values)
        if not self.vehicle:
            raise UserError(_("The vehicle is required on the line"))
        # if not self.cost:
        #     raise UserError(_("The cost is required on the line"))
        if self.cost < 0:
            raise UserError(_("The cost can't be negative"))
        return record


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    municipality_ids = fields.One2many(
        'res.country.municipality',
        'delivery_carrier_id',
        string='Municipality', copy=True,
        track_visibility='onchange')
    delivery_carrier_cost = fields.One2many(
        'delivery.carrier.cost',
        'delivery_carrier_id',
        string='Lines Delivery Carrier'
        'Cost', copy=True)
    product_id = fields.Many2one(
        'product.product',
        string='Delivery Product',
        required=True,
        ondelete='restrict',
        domain=[('product_tmpl_id.for_shipping', '=', True)])
    price_type = fields.Selection(
        [('fixed_price', 'Fixed price'),
         ('multiple_prices', 'Multiple prices')],
        string="Price Type", default="fixed_price")

    @api.onchange('free_over')
    def onchange_free_over(self):
        if not self.free_over:
            self.amount = 0.0

    @api.onchange('state_ids')
    def onchange_states(self):
        """
        Onchange function that update the country_ids and municipality_ids
        with the correct municipality and country based on the given
        State/Province.

        :return: None
        """
        self.country_ids = [
            (6,
             0,
             self.country_ids.ids + self.state_ids.mapped(
                 'country_id.id'))]
        self.municipality_ids = [
            (6,
             0,
             self.municipality_ids.ids + self.municipality_ids.mapped(
                 'state_id.id'))]

    @api.onchange('delivery_carrier_cost')
    def onchange_vehicle_list(self):
        vehicle_list = []
        if self.delivery_carrier_cost:
            for data in self.delivery_carrier_cost:
                vehicle_list.append(data.vehicle)
            count = Counter(vehicle_list)
            new_list = [[k, ]*v for k, v in count.items()]
            for nlist in new_list:
                if len(nlist) > 1:
                    raise UserError(_(
                        "The vehicle %s already asigned in delivery carrier"
                        ) % nlist[0].name)

    @api.model
    def create(self, values):
        vehicle_list = []
        record = super(DeliveryCarrier, self).create(values)
        if record.amount < 0:
            raise UserError(_("The amount limit can't be negative"))
        for data in record.delivery_carrier_cost:
            vehicle_list.append(data.vehicle)
        count = Counter(vehicle_list)
        new_list = [[k, ]*v for k, v in count.items()]
        for nlist in new_list:
            if len(nlist) > 1:
                raise UserError(_(
                    "The vehicle %s already asigned in delivery carrier"
                    ) % nlist[0].name)
        return record

    @api.multi
    def write(self, values):
        vehicle_list = []
        record = super(DeliveryCarrier, self).write(values)
        if self.amount < 0:
            raise UserError(_("The amount limit can't be negative"))
        for data in self.delivery_carrier_cost:
            vehicle_list.append(data.vehicle)
        count = Counter(vehicle_list)
        new_list = [[k, ]*v for k, v in count.items()]
        for nlist in new_list:
            if len(nlist) > 1:
                raise UserError(_(
                    "The vehicle %s already asigned in delivery carrier"
                    ) % nlist[0].name)
        return record


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
