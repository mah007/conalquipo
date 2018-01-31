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

    vehicle = fields.Many2one(comodel_name='fleet.vehicle', string='Vehicle',
                              ondelete='cascade', index=True, copy=False,
                              track_visibility='onchange')
    cost = fields.Float(string='Cost', track_visibility='onchange')
    delivery_carrier_id = fields.Many2one('delivery.carrier',
                                          string='Delivery Carrier',
                                          ondelete='cascade', index=True,
                                          copy=False,
                                          track_visibility='onchange')


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'


    delivery_carrier_cost = fields.One2many('delivery.carrier.cost',
                                            'delivery_carrier_id',
                                            string='Lines Delivery Carrier'
                                                   'Cost', copy=True)
