# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportProjectProductAvailable(models.AbstractModel):
    _name = 'report.con_project.report_product_project'

    @api.model
    def get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        project_ids = self.env[
            'project.project'].browse(
                data.get('form', {}).get('project_ids', False))
        partner_ids = self.env[
            'res.partner'].browse(
                data.get('form', {}).get('partner_ids', False))
        products_ids = self.env[
            'product.product'].browse(
                data.get('form', {}).get('products_ids', False))
        in_move_ids = self.env[
            'stock.move'].browse(
                data.get('form', {}).get('in_move_ids', False))
        out_move_ids = self.env[
            'stock.move'].browse(
                data.get('form', {}).get('out_move_ids', False))
        picking_ids = self.env[
            'stock.picking'].browse(
                data.get('form', {}).get('picking_ids', False))
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'stock.move',
            'data': dict(data,
                         products_ids=products_ids,
                         project_ids=project_ids,
                         picking_ids=picking_ids,
                         partner_ids=partner_ids,
                         in_move_ids=in_move_ids,
                         out_move_ids=out_move_ids),}