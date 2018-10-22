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
    _description = 'Delivery carrier cost'

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
