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
from odoo.models import Model
from odoo import fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(Model):
    _inherit = "product.pricelist.item"

    compute_price = fields.Selection(
        selection_add=[
            ('on_total',
             'Apply on total')])
    percent_price_total = fields.Float(
        'Total percentage Price')

    @api.one
    @api.depends(
        'categ_id',
        'product_tmpl_id',
        'product_id', 'compute_price', 'fixed_price',
        'pricelist_id', 'percent_price', 'price_discount',
        'price_surcharge')
    def _get_pricelist_item_name_price(self):
        if self.categ_id:
            self.name = _("Category: %s") % (self.categ_id.name)
        elif self.product_tmpl_id:
            self.name = self.product_tmpl_id.name
        elif self.product_id:
            self.name = self.product_id.display_name.replace(
                '[%s]' % self.product_id.code, '')
        else:
            self.name = _("All Products")

        if self.compute_price == 'fixed':
            self.price = ("%s %s") % (
                self.fixed_price,
                self.pricelist_id.currency_id.name)
        elif self.compute_price == 'percentage':
            self.price = _("%s %% discount") % (self.percent_price)
        elif self.compute_price == 'on_total':
            self.price = _("%s %% discount on total") % (
                self.percent_price_total)
        else:
            self.price = _(
                "%s %% discount and %s surcharge") % (
                    self.price_discount, self.price_surcharge)
