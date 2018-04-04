# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportProjectProductAvailable(models.AbstractModel):
    _name = 'report.con_project_works.report_product_project'

    @api.model
    def get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        selectionby = data['form']['selectionby']
        project_ids = self.env[
            'project.project'].browse(
                data.get('form', {}).get('project_ids', False))
        partner_ids = self.env[
            'res.partner'].browse(
                data.get('form', {}).get('partner_ids', False))
        move_line_ids = self.env[
            'stock.move.line'].browse(
                data.get('form', {}).get('move_line_ids', False))
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.move.line',
            'data': dict(data,
                         date_from=date_from,
                         date_to=date_to,
                         selectionby=selectionby,
                         project_ids=project_ids,
                         partner_ids=partner_ids,
                         move_line_ids=move_line_ids),}