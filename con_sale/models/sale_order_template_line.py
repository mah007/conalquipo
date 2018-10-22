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

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    indicted = fields.Boolean(string='Indicted')
    product_id = fields.Many2one(
        'product.product',
        'Product', domain=[], required=True)
    bill_uom = fields.Many2one(
        'uom.uom',
        string='Unidad de venta')
    bill_uom_qty = fields.Float(
        'Cant. Venta',
        digits=dp.get_precision('Product Unit'
                                ' of Measure'))
    min_sale_qty = fields.Float('MQty')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        uoms_list = []
        if self.product_id:
            name = self.product_id.name_get()[0][1]
            if self.product_id.description_sale:
                name += '\n' + self.product_id.description_sale
            self.name = name
            self.layout_category_id = \
                self.product_id.product_tmpl_id.layout_sec_id.id
            self.price_unit = self.product_id.lst_price
            self.product_uom_id = self.product_id.uom_id.id
            self.website_description = \
                self.product_id.quote_description or \
                self.product_id.website_description or ''
            # Get uoms
            uoms_ids = self.product_id.product_tmpl_id.uoms_ids
            if uoms_ids:
                self.product_uoms = True
                for p in uoms_ids:
                    uoms_list.append(p.uom_id.id)
            else:
                self.bill_uom = self.product_id.product_tmpl_id.sale_uom.id
                self.bill_uom_qty = self.product_uom_qty
                uoms_list.append(self.product_id.product_tmpl_id.sale_uom.id)
            domain = {
                'product_uom_id': [
                    ('category_id',
                     '=',
                     self.product_id.uom_id.category_id.id)],
                'bill_uom': [('id', 'in', uoms_list)]}
            return {'domain': domain}

    @api.onchange('bill_uom')
    def _onchange_product_uom(self):
        """
        Get price for specific uom of product
        """
        product_muoms = self.product_id.product_tmpl_id.multiples_uom
        if not product_muoms:
            self.price_unit = self.product_id.product_tmpl_id.list_price
            self.min_sale_qty = \
                self.product_id.product_tmpl_id.min_qty_rental
        else:
            for uom_list in self.product_id.product_tmpl_id.uoms_ids:
                if self.bill_uom.id == uom_list.uom_id.id:
                    self.price_unit = uom_list.cost_byUom
                    self.min_sale_qty = uom_list.quantity