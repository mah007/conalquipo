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


class SaleQuoteLine(models.Model):
    _inherit = 'sale.quote.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(SaleQuoteLine, self)._onchange_product_id()
        components_ids = self.product_id.product_tmpl_id.components_ids
        if components_ids:
            for p in components_ids:
                values = {
                    'product_id': p.product_child_id.id,
                    'product_uom_qty': p.quantity,
                    'product_uom_id': p.product_child_id.product_tmpl_id.sale_uom.id,
                    'quote_id': 1,
                    'name': 'Prueba',
                    'price_unit': 200
                }

                self.create(values)
        _logger.warning(components_ids)
        return res