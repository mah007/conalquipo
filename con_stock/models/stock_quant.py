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
_logger = logging.getLogger(__name__)
from odoo import models, _, api
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, values):
        record = super(StockQuant, self).create(values)
        record.create_compute_locations()
        return record

    @api.multi
    def write(self, values):
        record = super(StockQuant, self).write(values)
        self.update_compute_locations()
        return record

    def create_compute_locations(self):
        for record in self:
            line_ids = []
            if record.product_id.product_tmpl_id.non_mech:
                pro = record.product_id.id
                pro_tmpl = record.product_tmpl_id.id
                loc = record.location_id
                state = record.location_id.product_state.id
                color = record.location_id.color
                if loc.usage not in ['view', 'inventory', 'transit']:
                    val = {
                        'product_id': pro,
                        'product_tmpl_id': pro_tmpl,
                        'location_id': loc.id,
                        'state_name': state,
                        'color': color,
                        'qty': record.quantity
                    }
                    line_ids.append((0, 0, val))
                record.product_tmpl_id.states_nonmech_ids = [
                    i for n, i in enumerate(
                        line_ids) if i not in line_ids[n + 1:]]

    def update_compute_locations(self):
        for record in self:
            if record.product_id.product_tmpl_id.non_mech:
                for data in record.product_tmpl_id.states_nonmech_ids:
                    if record.location_id.id == data.location_id.id:
                        val = {
                            'product_id': record.product_id.id,
                            'product_tmpl_id': record.product_tmpl_id.id,
                            'location_id': record.location_id.id,
                            'state_name': record.location_id.product_state.id,
                            'color': record.location_id.color,
                            'qty': record.quantity
                        }
                        data.write(val)
