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

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order', ondelete='cascade')
    order_type = fields.Selection(
        [('rent', 'Rent'), ('purchase', 'Purchase')],
        string="Type", default="purchase")

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self._add_product_with_components()
        return res

    @api.multi
    def _add_product_with_components(self):
        for po in self:
            for ln in po.order_line:
                if ln.product_id.components:
                    for pk in po.picking_ids:
                        for mv in pk.move_lines:
                            mv.copy({
                                'product_id': ln.product_id.id,
                                'product_uom_qty': ln.product_qty,
                                'picking_id': pk.id,
                                'not_explode': True,
                            })
                            break
        return True
