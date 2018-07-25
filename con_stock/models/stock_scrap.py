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
from odoo import models, _, api
from odoo.tools import float_compare
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def action_validate(self):
        res = super(StockScrap, self).action_validate()
        qtys = []
        precision = self.env[
            'decimal.precision'].precision_get(
                'Product Unit of Measure')
        available_qty = self.env[
            'stock.move'].search(
                [('product_id', '=', self.product_id.id),
                 ('location_id', '=', self.location_id.id),
                 ('picking_id', '=', self.picking_id.id)
                ])
        for products_qty in available_qty:
            qtys.append(products_qty.product_qty)
        if float_compare(sum(qtys), \
         self.scrap_qty, precision_digits=precision) >= 0:
            return self.do_scrap()
        else:
            return {
                'name': _('Insufficient Quantity'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.warn.insufficient.qty.scrap',
                'view_id': self.env.ref(
                    'stock.stock_warn_insufficient_qty_scrap_form_view').id,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_location_id': self.location_id.id,
                    'default_scrap_id': self.id
                },
                'target': 'new'
            }

        if isinstance(res, dict):
            warn = res.get('res_model', '')
            if warn == 'stock.warn.insufficient.qty.scrap':
                return res

        if any([not res, not self.picking_id.sale_id,
                not self.product_id.replenishment_charge,
                not self.scrap_location_id.is_charge_replacement]):
            return res

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

    @api.multi
    def do_scrap(self):
        res = super(StockScrap, self).do_scrap()
        for scrap in self:
            reple_id = scrap.product_id.replenishment_charge
            if not reple_id:
                raise UserError(_(
                    "The product doesn't have replacement service!"))
        return res


class StockWarnInsufficientQtyScrap(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.scrap'

    def action_done(self):
        res = super(StockWarnInsufficientQtyScrap, self).action_done()
        scrap_id = self.scrap_id

        if any([not res, not scrap_id.picking_id.sale_id,
                not scrap_id.product_id.replenishment_charge,
                not scrap_id.scrap_location_id.is_charge_replacement]):
            return res

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
            scrap_id.move_id.write({'description': _(
                'Replenishment %s') % (reple_id.name)})
            return res
        else:
            raise UserError(_(
                "The product doesn't have replacement service!"))
