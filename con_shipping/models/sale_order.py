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
        """
        On changed method that allow adds automatically the cost product
        shipping to the order lines, and deleted the product when the shipping
        option is `Client`
        :return: None
        """
        if self.carrier_type == 'company' and self.project_id:
            delivery = self.env['delivery.carrier'].search(
                [('country_ids', '=',
                  self.project_id.country_id.id),
                 ('state_ids', '=',
                  self.project_id.state_id.id),
                 ('municipality_ids', '=',
                  self.project_id.municipality_id.id)],
                limit=1
                )
            self.update({
                'carrier_id': delivery,
            })
        else:
            if self.partner_id:
                lines = list()
                order_line = self.env['sale.order.line']
                del_ids = order_line.search(
                    [('order_id', '=', self._origin.id),
                     ('is_delivery', '=', True)])._ids
                link_ids = order_line.search(
                    [('order_id', '=', self._origin.id),
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
        """
        Overloaded function that checks the if a carrier is seated and
        search all the vehicle linked to it and create a domain en polish
        notation.

        :return:
            Dict(str, Dict(str, list(tuple))): A Dictionary of dictionaries
            with domain values in polish notation list(tuple).
        """
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
        """
        Overloaded function that verify the order state for update the field
        delivery_price with the values of the carrier selected.

        :return: None
        """
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
        """
        Overloaded function that check is a vehicle is selected and create
        the delivery line on orders lines and set the delivery price on the
        order if not have a vehicle the function run a super over the function.

        :return: None
        """
        for rec in self:
            if rec.vehicle:
                veh_carrier = self.env['delivery.carrier.cost'].search(
                    [('vehicle', '=', rec.vehicle.id),
                     ('delivery_carrier_id', '=', rec.carrier_id.id)])
                rec._create_delivery_line(
                    rec.carrier_id, veh_carrier.cost, False, True)
                rec.delivery_price = veh_carrier.cost
            else:
                super(SaleOrder, self).set_delivery_line()

    def _create_delivery_line(self, carrier, price_unit, picking_ids=False,
                              receipt=False):
        """
        Overwrote function that create the line of the delivery on the sale
        order lines, this function have been modified for add the delivery
        output line and delivery input line by cargo cost.

        :param carrier: carrier's recordset.
        :param price_unit: price of the cargo.
        :param receipt: Flag parameter that receipt a boolean value False
         for only the output cargo and True for the output/input cargo.

        :return: boolean value.
        """
        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, carrier.product_id, self.partner_id).ids
        _logger.warning(price_unit)
        _logger.warning('AQUIIIIIII')
        # Create the sales order line
        for x in range(2):
            values = {
                'order_id': self.id or self._origin.id,
                'name': '{} - {}'.format(
                    carrier.name, _('Delivery') if x == 0 else
                    _('Receive')),
                'product_uom_qty': 1,
                'product_uom': carrier.product_id.uom_id.id,
                'product_id': carrier.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
                'delivery_direction': 'out' if x == 0 else 'in',
                'picking_ids': picking_ids,
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            self.update({'order_line': [(0, 0, values)]})
            if not receipt:
                break
        return True

    @api.multi
    def action_confirm(self):

        res = super(SaleOrder, self).action_confirm()

        # stock_location_partner = self.env['stock.location'].search([(
        #     'project_id', '=', self.project_id.id)])

        # ~ dl_ids: Deliveries Lines Ids
        dl_ids = self.env['sale.order.line'].search(
            [('delivery_direction', 'in', ['out']),
             ('picking_ids', '=', False),
             ('order_id', '=', self.id)])

        customer_location = self.env.ref('stock.stock_location_customers')

        for picking in self.picking_ids:
            if picking.state not in ['done', 'cancel'] and \
                    picking.location_dest_id.id == customer_location.id:
                dl_ids.update({'picking_ids': [(4, picking.id)]})
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_direction = fields.Selection([('in', 'collection'),
                                           ('out', 'delivery')],
                                          string="Delivery Type")
    picking_ids = fields.Many2many('stock.picking', 'order_line_picking_rel',
                                  'picking_id', 'sale_order_line_id',
                                   string="Pickings",
                                   help="Linked picking to the delivery cost")
