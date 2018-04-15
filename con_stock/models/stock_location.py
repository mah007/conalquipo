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
import logging
_logger = logging.getLogger(__name__)


class StockLocation(Model):
    _inherit = "stock.location"


    @api.multi
    @api.depends('product_state')
    def _get_color(self):
        for a in self:
            if a.product_state:
                a.color = a.product_state.color

    set_product_state = fields.Boolean(
        string="Change the state to all products when arrive to this location")
    product_state = fields.Many2one(
        'product.states', string="Set state")
    color = fields.Char(
        string="Color", compute=_get_color, store=True)
    project_id = fields.One2many('project.project', 'stock_location_id',
                                 string='project')