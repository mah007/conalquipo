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
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    mess_operated = fields.Boolean('Message Operated', default=False)
    reason = fields.Selection([
        ('0', 'End project-work'),
        ('2', 'Change Because of Malfunction'),
        ('1', 'It seems very expensive'),
        ('3', 'Bad attention'),
        ('2', 'The equipment did not serve you'),
        ('0', 'No longer need it'),
    ], string="Reason")


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    assigned_operator = fields.Many2one('res.users', string="Assigned Operator")

    @api.model
    def create(self, vals):
        res = super(StockMoveLine, self).create(vals)

        if res.product_id.is_operated \
                and res.move_id.sale_line_id.service_operator:
            res.picking_id.update({'mess_operated': True})

        return res

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):
        if self.assigned_operator:
            mess_operated = False
            for line in self.move.move_line_ids:
                if not line.assigned_operator:
                    mess_operated = True
            self.move.picking_id.write({'mess_operated': mess_operated})
