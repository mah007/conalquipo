# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 Tiny SPRL (<http://www.ias.com.co>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.models import Model, api, _
from odoo import fields
import logging

_logger = logging.getLogger(__name__)


class StockPicking(Model):
    _inherit = "stock.picking"

    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         readonly=True,
                                         required=True,
                                         states={
                                             'draft': [('readonly', False)],
                                             'partially_available':
                                                 [('readonly', False)],
                                             'done': [('readonly', False)],
                                             'waiting': [('readonly', False)],
                                             'assigned': [('readonly', False)]
                                         },
                                         help="Invoice address for "
                                              "current sales order.")
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Delivery Address',
                                          readonly=True,
                                          required=True,
                                          states={
                                              'draft': [('readonly', False)],
                                              'partially_available':
                                                  [('readonly', False)],
                                              'done': [('readonly', False)],
                                              'waiting': [('readonly', False)],
                                              'assigned': [('readonly', False)]
                                          },
                                          help="Delivery address for"
                                               " current sales order.")

    receives_maintenance = fields.Many2one(comodel_name='hr.employee',
                                           string='Receives in maintenance',
                                           track_visibility='onchange')

    pack_detail_product_ids = fields.One2many('stock.pack.detail.product',
                                              'picking_id',
                                              'pack Detail Product')

    pack_mechanic_ids = fields.One2many('stock.pack.mechanic', 'picking_id',
                                        'pack Mechanic')

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        moves = self.env['stock.move'].search([('picking_id', '=', res.id)])
        for move in moves:
            if move.product_id:
                detail = {
                    'picking_id': res.id,
                    'product_id': move.product_id.id,
                }
                self.env['stock.pack.detail.product'].create(detail)
                self.env['stock.pack.mechanic'].create(detail)

        return res

    @api.multi
    def write(self, vals):

        res = super(StockPicking, self).write(vals)
        moves = self.env['stock.move'].search([('picking_id', '=', self.id)])
        detail_product = self.env['stock.pack.detail.product']
        mechanic = self.env['stock.pack.mechanic']
        d_product = []
        move_id = []

        if self.pack_detail_product_ids:
            for product in self.pack_detail_product_ids:
                d_product.append(product.product_id.id)
        if moves:
            for mv in moves:
                if mv.product_id:
                    move_id.append(mv.product_id.id)
                    if mv.product_id.id not in d_product:
                        detail = {
                            'picking_id': mv.picking_id.id,
                            'product_id': mv.product_id.id,
                        }
                        detail_product.create(detail)
                        mechanic.create(detail)
            for d in d_product:
                    if d not in move_id:
                        detail_product.search([('product_id', '=',
                                                d)]).unlink()
                        mechanic.search([('product_id', '=', d)]).unlink()

        return res

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        super(StockPicking, self).onchange_picking_type()
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        self.update(values)

    @api.multi
    def state_product(self, product):
        move = self.env['stock.move'].search([
            ('picking_id', '=', self.id),
            ('product_id', '=', product.product_id.id)], limit=1)

        return move.state

    @api.multi
    def is_mechanic(self, product):
        result = self.env['stock.pack.mechanic'].search([
            ('picking_id', '=', self.id),
            ('product_id', '=', product.product_id.id)], limit=1)

        return result


class StockPickingDetailProduct(Model):
    _name = "stock.pack.detail.product"

    picking_id = fields.Many2one('stock.picking', 'Stock Picking')

    product_id = fields.Many2one('product.product', 'Product',
                                 ondelete="cascade")

    product_t_id = fields.Many2one(related='product_id.product_tmpl_id',
                                   String="Product Tem", ondelete="cascade")

    is_operated = fields.Boolean(
        related='product_id.product_tmpl_id.is_operated', string='Is Operated')

    operator_ids = \
        fields.Many2one(comodel_name='hr.employee', string='Operator',
                        domain="[('product_ids', '=', product_t_id)]")

    observation = fields.Char(string="Observation")

    @api.multi
    def action_see_instructive(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product_id.product_tmpl_id.id)]
        attachment_view = \
            self.env.ref('con_stock.view_document_file_kanban_instructive')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                                   Click to upload files to your product.
                               </p><p>
                                   Use this feature to store any files, like
                                   drawings or specifications.
                               </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" %
                       ('product.product', self.product_id.id)
        }


class StockPickingMechanic(Model):
    _name = "stock.pack.mechanic"

    picking_id = fields.Many2one('stock.picking', 'Stock Picking')

    product_id = fields.Many2one('product.product', 'Product',
                                 ondelete="cascade")

    is_mechanic = fields.Boolean(
        related='product_id.product_tmpl_id.is_mechanic', string='Is Operated')

    mechanic_ids = fields.Many2one(comodel_name='hr.employee',
                                   string='Mechanic')

    broken = fields.Boolean(string="Broken")


class SaleOrder(Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._add_picking_detail()
        return res

    @api.multi
    def _add_picking_detail(self):
        for so in self:
            for pk in so.picking_ids:
                for mv in pk.move_lines:
                    res = self.env['stock.pack.detail.product'].search(
                        [('picking_id', '=', pk.id),
                         ('product_id', '=', mv.product_id.id)], limit=1)
                    if not res:
                        detail = {
                            'picking_id': pk.id,
                            'product_id': mv.product_id.id,
                        }
                        self.env['stock.pack.detail.product'].create(
                            detail)
                        self.env['stock.pack.mechanic'].create(
                            detail)

        return True
