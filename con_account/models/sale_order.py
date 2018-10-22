# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2018 IAS (<http://www.ias.com.co>).
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
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    init_date_invoice = fields.Date(
        string='Init Date')
    end_date_invoice = fields.Date(
        string='End Date')

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order.
         This method may be
        overridden to implement custom invoice generation
        (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({'init_date_invoice': self.init_date_invoice,
                             'end_date_invoice': self.end_date_invoice,
                             'invoice_type': self.order_type})

        return invoice_vals

