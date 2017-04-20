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

from odoo.addons.stock.tests.common import TestStockCommon
from odoo.tools import mute_logger


class TestStockFlow(TestStockCommon):

    @mute_logger('odoo.addons.base.ir.ir_model', 'odoo.models')
    def test_00_picking_create_and_transfer_quantity(self):
        """ Basic stock operation on outgoing shipment."""
        # ======================================================================
        # Create Outgoing shipment with ...
        #   product A ( 10 Unit ) , product B ( 5 Unit )
        #   product C (  3 unit ) , product D ( 10 Unit )
        # ======================================================================

        project_agrolite_id = self.env['project.project'].create({
            'partner_id': self.partner_agrolite_id,
            'name': 'Test Project',
        })

        picking_out = self.PickingObj.create({
            'partner_id': self.partner_agrolite_id,
            'project_id': project_agrolite_id,
        })

        self.MoveObj.create({
            'name': self.productA.name,
            'product_id': self.productA.id,
            'product_uom_qty': 10,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location,
            'location_dest_id': self.customer_location})
        # Confirm outgoing shipment.
        picking_out.action_confirm()
        for move in picking_out.move_lines:
            self.assertEqual(move.state, 'confirmed', 'Wrong state of move line.')
        # Product assign to outgoing shipments
        picking_out.action_assign()
        self.assertEqual(picking_out.move_lines[0].state, 'confirmed', 'Wrong state of move line.')
        self.assertEqual(picking_out.move_lines[1].state, 'assigned', 'Wrong state of move line.')
        self.assertEqual(picking_out.move_lines[2].state, 'assigned', 'Wrong state of move line.')
        self.assertEqual(picking_out.move_lines[3].state, 'confirmed', 'Wrong state of move line.')
        # Check availability for product A
        aval_a_qty = self.MoveObj.search([('product_id', '=', self.productA.id),
                                          ('picking_id', '=', picking_out.id)], limit=1).reserved_availability
        self.assertEqual(aval_a_qty, 4.0,
                         'Wrong move quantity availability of product A (%s found instead of 4)' % aval_a_qty)
        # Transfer picking.
        picking_out.do_transfer()
