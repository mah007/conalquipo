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

    type_sp = fields.Integer(related='picking_type_id.id')

    carrier_type = fields.Selection(related='sale_id.carrier_type')

    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle',
                                 string='Vehicle',
                                 related='sale_id.vehicle',
                                 onchange='onchange_vehicle_id',
                                 track_visibility='onchange')

    vehicle_client = fields.Char(string='Vehicle',
                                 track_visibility='onchange')

    driver_client = fields.Char(string='Driver',
                                track_visibility='onchange')

    driver_ids = fields.One2many('shipping.driver', 'stock_picking_id',
                                 string='Shipping Driver', copy=True)
    vehicle_client = fields.Char(string='Vehicle',
                                 track_visibility='onchange')

    Hr_entry = fields.Float(string='Hour Entry', track_visibility='onchange')

    Hr_output = fields.Float(string='Hour Output', track_visibility='onchange')

    receipts_driver_ids = fields.One2many('shipping.driver',
                                          'stock_picking_id',
                                          string='Shipping Driver', copy=True)

    person_receives = fields.Char(string='Person receives',
                                  track_visibility='onchange')
    person_identification_id = fields.Char(string='Person identification',
                                           track_visibility='onchange')
    post = fields.Char(string='post', track_visibility='onchange')

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
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
        domain = {}
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)], limit=10)
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)

            vehicle = self.env['fleet.vehicle'].search([('id', 'in',
                                                         veh_ids)], limit=10)

            domain = {'vehicle_id': [('id', 'in', vehicle.ids)]}

        return {'domain': domain}


class ShippingDriver(models.Model):
    _name = 'shipping.driver'

    driver_ids = fields.Many2one(comodel_name='hr.employee',
                                 string='Driver', ondelete='cascade',
                                 index=True, copy=False,
                                 track_visibility='onchange')

    type_hr = fields.Selection([('driver', 'Driver'),
                                ('assistant', 'Assistant')],
                               string='HR Type', default='driver')

    stock_picking_id = fields.Many2one('stock.picking',
                                       string='Stock Picking',
                                       ondelete='cascade', index=True,
                                       copy=False, track_visibility='onchange')
