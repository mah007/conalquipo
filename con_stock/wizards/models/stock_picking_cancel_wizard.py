from odoo import models, fields, api


class StockPickingCancelWizard(models.TransientModel):
    _name = "stock.picking.cancel.wizard"

    name = fields.Text("Reasons for cancellation")
    picking_ids = fields.Many2many('stock.picking', string="Picking")

    @api.multi
    def action_cancel(self):
        pickings_to_cancel = self.env['stock.picking'].search(
            [('id', 'in', self.picking_ids._ids)])
        for picking in pickings_to_cancel:
            picking.write({'cancel_reason': self.name})
            picking.action_do_cancel()
        return {'type': 'ir.actions.act_window_close'}
