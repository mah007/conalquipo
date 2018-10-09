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
        reple_id = self.product_id.product_tmpl_id.replenishment_charge
        if reple_id:
            self.env['sale.order.line'].create({
                'order_id': self.picking_id.sale_id.id,
                'product_id': reple_id.id,
                'product_uom_qty': self.scrap_qty,
                'price_unit': reple_id.lst_price,
                'name': _('Replenishment %s') % (reple_id.default_code),
                'product_uom': reple_id.uom_id.id,
            })

            sign_template = self.env.ref(
                    'con_website_sign.template_con_website_sign_1')
            request_id = self.env['signature.request'].create({
                'sale_id': self.picking_id.sale_id.id,
                'template_id': sign_template.id,
                'state': 'draft',
                'reference': sign_template.share_link,
            })

            picking = self.picking_id
            items = ['signature_con_item_1', 'signature_con_item_2',
                     'signature_con_item_3', 'signature_con_item_4',
                     'signature_con_item_5', 'signature_con_item_6',
                     'signature_con_item_7', 'signature_con_item_8',
                     'signature_con_item_9']
            items_values = [picking.advertisement_date,
                            picking.project_id.partner_id.name,
                            picking.project_id.name,
                            picking.project_id.city,
                            picking.advertisement_date,
                            picking.name,
                            self.product_id.product_tmpl_id.name,
                            self.product_id.product_tmpl_id.default_code]

            d = dict(zip(items, items_values))
            for key, value in d.items():
                self.env['signature.item.value'].create({
                    'signature_item_id': self.env.ref(
                        'con_website_sign.' + str(key)).id,
                    'signature_request_id': request_id.id,
                    'value': value
                })

            return res
        else:
            raise UserError(_(
                "The product doesn't have replacement service!"))
        return res

    @api.multi
    def do_scrap(self):
        res = super(StockScrap, self).do_scrap()
        for scrap in self:
            reple_id = scrap.product_id.product_tmpl_id.replenishment_charge
            if not reple_id:
                raise UserError(_(
                    "The product doesn't have replacement service!"))
            scrap.move_id.update({
                'description': _(
                    'Replenishment %s') % (reple_id.default_code),
                'location_id': self.location_id.id,
                'location_dest_id': self.scrap_location_id.id,
                'state': 'draft'})
        return res


class StockWarnInsufficientQtyScrap(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.scrap'

    def action_done(self):
        res = super(StockWarnInsufficientQtyScrap, self).action_done()
        scrap_id = self.scrap_id
        reple_id = scrap_id.product_id.product_tmpl_id.replenishment_charge
        if reple_id:
            self.env['sale.order.line'].create({
                'order_id': scrap_id.picking_id.sale_id.id,
                'product_id': reple_id.id,
                'product_uom_qty': scrap_id.scrap_qty,
                'price_unit': reple_id.lst_price,
                'name': _('Replenishment %s') % (reple_id.default_code),
                'product_uom': reple_id.uom_id.id})

            sign_template = self.env.ref(
                    'con_website_sign.template_con_website_sign_1')
            request_id = self.env['signature.request'].create({
                'sale_id': scrap_id.picking_id.sale_id.id,
                'template_id': sign_template.id,
                'state': 'draft',
                'reference': sign_template.share_link,
            })

            picking = scrap_id.picking_id
            items = ['signature_con_item_1', 'signature_con_item_2',
                     'signature_con_item_3', 'signature_con_item_4',
                     'signature_con_item_5', 'signature_con_item_6',
                     'signature_con_item_7', 'signature_con_item_8',
                     'signature_con_item_9']
            items_values = [picking.advertisement_date,
                            picking.project_id.partner_id.name,
                            picking.project_id.name,
                            picking.project_id.city,
                            picking.advertisement_date,
                            picking.name,
                            scrap_id.product_id.product_tmpl_id.name,
                            scrap_id.product_id.product_tmpl_id.default_code]

            d = dict(zip(items, items_values))
            for key, value in d.items():
                self.env['signature.item.value'].create({
                    'signature_item_id': self.env.ref(
                        'con_website_sign.' + str(key)).id,
                    'signature_request_id': request_id.id,
                    'value': value
                })
        else:
            raise UserError(_(
                "The product doesn't have replacement service!"))
        return res
