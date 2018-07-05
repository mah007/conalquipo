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
from odoo import models, _
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def action_validate(self):
        res = super(StockScrap, self).action_validate()

        if isinstance(res, dict):
            warn = res.get('res_model', '')
            if warn == 'stock.warn.insufficient.qty.scrap':
                return res

        # if any([not res, not self.picking_id.sale_id,
        #         not self.product_id.replenishment_charge,
        #         not self.scrap_location_id.is_charge_replacement]):
        #     return res

        reple_id = self.product_id.replenishment_charge
        if reple_id:
            self.picking_id.sale_id.order_line.create({
                'order_id': self.picking_id.sale_id.id,
                'product_id': reple_id.id,
                'product_uom_qty': self.scrap_qty,
                'price_unit': reple_id.lst_price,
                'name': _('Replenishment %s') % (reple_id.name),
                'product_uom': reple_id.uom_id.id,
            })
            return res
        else:
            raise UserError(_(
                "The product doesn't have replacement service!"))            
            

class StockWarnInsufficientQtyScrap(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.scrap'

    def action_done(self):
        res = super(StockWarnInsufficientQtyScrap, self).action_done()
        scrap_id = self.scrap_id

        # if any([not res, not scrap_id.picking_id.sale_id,
        #         not scrap_id.product_id.replenishment_charge,
        #         not scrap_id.scrap_location_id.is_charge_replacement]):
        #     return res

        reple_id = scrap_id.product_id.replenishment_charge
        if reple_id:
            scrap_id.picking_id.sale_id.order_line.create({
                'order_id': scrap_id.picking_id.sale_id.id,
                'product_id': reple_id.id,
                'product_uom_qty': scrap_id.scrap_qty,
                'price_unit': reple_id.lst_price,
                'name': _('Replenishment %s') % (reple_id.name),
                'product_uom': reple_id.uom_id.id,
            })
            return res
        else:
            raise UserError(_(
                "The product doesn't have replacement service!"))            