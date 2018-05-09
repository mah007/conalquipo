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

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _get_default_country(self):
        country = self.env[
            'res.country'].search([('code', '=', 'CO')], limit=1)
        return country

    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict',
        default=_get_default_country)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        ondelete='restrict')
    municipality_id = fields.Many2one(
        'res.country.municipality',
        string='Municipality')'
