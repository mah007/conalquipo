# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
_LOGGER = logging.getLogger(__name__)
from openerp import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.one
    @api.depends(
        'product_uom_qty',
        'product_id')
    def _fnct_line_stock(self):
        available = self.product_id.qty_available - self.product_uom_qty
        if available < 0.0:
            available = 0.0
        self.real_available = available

    real_available = fields.Float(
        compute="_fnct_line_stock", string='Real Stock')
