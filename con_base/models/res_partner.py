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

    @api.model
    def _get_default_country(self):
        country = self.env[
            'res.country'].search([('code', '=', 'CO')], limit=1)
        return country

    partner_code = fields.Char(string='Partner Code')
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict',
        default=_get_default_country)
    l10n_co_document_type = fields.Selection(
        [('nit', 'NIT'),
         ('citizenship_card', 'Citizenship card'),
         ('id_card', 'Tarjeta de Identidad'),
         ('passport', 'Pasaporte'),
         ('foreign_id_card', 'Cedula de Extranjeria'),
         ('external_id', 'ID del Exterior')],
        string='Document Type',
        help='Indicates to what document the information in here belongs to.'
        )
    state_id = fields.Many2one(
        "res.country.state", string='State',
        ondelete='restrict')
    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')
    category_id = fields.Many2many(
        'res.partner.category',
        column1='partner_id',
        column2='category_id',
        string='Tradename',
        default=_default_category)

    def _default_category(self):
        return self.env[
            'res.partner.category'].browse(
                self._context.get('category_id'))

    @api.model
    def create(self, values):
        values['partner_code'] = self.env[
            'ir.sequence'].next_by_code('res.partner.code')
        res = super(ResPartnerCode, self).create(values)
        return res