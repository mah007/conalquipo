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

from odoo import _, api, fields, exceptions, models


class ResPartnerSector(models.Model):
    _name = 'res.partner.sector'
    _order = "parent_left"
    _parent_order = "name"
    _parent_store = True
    _description = "Sector"

    name = fields.Char(
        required=True, translate=True)
    parent_id = fields.Many2one(
        comodel_name='res.partner.sector',
        ondelete='restrict')
    child_ids = fields.One2many(
        comodel_name='res.partner.sector',
        inverse_name='parent_id',
        string="Children")
    parent_left = fields.Integer(
        'Parent Left', index=True)
    parent_right = fields.Integer(
        'Parent Right', index=True)

    @api.multi
    def name_get(self):
        def get_names(cat):
            """
            Return the list [cat.name, cat.parent_id.name, ...]
            """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [
            (cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise exceptions.ValidationError(
                _('Error! You cannot create recursive sectors.'))
