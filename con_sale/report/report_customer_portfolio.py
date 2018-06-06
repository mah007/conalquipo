# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportCustomerPortfolio(models.AbstractModel):
    _name = 'report.con_sale.report_customer_portfolio'

    @api.model
    def get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        partner_ids = self.env[
            'res.partner'].browse(
                data.get('form', {}).get('partner_ids', False))
        invoice_ids = self.env[
            'account.invoice'].browse(
                data.get('form', {}).get('invoice_ids', False))
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'account.invoice',
            'data': dict(data,
                         partner_ids=partner_ids,
                         invoice_ids=invoice_ids),}