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


class SaleQuoteTemplate(models.Model):
    _inherit = 'sale.quote.template'

    groups_ids = fields.Many2many(
        "res.groups", string='Notifications to groups')
    special_category = fields.Many2one(
        'product.category', 'Special category',
        domain=lambda self: self.getcategory())

    @api.model
    def getcategory(self):
        """
        Domain for templates categories
        """
        cat_list = []
        cats = self.env.user.company_id.special_quotations_categories
        for data in cats:
            cat_list.append(data.id)
        return [('id', 'in', cat_list)]

    @api.model
    def create(self, values):
        """
        Overwrite the method write from sale quote template
        """
        res = super(SaleQuoteTemplate, self).create(values)
        for data in res.quote_line:
            components_ids = data.product_id.product_tmpl_id.components_ids
            if components_ids and not data.indicted:
                data.write({'indicted': True})
                for p in components_ids:
                    values = {
                        'product_id': p.product_child_id.id,
                        'product_uom_qty': p.quantity,
                        'product_uom_id':
                        p.product_child_id.product_tmpl_id.uom_id.id,
                        'name': 'Comp. ' + str(
                            data.product_id.product_tmpl_id.name),
                        'price_unit': 0,
                        'quote_id': res.id,
                        'layout_category_id':
                        p.product_child_id.product_tmpl_id.layout_sec_id.id,
                        'indicted': True
                    }
                    res.quote_line.create(values)
        return res

    @api.multi
    def write(self, values):
        """
        Overwrite the method write from sale quote template
        """
        res = super(SaleQuoteTemplate, self).write(values)
        for data in self.quote_line:
            components_ids = data.product_id.product_tmpl_id.components_ids
            if components_ids and not data.indicted:
                data.write({'indicted': True})
                for p in components_ids:
                    values = {
                        'product_id': p.product_child_id.id,
                        'product_uom_qty': p.quantity,
                        'product_uom_id':
                        p.product_child_id.product_tmpl_id.uom_id.id,
                        'name': 'Comp. ' + str(
                            data.product_id.product_tmpl_id.name),
                        'price_unit': 0,
                        'quote_id': self.id,
                        'layout_category_id':
                        p.product_child_id.product_tmpl_id.layout_sec_id.id,
                        'indicted': True,
                    }
                    self.quote_line.create(values)
        return res


class SaleQuoteLine(models.Model):
    _inherit = "sale.quote.line"

    indicted = fields.Boolean(string='Indicted')
    product_id = fields.Many2one(
        'product.product',
        'Product', domain=[], required=True)
    bill_uom = fields.Many2one(
        'product.uom',
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