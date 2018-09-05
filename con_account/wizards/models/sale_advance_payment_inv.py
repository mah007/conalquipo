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

    init_date_invoice = fields.Datetime(
        string='Init Date')
    end_date_invoice = fields.Datetime(
        string='End Date')

    @api.onchange('init_date_invoice', 'end_date_invoice')
    def _onchange_dates(self):
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
        local = timezone(self._context['tz'])
        res = super(SaleAdvancePaymentInv, self).create_invoices()

        invoice = self.env['account.invoice'].search(
            [('id', '=', res['res_id'])])
        date_init = datetime.strptime(self.init_date_invoice,
            DEFAULT_SERVER_DATETIME_FORMAT).replace(
                hour=0, minute=0, second=0, microsecond=0)
        local_dt_init = local.localize(date_init, is_dst=None)
        utc_dt_init = local_dt_init.astimezone(utc)

        _logger.info("Pass")
        date_end = datetime.strptime(self.end_date_invoice,
             DEFAULT_SERVER_DATETIME_FORMAT).replace(
                 hour=23, minute=59, second=59, microsecond=0)
        local_dt_end = local.localize(date_end, is_dst=None)
        utc_dt_end = local_dt_end.astimezone(utc)

        if invoice.invoice_type == 'rent':
            invoice.write({
                'init_date_invoice': utc_dt_init,
                'end_date_invoice': utc_dt_end})
        return res
