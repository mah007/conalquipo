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


class SaleOrder(Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._add_product_with_components()
        return res

    @api.multi
    def _add_product_with_components(self):
        for so in self:
            for ln in so.order_line:
                if ln.product_id.components:
                    for pk in so.picking_ids:
                        for mv in pk.move_lines:
                            mv.copy({
                                'product_id': ln.product_id.id,
                                'product_uom_qty': ln.product_uom_qty,
                                'picking_id': pk.id,
                                'not_explode': True,
                            })
                            break
        return True
