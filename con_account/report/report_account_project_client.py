# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportProjectCreate(models.AbstractModel):
    _name = 'report.con_account.project_create_report'


    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        date_from = data['form'].get("from")
        date_to = data['form'].get("to")
        invoiced_work = data['form'].get("invoiced_work")
        return {
            'doc_ids': docs.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'date_from': date_from,
            'date_to': date_to,
            'invoiced_work': invoiced_work,
        }
