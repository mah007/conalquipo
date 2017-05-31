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
from odoo.models import Model
from odoo import fields, api


class Characteristic(Model):
    _name = "characteristic"

    code = fields.Char(string='Code', track_visibility='onchange')
    name = fields.Char(string='Name', track_visibility='onchange')


class ProductCharacteristic(Model):
    _name = "product.characteristic"

    product_id = fields.Many2one(comodel_name='product.template',
                                 string='Product', ondelete='cascade',
                                 index=True, copy=False,
                                 track_visibility='onchange')

    characteristic_id = fields.Many2one(comodel_name='characteristic',
                                        string='Characteristic',
                                        ondelete='cascade',
                                        index=True, copy=False,
                                        track_visibility='onchange')


class ProductTemplate(Model):
    _inherit = "product.template"

    characteristic = fields.One2many('product.characteristic',
                                     'product_id',
                                     string='Product Characteristic',
                                     copy=True, track_visibility='onchange')

    @api.onchange('characteristic')
    def onchange_characteristic(self):
        if self.characteristic:
            for char in self.characteristic:
                char.product_id = self._origin.id
            self.update({'characteristic': self.characteristic})
