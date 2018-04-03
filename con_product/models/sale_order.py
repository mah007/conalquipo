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
from odoo import fields
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

    product_components = fields.Boolean('Have components?')
    min_sale_qty = fields.Boolean('Min Sale QTY')
    components_ids = fields.Many2many(
        'product.components', string='Components')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        """Overloaded on changed function for product_id.

          This overload check if the line have a componentes and update the
          field product_components with a boolean value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the product information.

        """
        result = super(SaleOrderLine, self).product_id_change()
        components_ids = self.product_id.product_tmpl_id.components_ids
        if components_ids:
            self.product_components = True
            self.components_ids = components_ids
        return result

    @api.onchange('bill_uom', 'bill_uom_qty')
    def min_bill_qty(self):
        """
        Get min qty and uom of product
        """
        product_muoms = self.product_id.product_tmpl_id.multiples_uom
        if product_muoms != True:
            if self.bill_uom and self.bill_uom_qty > 0.0:
                self.price_unit = self.product_id.product_tmpl_id.list_price
        else:
            if self.bill_uom and self.bill_uom_qty > 0.0:
                for uom_list in self.product_id.product_tmpl_id.uoms_ids:
                    if self.bill_uom.id == uom_list.uom_id.id:
                        self.price_unit = uom_list.cost_byUom                 

    @api.model
    def create(self, values):
        """
        Get min qty and uom of product
        """
        record = super(SaleOrderLine, self).create(values)
        product_muoms = record.product_id.product_tmpl_id.multiples_uom
        if product_muoms != True:
            record.price_unit = record.product_id.product_tmpl_id.list_price
        else:
            for uom_list in record.product_id.product_tmpl_id.uoms_ids:
                if record.bill_uom.id == uom_list.uom_id.id:
                    record.price_unit = uom_list.cost_byUom                
        # Create in lines extra products for componentes
        if record.components_ids:
            for data in record.components_ids:
                if data.extra:
                    qty = data.quantity * record.product_uom_qty
                    new_line = {
                        'product_id': data.product_child_id.id,
                        'name': 'Extra component for %s'%(
                            record.product_id.name),
                        'order_id': record.order_id.id,
                        'product_uom_qty': qty,
                        'bill_uom_qty': qty,
                        '': data.product_child_id.product_tmpl_id.uom_id.id
                    } 
                    super(SaleOrderLine, self).sudo().create(new_line)
        return record