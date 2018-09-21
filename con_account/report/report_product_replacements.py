# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportProductReplacements(models.AbstractModel):
    _name = 'report.con_account.report_product_replacements'

    @api.model
    def get_report_values(self, docids, data=None):
        data = data if data is not None else {}

        partner_ids = self.env['res.partner'].browse(
            data.get('form', {}).get('partner_ids', False)
        )
        project_ids = self.env['project.project'].browse(
            data.get('form', {}).get('project_ids', False)
        )

        move_ids = self.env[
            'stock.move.history'].browse(
                data.get('form', {}).get('move_ids', False))

        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.move',
            'data': dict(data,
                         move_ids=move_ids,
                         partner_ids=partner_ids,
                         project_ids=project_ids,
                         ),}