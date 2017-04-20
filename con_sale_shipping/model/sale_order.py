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

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carrier_type = fields.Selection(
        [('client', 'Client'), ('company', 'Company')],
        string='Carrier Responsible', default='fixed')

    project_id = fields.Many2one('project.project', string="Project")
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(string="Shipping", compute="")
    invoice_address = fields.Text(string="Billing", compute="")

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        super(SaleOrder, self).onchange_picking_type()
        if self.partner_id:
            self.project_id = False

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            p = self.project_id
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
