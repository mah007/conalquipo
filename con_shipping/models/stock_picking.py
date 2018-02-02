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

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    type_sp = fields.Integer(related='picking_type_id.id', store=True)
    carrier_type = fields.Selection(related='sale_id.carrier_type', store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                 related='sale_id.vehicle',
                                 onchange='onchange_vehicle_id',
                                 track_visibility='onchange', store=True)
    driver_client = fields.Char(string='Driver', track_visibility='onchange')
    driver_ids = fields.One2many(
        'shipping.driver', 'stock_picking_id', string='Shipping Driver',
        copy=True)
    vehicle_client = fields.Char(string='Vehicle', track_visibility='onchange')
    in_hour = fields.Float(string='Hour Entry', track_visibility='onchange')
    out_hour = fields.Float(string='Hour Output', track_visibility='onchange')
    receipts_driver_ids = fields.One2many(
        'shipping.driver', 'stock_picking_id', string='Shipping Driver',
        copy=True)
    responsible = fields.Char(string='Responsible',
                              track_visibility='onchange')
    id_number = fields.Char(string='Person identification',
                            track_visibility='onchange')
    job_title = fields.Char(string='Job title', track_visibility='onchange')
    carrier_tracking_ref = fields.Char(string='Tracking Reference',
                                       compute='_carrier_tracking_ref')

    @api.onchange('carrier_type')
    def onchange_carrier_type(self):
        """
        Wipe the values in the following fields:
        carrier_id and vehicle_id are False if carrier_type is 'client'
        vehicle_client and driver client are '' if carrier type is different
        to client.
        :return: None
        """
        if self.carrier_type == 'client':
            self.carrier_id = False
            self.vehicle_id = False
        else:
            self.vehicle_client = ''
            self.driver_client = ''

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """
        Check the vehicles available for the carrier selected and return
        a exception if the same is not available in that zone
        :return: a empty dictionary if process is ok and warning if have a
        exception
        """
        res = {}
        if not self.vehicle_id or not self.carrier_id:
            return res
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)], limit=10)
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            if self.vehicle_id.id not in veh_ids:
                self.vehicle_id = self.vehicle_id.id
                res['warning'] = {'title': _('Warning'), 'message': _(
                    'Selected vehicle is not available for the shipping '
                    'area. please select another vehicle.')}
                self.vehicle_id = self.vehicle_id.id
            else:
                return res
        return res

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        """
        Search all vehicle available for a carrier and send the dynamic
        domain to the field vehicle_id.
        :return: A dictionary with a domain in polish notation
        """
        domain = {}
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)], limit=10)
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            vehicle = self.env['fleet.vehicle'].search(
                [('id', 'in', veh_ids)], limit=10)
            domain = {'vehicle_id': [('id', 'in', vehicle.ids)]}
        return {'domain': domain}

    @api.one
    @api.depends('scheduled_date', 'carrier_id', 'vehicle_id',
                 'vehicle_client')
    def _carrier_tracking_ref(self):
        """
        This function merge the following fields in a simple string,
        for create a tracking code:
            scheduled_date : date
            carrier_id: int
            vehicle_id.license_plate: int
            location_id.location_id.name: str
        :return: a joined string tracker code
        """
        if self.carrier_id:
            ref = [str(self.scheduled_date), str(self.carrier_id.id),
                   str(self.vehicle_id.license_plate or ''),
                   str(self.location_id.location_id.name or '')]
        else:
            ref = [str(self.scheduled_date), str(self.vehicle_client or ''),
                   self.location_id.location_id.name or '']
        self.carrier_tracking_ref = str("".join(ref)).replace("-", "").\
            replace(" ", "").replace(":", "")


class ShippingDriver(models.Model):
    """
    Model that link the driver's information from Employees nad set the job
    title on the shipping this model create the following fields on Odoo
    database:
        driver_ids: int
            A link over `hr.employee` model with track visibility.
        type_hr: str (Selection Field)
            Contain the selection job title of the shipping for each
            assigned employee.
        stock_picking_id: int
            A link over `stock.picking` model with track visibility.

    If you need add a new value on type_hr please use the option
    selection_add available for the field in the Odoo ORM.
    """
    _name = 'shipping.driver'

    driver_ids = fields.Many2one(
        'hr.employee', string='Employee', ondelete='cascade', index=True,
        copy=False, track_visibility='onchange')
    job_title = fields.Selection([('driver', 'Driver'),
                                  ('assistant', 'Assistant')],
                                 string='HR Type', default='driver')
    stock_picking_id = fields.Many2one(
        'stock.picking', string='Stock Picking', ondelete='cascade',
        index=True, copy=False, track_visibility='onchange')
