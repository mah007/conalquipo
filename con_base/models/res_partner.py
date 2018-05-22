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

    def _default_category(self):
        return self.env[
            'res.partner.category'].browse(
                self._context.get('category_id'))

    partner_code = fields.Char(
        string='Partner Code')
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
    municipality_id = fields.Many2one(
        'res.country.municipality',
        string='Municipality')
    category_id = fields.Many2many(
        'res.partner.category',
        column1='partner_id',
        column2='category_id',
        string='Tradename',
        default=_default_category)
    property_product_pricelist = fields.Many2one(
        'product.pricelist',
        'Sale Pricelist',
        compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist",
        company_dependent=False,
        help="""
            This pricelist will be used, instead of the default one,
            for sales to the current partner""",
        track_visibility='onchange')
    can_edit_pricelist = fields.Boolean(
        compute='_compute_can_edit_pricelist')
    documents_delivered = fields.Boolean(
        string='Documents delivered',
        track_visibility='onchange')

    def _compute_can_edit_pricelist(self):
        for data in self:
            data.can_edit_pricelist = self.env.user.has_group(
                'con_profile.group_commercial_director')

    @api.multi
    @api.depends('country_id')
    def _compute_product_pricelist(self):
        for p in self:
            if not isinstance(p.id, models.NewId):  # if not onchange
                p.property_product_pricelist = self.env['product.pricelist']._get_partner_pricelist(p.id)

    @api.model
    def create(self, values):
        values['partner_code'] = self.env[
            'ir.sequence'].next_by_code('res.partner.code')
        res = super(ResPartnerCode, self).create(values)
        return res


