from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingEquipmentChangeWizard(models.TransientModel):
    _name = "stock.picking.equipment.change.wizard"
    track_visibility = 'onchange',
    reason = fields.Text("Reason")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    product_ids = fields.One2many('product.change.wizard', 'equipment_cw_id',
                                  string="Product Change")

    @api.multi
    def action_change(self):
        for new_p in self.product_ids:
            if new_p.new_product_id:
                new_p.move_line.update({'product_id': new_p.new_product_id.id})
                new_p.move_line.sale_line_id.update(
                    {'product_id': new_p.new_product_id.id})
        return {'type': 'ir.actions.act_window_close'}


class ProductChangeWizard(models.TransientModel):
    _name = "product.change.wizard"

    equipment_cw_id = fields.Many2one('stock.picking.equipment.change.wizard',
                                      'equipment.change.wizard', )
    ant_product_id = fields.Many2one('product.product', string='product Ant')
    new_product_id = fields.Many2one('product.product', string='Product New')
    move_line = fields.Many2one('stock.move', string="Stock move")

    @api.onchange('new_product_id')
    def _onchange_new_product(self):
        if self.move_line.product_uom_qty > self.new_product_id.qty_available:
            raise UserError(_("selected product does not have quantity "
                              "available in the inventory"))
