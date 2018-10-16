# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportProjectInvoice(models.AbstractModel):
    _name = 'report.con_account.account_project_invoice_report'

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        form = data['form']
        values = {
            'doc_ids': docs.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
        }
        values.update(form)
        return values
