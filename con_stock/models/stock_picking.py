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

from odoo.models import Model, api
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

    pack_detail_product = fields.One2many(
        'stock.pack.detail.product', 'picking_id', 'pack Detail Product',
        domain=[('product_id', '!=', False)])

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


class StockPickingDetailProduct(Model):
    _name = "stock.pack.detail.product"

    picking_id = fields.Many2one('stock.picking', 'Stock Picking')

    product_id = fields.Many2one('product.product', 'Product',
                                 ondelete="cascade")

    operator_ids = fields.Many2one(comodel_name='hr.employee',
                                   string='Operator')

    observation = fields.Char(string="Observation")

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        doamin = {}
        if self.product_id:

            if not self.operator_ids:
                self.operator_ids = self.product_id.employee_ids.ids
                doamin.update(
                    {'operator_ids': [('id', 'in',
                                       self.product_id.employee_ids.ids)]})
            # if not self.is_operated:
            #     self.update({'is_operated': self.product_id.is_operated})
            # else:
            #     self.update({'is_operated': self.product_id.is_operated})

            res = {'domain': doamin}
        else:
            res = {'domain': {'product_uom_id': []}}
        return res

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
