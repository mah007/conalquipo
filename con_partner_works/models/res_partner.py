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
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = ('street', 'street2', 'municipality_id',
                  'zip', 'city', 'state_id', 'country_id')

ADDRESS_FORMAT_CLASSES = {
    '%(city)s %(state_code)s\n%(zip)s': 'o_city_state',
    '%(zip)s %(city)s': 'o_zip_city'
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    @api.depends('partner_id')
    def _get_partner_code(self):
        if self.partner_id:
            self.partner_code = self.partner_id.partner_code

    partner_code = fields.Char(string='Partner Code')
    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')
    is_work = fields.Boolean(string="Is a Work?", default=False)
    work_code = fields.Char(string='Work Code')
    work_date_creation = fields.Date(
        string="Work date creation")
    invoice_limit_date = fields.Date(
        string="Invoice limit date")
    observations = fields.Html(string='Observations')
    legal_responsible = fields.Many2one(
        'res.partner', string='Legal Responsible')
    contract_number = fields.Char(string='Contract Number')
    work_responsible = fields.Many2one(
        'res.partner', string='Work Responsible')
    work_resident = fields.Many2one(
        'res.partner', string='Work Resident')
    work_storer = fields.Many2one(
        'res.partner', string='Work Storer')
    work_contract = fields.Many2one(
        'res.partner', string='Work Contract')
    work_phone = fields.Char(string='Work Phone')
    owner_phone = fields.Char(string='Owner Phone')
    work_interventor = fields.Many2one(
        'res.partner', string='Work Interventor')
    interventor_phone = fields.Char(string='Interventor Phone')

    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if name and partner.type in ['invoice', 'delivery', 'other']:
                    _logger.info('Is Here!!! Not Name and Partner '
                                 'Type in In-Del-Other')
                    name = dict(self.fields_get(
                        ['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or
                                       partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + \
                       partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

    @api.multi
    def _display_address(self, without_company=False):
        ''' The purpose of this function is to build and 
        return an address formatted accordingly to the
        standards of the country where it belongs.
        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its
         country habits (or the default ones
            if not country is specified)
        :rtype: string '''

        # get the information that will be injected into the display format
        # get the address format
        address_format = \
            self.country_id.address_format or \
            "%(street)s\n%(street2)s\n%(muni_name)s %(city)s" \
            " %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'muni_code': self.municipality_id.code or '',
            'muni_name': self.municipality_id.name or '',
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.commercial_company_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._address_fields() + [
            'country_id.address_format', 'country_id.code', 'country_id.name',
            'company_name', 'state_id.code', 'state_id.name',
            'municipality_id.code', 'municipality_id.name'
        ]
