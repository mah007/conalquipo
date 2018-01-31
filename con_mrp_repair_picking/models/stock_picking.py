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

from odoo import models, api, fields
import logging
_logger = logging.getLogger(__name__)


class StockPickingMRPRepair(models.Model):
    _inherit = "stock.picking"

    repair_requests = fields.Boolean(string='Repair request')

    @api.one
    def generate_repair_requests(self):
        mrp_repair_obj = self.env['mrp.repair']
        for l in self.move_lines:
            _logger.warning('AQUIIIIII')
            _logger.warning(l)
            vals = {
                'product_id': l.product_id.id,
                'partner_id': self.partner_id.id,
                'picking_id': self.id,
                'product_uom_qty': l.product_qty,
                'product_uom': l.product_uom.id,
                'location_dest_id': self.location_dest_id.id,
            }
            _logger.warning(vals)
            repair = mrp_repair_obj.create(vals)
            l.mrp_repair_id = repair.id
            self.repair_requests = True

