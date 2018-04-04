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

from odoo import models, fields, api


class ResPartnerCode(models.Model):
    _inherit = "res.partner"

    partner_code = fields.Char(string='Partner Code')
    l10n_co_document_type = fields.Selection(
        selection_add=[('nit', 'NIT')])
    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')

    @api.model
    def create(self, values):
        values['partner_code'] = self.env[
            'ir.sequence'].next_by_code('res.partner.code')
        res = super(ResPartnerCode, self).create(values)
        return res
