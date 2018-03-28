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
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._get_components()
        return res


    @api.multi
    def _get_components(self):
        for pk in self.picking_ids:
            for ml in pk.move_lines:
                if ml.product_id.components_ids:
                        ml.get_components_button()
        return True


class SaleOrderLine(Model):
    _inherit = "sale.order.line"

    @api.onchange('bill_uom_qty')
    def min_bill_qty(self):
        product_qty_temp = self.product_id.product_tmpl_id.min_qty_rental
        product_bill_qty = self.bill_uom_qty
        if product_qty_temp > 0 and product_bill_qty < product_qty_temp:
            raise UserError(_("The min qty for rental this product is:"
                              " %s") % product_qty_temp)            
