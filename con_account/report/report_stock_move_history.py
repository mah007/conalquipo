from odoo import api, models
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class ReportAccountStockMove(models.AbstractModel):
    _name = 'report.con_account.account_stock_move_report'

    @api.model
    def get_report_values(self, docids, data=None):
        if not self.env.context.get(
            'active_model') or not self.env.context.get(
                    'active_id'):
                raise UserError(_(
                    "Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data,
            'docs': docs,
        }
