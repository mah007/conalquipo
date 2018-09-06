# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone, utc


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
                self.init_date_invoice, date_format)
            end = datetime.strptime(
                self.end_date_invoice, date_format)
            if end < init:
                self.init_date_invoice = False
                self.end_date_invoice = False
                raise UserError(_(
                    'End day can not be less than init day'))

    @api.multi
    def create_invoices(self):
        # TODO: Found a better way to do this
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        date_format = "%Y-%m-%d"
        invoice = self.env['account.invoice'].search(
            [('id', '=', res['res_id'])])
        date_init = datetime.strptime(
            self.init_date_invoice,
            date_format)
        date_end = datetime.strptime(
            self.end_date_invoice,
            date_format)
        if invoice.invoice_type == 'rent':
            invoice.write({
                'init_date_invoice': date_init,
                'end_date_invoice': date_end})
        return res
