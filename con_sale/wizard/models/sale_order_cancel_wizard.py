from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrderCancelWizard(models.TransientModel):
    _name = "sale.order.cancel.wizard"
    _rec_name = "cancel_options"

    cancel_options = fields.Selection(
        [('no_vehicle_availability', 'No vehicle availability'),
         ('no_team_maintenance', 'There is no product for Maintenance'),
         ('no_operator', 'There is no operator'),
         ('no_stock', 'There is no stock'),
         ('hogh_prices', ' High prices'),
         ('i_got_it', 'I already got it'),
         ('not_need-it', 'He does not need it'),
         ('delay_response', 'Delay in response'),
         ('Other', 'Other')],
        string='Cancel reason')
    partner_id = fields.Many2one("res.partner", string="Partner")
    project_id = fields.Many2one("project.project", string="Project")
    sale_order_id = fields.Many2one("sale.order", string="Sale order")
    notes = fields.Text(string="Reason for cancellation")

    @api.multi
    def make_cancellation(self):
        for record in self:
            record.sale_order_id.update({
                'cancel_options': record.cancel_options
            })
            record.sale_order_id.action_cancel()

        return {'type': 'ir.actions.act_window_close'}