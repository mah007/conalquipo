# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    init_date_invoice = fields.Datetime(
        string='Init Date')
    end_date_invoice = fields.Datetime(
        string='End Date')

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
