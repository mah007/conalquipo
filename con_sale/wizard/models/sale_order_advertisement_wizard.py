from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrderAdvertisementWizard(models.TransientModel):
    _name = "sale.order.advertisement.wizard"

    project_id = fields.Many2one('project.project', string="Project")
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    partner_id = fields.Many2one('res.partner', 'Partner')
    location_id = fields.Many2one('stock.location', "Source Location")
    location_dest_id = fields.Many2one('stock.location',
                                       "Destination Location",
                                       domain=[('usage', '=', 'internal')])
    reason = fields.Selection([
        ('0', 'End project-work'),
        ('2', 'Change Because of Malfunction'),
        ('1', 'It seems very expensive'),
        ('3', 'Bad attention'),
        ('2', 'The equipment did not serve you'),
        ('0', 'No longer need it'),
    ], string="Reason")

    notes = fields.Text(string="Notes",)

    @api.multi
    def action_create_advertisement(self):

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'project_id': self.project_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'origin': self.sale_order_id.name,
            'sale_id': self.sale_order_id.id,
            'group_id': self.sale_order_id.procurement_group_id.id,
            'return_reason': self.reason,
            'user_notes': self.notes
        })
        stock_move = self.env['stock.move'].search(
            [('location_dest_id', '=', self.location_id.id),
             ('state', '=', 'done'),
             ('picking_id.project_id', '=', self.project_id.id)])

        for move in stock_move:
            new_move = self.env['stock.move'].create({
                'name': _('New Move:') + move.product_id.display_name,
                'product_id': move.product_id.id,
                'product_uom_qty': move.quantity_done,
                'product_uom': move.product_uom.id,
                'location_dest_id': self.location_dest_id.id,
                'location_id': self.location_id.id,
                'returned': move.id,
                'picking_id': picking.id,
                'group_id': move.group_id.id,
                'state': 'draft',
                'button_pushed': True,
                'sale_line_id': move.sale_line_id.id,
            })

        self.sale_order_id.update({'picking_ids': [(4, picking.id)]})

        return {'type': 'ir.actions.act_window_close'}

