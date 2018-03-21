# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class report_project_product_available(models.AbstractModel):
    _name = 'report.con_project_works.report_product_project'

    @api.model
    def get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'project.project',
            'data': dict(data),
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'selectionby': data['form']['selectionby'],
            'project_ids': self.env[
                'project.project'].browse(data['form']['project_ids']),
            'partners': self.env[
                'res.partner'].browse(data['form']['partner_ids'])
        }