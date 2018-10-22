# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 (<http://www.ias.com.co>).
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
import time
from datetime import datetime, timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT, float_compare,
                        float_is_zero)

_logger = logging.getLogger(__name__)


class SaleProductComponents(models.Model):
    _name = "sale.product.components"
    _description = "A model for store and manage the products components"
    rec_name = "product_id"

    sale_line_id = fields.Many2one(
        'sale.order.line', string="Sale line")
    product_id = fields.Many2one(
        'product.product', string="Product component")
    quantity = fields.Integer('Default quantity', default=1)
    extra = fields.Boolean('Extra product')
    owner_id = fields.Many2one(
        'res.partner', string='Supplier',
        change_default=True, track_visibility='always')
