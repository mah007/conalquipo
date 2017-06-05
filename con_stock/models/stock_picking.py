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

from odoo.models import Model, api
from odoo import fields
import logging

_logger = logging.getLogger(__name__)


class StockPicking(Model):
    _inherit = "stock.picking"

    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         readonly=True,
                                         required=True,
                                         states={
                                             'draft': [('readonly', False)],
                                             'partially_available':
                                                 [('readonly', False)],
                                             'done': [('readonly', False)],
                                             'waiting': [('readonly', False)],
                                             'assigned': [('readonly', False)]
                                         },
                                         help="Invoice address for "
                                              "current sales order.")
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Delivery Address',
                                          readonly=True,
                                          required=True,
                                          states={
                                              'draft': [('readonly', False)],
                                              'partially_available':
                                                  [('readonly', False)],
                                              'done': [('readonly', False)],
                                              'waiting': [('readonly', False)],
                                              'assigned': [('readonly', False)]
                                          },
                                          help="Delivery address for"
                                               " current sales order.")

    receives_maintenance = fields.Many2one(comodel_name='hr.employee',
                                           string='Receives in maintenance',
                                           track_visibility='onchange')

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        super(StockPicking, self).onchange_picking_type()
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        self.update(values)


class PackOperation(Model):
    _inherit = "stock.pack.operation"

    type_sp = fields.Integer(related='picking_id.picking_type_id.id')
    is_mechanic = fields.Boolean(
        related='product_id.product_tmpl_id.is_mechanic', string='Is Mechanic')

    mechanic_rem = fields.Many2one(comodel_name='hr.employee',
                                   string='Mechanic (Rem)')
    mechanic_dev = fields.Many2one(comodel_name='hr.employee',
                                   string='Mechanic (Dev)')
    observation = fields.Char(string="Observation")
