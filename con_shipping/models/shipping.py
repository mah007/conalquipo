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

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class Municipality(models.Model):
    _inherit = 'res.country.municipality'

    delivery_carrier_id = fields.Many2one('delivery.carrier',
                                          string='Delivery Carrier',
                                          ondelete='cascade', index=True,
                                          copy=False,
                                          track_visibility='onchange')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carrier_type = fields.Selection(
        [('client', 'Client'), ('company', 'Company')],
        string='Carrier Responsible', default='client')

    vehicle = fields.Many2one(comodel_name='fleet.vehicle',
                              string='Vehicle', ondelete='cascade',
                              index=True, copy=False,
                              track_visibility='onchange')

    @api.onchange('carrier_type')
    def onchange_carrier_type(self):
        if self.carrier_type == 'company':
            if self.partner_id:
                if self.partner_shipping_id:

                    delivery = self.env['delivery.carrier'].search(
                        [('country_ids', '=',
                          self.partner_shipping_id.country_id.id),
                         ('state_ids', '=',
                          self.partner_shipping_id.state_id.id),
                         ('municipality_ids', '=',
                          self.partner_shipping_id.municipality_id.id)],
                        limit=1
                        )
                    self.update({
                        'carrier_id': delivery,
                    })
        else:
            if self.partner_id:

                self.update({
                    'order_line': [(5, _, _)],
                })
                new_lines = self.env['sale.order.line'].search([
                    ('order_id', '=', self._origin.id),
                    ('is_delivery', '!=', True)])

                for new in new_lines:
                    self.update({'order_line': [
                        (0, 0, {
                                'order_id': self._origin.id,
                                'name': new.name,
                                'product_uom_qty': new.product_uom_qty,
                                'product_uom': new.product_uom.id,
                                'product_id': new.product_id.id,
                                'price_unit': new.price_unit,
                                'tax_id': new.tax_id,
                                'is_delivery': False})]
                    })
                self.write({'carrier_id': None})

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

            domain = {'vehicle': [('id', 'in', vehicle.ids)]}

        return {'domain': domain}

    @api.depends('carrier_id', 'order_line')
    def _compute_delivery_price(self):

        if self.vehicle:

            for order in self:
                if order.state != 'draft':
                    continue
                elif order.carrier_id.delivery_type != 'grid' and \
                        not order.order_line:
                    continue
                else:
                    veh_carrier = self.env['delivery.carrier.cost'].search(
                        [('vehicle', '=', order.vehicle.id)], limit=1)

                    order.delivery_price = veh_carrier.cost
        else:
            super(SaleOrder, self)._compute_delivery_price()

    @api.multi
    def delivery_set(self):

        if self.vehicle:
            self._delivery_unset()
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('vehicle', '=', self.vehicle.id)], limit=1)

            self._create_delivery_line(self.carrier_id, veh_carrier.cost)

        else:
            super(SaleOrder, self).delivery_set()
