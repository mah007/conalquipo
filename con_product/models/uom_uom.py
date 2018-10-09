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

from odoo import tools, models, fields, api, _
from odoo.exceptions import UserError


class UomUoM(models.Model):
    _inherit = 'uom.uom'

    @api.multi
    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP',
                          rent=False):
        if not self:
            return qty
        self.ensure_one()
        if not rent:
            if self.category_id.id != to_unit.category_id.id:
                if self._context.get('raise-exception', True):
                    raise UserError(_(
                        'Conversion from Product UoM %s to Default UoM %s '
                        'is not possible as they both belong to different '
                        'Category!.') % (self.name, to_unit.name))
                return qty
        amount = qty / self.factor
        if to_unit:
            amount = amount * to_unit.factor
            if round:
                amount = tools.float_round(amount,
                                           precision_rounding=to_unit.rounding,
                                           rounding_method=rounding_method)
        return amount
