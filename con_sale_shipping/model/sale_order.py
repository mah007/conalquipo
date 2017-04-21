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

from odoo.models import Model, api, _
from odoo import fields


class SaleOrder(Model):
    _inherit = 'sale.order'

    carrier_type = fields.Selection(
        [('client', 'Client'), ('company', 'Company')],
        string='Carrier Responsible', default='client')

    projects_id = fields.Many2one('project.project', string="Project")
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(string="Shipping")
    invoice_address = fields.Text(string="Billing")

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.projects_id = False

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.projects_id:
            p = self.projects_id
            self.shipping_address = self.merge_address(
                p.street1 or '', p.street1_2 or '', p.city or '',
                p.municipality_id.name or '', p.state_id.name or '',
                p.zip or '', p.country_id.name or '')
            self.invoice_address = self.merge_address(
                p.street2_1 or '', p.street2_2 or '', p.city2 or '',
                p.municipality2_id.name or '', p.state2_id.name or '',
                p.zip2 or '', p.country2_id.name or '')

    @api.onchange('carrier_type')
    def onchange_carrier_type(self):
        if self.carrier_type != 'company':
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
                                'is_delivery': False
                        })]
                    })
                self.write({'carrier_id': None})

    @staticmethod
    def merge_address(street, street2, city, municipality,
                      state, zip, country):
        """
        This function receive text fields for merge the address fields.
        :param street: The text field for the address to merge.
        :param street2: The text field for the second line of
         the address to merge.
        :param city: The text field for the city of the address to merge.
        :param municipality: the text for the municipality to merge.
        :param state: The text for the state to merge.
        :param zip: the text for the zip code of the address. 
        :param country: the text for the name of the country.
        :return: merge string with 
        street+street2+city+municipality+state+zip+country
        """
        new_string = street+', '+street2+', '+city+', '+municipality+', '
        new_string += state+','+zip+', '+country
        return new_string
