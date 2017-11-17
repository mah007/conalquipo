# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pack_operation_ids = fields.One2many('stock.pack.operation',
                                         compute='compute_pack_operation')

    add_bom = fields.Boolean('Display BOM Products on Invoice Report')

    @api.multi
    def compute_pack_operation(self):
        for invoice in self:

            order = self.env['sale.order'].search([
                ('order_line.invoice_lines.invoice_id', '=', invoice.id)
            ])
            if order:
                pickings = order.mapped('picking_ids')
                if pickings:
                    pack_operations = \
                        pickings.mapped('pack_operation_product_ids')

                    invoice.pack_operation_ids = pack_operations
