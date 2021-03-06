from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingEquipmentChangeWizard(models.TransientModel):
    _name = "stock.picking.equipment.change.wizard"

    reason = fields.Text("Reasons for cancellation")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    product_ids = fields.One2many('product.change.wizard', 'equipment_cw_id',
                                  string="Product Change")

    @api.multi
    def action_change(self):
        for new_p in self.product_ids:
            if new_p.new_product_id:
                new_p.move_line.update({
                    'product_id': new_p.new_product_id.id,
                    'description': new_p.product_desc})
                new_p.move_line.sale_line_id.update(
                    {'product_id': new_p.new_product_id.id,
                     'name': new_p.product_desc})
                     
                # Update description on sale order line
                for desc in self.picking_id.sale_id.order_line:
                    new_name = 'Comp ' + \
                     new_p.new_product_id.default_code
                    if desc.parent_line.id == new_p.move_line.sale_line_id.id:
                        desc.update({
                            'name': new_name})

                # Update description on stock move
                for desc in self.picking_id.move_lines:
                    new_name = 'Comp ' + \
                     new_p.new_product_id.default_code
                    if desc.sale_line_id.parent_line.id == \
                     new_p.move_line.sale_line_id.id:
                        desc.update({
                            'parent_sale_line': \
                             desc.sale_line_id.parent_line.id,
                            'description': new_name})

                self.env['stock.move.line']._log_message(
                    new_p.move_line.picking_id, new_p.move_line.id,
                    'con_shipping.equipment_change_template',
                    {'reason': self.reason,
                     'ant_product_id': new_p.ant_product_id.name,
                     'new_product_id': new_p.new_product_id.name})
        return {'type': 'ir.actions.act_window_close'}


class ProductChangeWizard(models.TransientModel):
    _name = "product.change.wizard"

    equipment_cw_id = fields.Many2one('stock.picking.equipment.change.wizard',
                                      'equipment.change.wizard', )
    ant_product_id = fields.Many2one('product.product', string='product Ant')
    new_product_id = fields.Many2one('product.product', string='Product New')
    product_desc = fields.Char(string='Description')
    move_line = fields.Many2one('stock.move', string="Stock move")

    @api.onchange('new_product_id')
    def _onchange_new_product(self):
        text = _(" change by ")
        self.product_desc = \
         str(self.new_product_id.default_code) + \
          text + str(self.ant_product_id.default_code)
        if self.ant_product_id.id == self.new_product_id.id:
            raise UserError(_("You can't select the same product"))
        if self.move_line.product_uom_qty > self.new_product_id.qty_available:
            raise UserError(_("selected product does not have quantity "
                              "available in the inventory"))
