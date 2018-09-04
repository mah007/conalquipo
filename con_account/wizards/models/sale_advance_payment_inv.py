# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    init_date_invoice = fields.Datetime(
        string='Init Date')
    end_date_invoice = fields.Datetime(
        string='End Date')

    @api.onchange('init_date_invoice', 'end_date_invoice')
    def _onchange_dates(self):
        date_format = "%Y-%m-%d %H:%M:%S"
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
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        invoice = self.env['account.invoice'].search(
            [('id', '=', res['res_id'])])
        if invoice.invoice_type == 'rent':
            invoice.write({
                'init_date_invoice': self.init_date_invoice,
                'end_date_invoice': self.end_date_invoice})
        return res
