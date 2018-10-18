# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT, float_compare,
                        float_is_zero)
from pytz import timezone, utc

_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    init_date_invoice = fields.Date(
        string='Init Date')
    end_date_invoice = fields.Date(
        string='End Date')

    @api.onchange('init_date_invoice', 'end_date_invoice')
    def _onchange_dates(self):
        date_format = "%Y-%m-%d"
        if self.init_date_invoice and self.end_date_invoice:
            init = datetime.strptime(
                self.init_date_invoice, DEFAULT_SERVER_DATETIME_FORMAT)
            end = datetime.strptime(
                self.end_date_invoice, DEFAULT_SERVER_DATETIME_FORMAT)
            if end < init:
                self.init_date_invoice = False
                self.end_date_invoice = False
                raise UserError(_(
                    'End day can not be less than init day'))

    @api.multi
    def create_invoices(self):
        date_format = "%Y-%m-%d"
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))

        date_init = datetime.strptime(
            self.init_date_invoice,
            date_format)
        date_end = datetime.strptime(
            self.end_date_invoice,
            date_format)

        sale_orders.write({
                'init_date_invoice': date_init,
                'end_date_invoice': date_end
        })

        return super(SaleAdvancePaymentInv, self).create_invoices()

