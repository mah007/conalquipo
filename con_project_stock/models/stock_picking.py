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

    project_id = fields.Many2one('project.project', string="Project")
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(string="Shipping",
                                   compute="_get_merge_address")
    invoice_address = fields.Text(string="Billing",
                                  compute="_get_merge_address")

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        super(StockPicking, self).onchange_picking_type()
        if self.partner_id:
            self.project_id = False

    @api.depends('project_id')
    def _get_merge_address(self):
        """
        This function verify if a project has been selected and return a
        merge address for shipping and invoice to the user.

        :return: None
        """
        for spk in self:
            if spk.project_id:
                p = spk.project_id
                spk.shipping_address = spk.merge_address(
                    p.street1 or '', p.street1_2 or '', p.city or '',
                    p.municipality_id.name or '', p.state_id.name or '',
                    p.zip or '', p.country_id.name or '', p.phone1 or '',
                    p.email or '')
                spk.invoice_address = spk.merge_address(
                    p.street2_1 or '', p.street2_2 or '', p.city2 or '',
                    p.municipality2_id.name or '', p.state2_id.name or '',
                    p.zip2 or '', p.country2_id.name or '', p.phone2 or '',
                    p.email or '')

    @staticmethod
    def merge_address(street, street2, city, municipality, state, zip_code,
                      country, phone, email):
        """
        This function receive text fields for merge the address fields.

        :param street: The text field for the address to merge.
        :param street2: The text field for the second line of
         the address to merge.
        :param city: The text field for the city of the address to merge.
        :param municipality: the text for the municipality to merge.
        :param state: The text for the state to merge.
        :param zip_code: the text for the zip code of the address.
        :param country: the text for the name of the country.
        :param phone: the phone in text.
        :param email: the email on string.

        :return: merge string with
        street+street2+city+municipality+state+zip+country
        """
        values = [street, ', ', street2, ', ', city, ', ', municipality, ', ',
                  state, ',', zip_code, ', ', country, ', ', phone, ', ',
                  email]
        out_str = ''
        for num in range(len(values)):
            out_str += values[num]
        return out_str


class SaleOrder(Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._propagate_picking_project()
        return res

    @api.multi
    def _propagate_picking_project(self):
        """
        This function write the `project_id` of the `sale_order` on the Stock
        Picking Order.

        :return: True
        """
        for picking in self.picking_ids:
            picking.write({'project_id': self.project_id.id})
        return True
