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

from odoo import fields, models


class PartnerWarnings(models.Model):
    _name = "partner.warnings"

    name = fields.Char(string='Code')
    warning_type = fields.Selection([('sale_warn', 'In Sale'),
                                     ('picking_warn', 'In Picking')])
    message_type = fields.Selection([('no-message', 'Message'),
                                     ('warning', 'Warning'),
                                     ('block', 'Block')], string="Type")
    message_body = fields.Text(string="Message")


class ResPartner(models.Model):
    _inherit = "res.partner"

    trust_code = fields.Many2one('partner.warnings', string="Trust Code")
