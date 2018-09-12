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
_logger = logging.getLogger(__name__)
from odoo import fields, models, api, _


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
                        'product_uom_id': \
                         p.product_child_id.product_tmpl_id.uom_id.id,
                        'name': 'Comp. ' + str(
                            data.product_id.product_tmpl_id.name),
                        'price_unit': 0,
                        'quote_id': res.id,
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
                        'product_uom_id': \
                         p.product_child_id.product_tmpl_id.uom_id.id,
                        'name': 'Comp. ' + str(
                            data.product_id.product_tmpl_id.name),
                        'price_unit': 0,
                        'quote_id': self.id,
                        'indicted': True
                    }
                    self.quote_line.create(values)
        return res


class SaleQuoteLine(models.Model):
    _inherit = "sale.quote.line"

    indicted = fields.Boolean(string='Indicted')
    product_id = fields.Many2one(
        'product.product',
        'Product', domain=[], required=True)
