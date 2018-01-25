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

from odoo import models, fields, api, _
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
        if self.carrier_type == 'company' and self.projects_id:
            delivery = self.env['delivery.carrier'].search(
                [('country_ids', '=',
                  self.projects_id.country_id.id),
                 ('state_ids', '=',
                  self.projects_id.state_id.id),
                 ('municipality_ids', '=',
                  self.projects_id.municipality_id.id)],
                limit=1
                )
            self.update({
                'carrier_id': delivery,
            })
        else:
            if self.partner_id:
                lines = list()
                saleOrderLine = self.env['sale.order.line']
                del_ids = saleOrderLine.search([
                         ('order_id', '=', self._origin.id),
                         ('is_delivery', '=', True)])._ids
                link_ids = saleOrderLine.search([
                         ('order_id', '=', self._origin.id),
                         ('is_delivery', '!=', True)])
                # ~ Data Backup
                for new in link_ids:
                    lines.append({
                                'order_id': self._origin.id,
                                'name': new.name,
                                'product_uom_qty': new.product_uom_qty,
                                'product_uom': new.product_uom.id,
                                'product_id': new.product_id.id,
                                'price_unit': new.price_unit,
                                'tax_id': new.tax_id,
                                'is_delivery': False
                    })
                # ~ Deleted the records
                self.update({
                    'order_line': [(2, del_ids)],
                })
                # ~ link new records
                for new in lines:
                    self.update({'order_line': [(0, 0, new)]})
                self.write({'carrier_id': None})

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        super(SaleOrder, self).onchange_carrier_id()
        domain = {}
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)])
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            domain = {'vehicle': [('id', 'in', veh_ids)]}
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
                        [('vehicle', '=', order.vehicle.id),
                         ('delivery_carrier_id', '=', order.carrier_id.id)])
                    order.delivery_price = veh_carrier.cost
        else:
            super(SaleOrder, self)._compute_delivery_price()

    @api.multi
    def set_delivery_line(self):
        if self.vehicle:
            # self._remove_delivery_line()
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('vehicle', '=', self.vehicle.id),
                 ('delivery_carrier_id', '=', self.carrier_id.id)])
            self._create_delivery_line(self.carrier_id, veh_carrier.cost,
                                       receipt=True)
            self.delivery_price = veh_carrier.cost
        else:
            super(SaleOrder, self).set_delivery_line()

    def _create_delivery_line(self, carrier, price_unit, receipt=False):
        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, carrier.product_id, self.partner_id).ids
        # Create the sales order line
        for x in range(2):
            values = {
                'order_id': self.id or self._origin.id,
                'name': '{} - {}'.format(carrier.name,
                                         'Entrega' if x == 0 else
                'Recogida'),
                'product_uom_qty': 1,
                'product_uom': carrier.product_id.uom_id.id,
                'product_id': carrier.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            self.update({'order_line': [(0, 0, values)]})
            if not receipt: break
        return True
