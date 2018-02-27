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

from odoo import models, api, _
import logging
_logger = logging.getLogger(__name__)


class StockMoveComponents(models.Model):
    _inherit = "stock.move"

    def get_components(self):
        if self.product_id.components_ids:
            for data in self.product_id.components_ids:
                self.env['stock.move'].create({
                    'name': _('New Move:') + 'Hola',
                    'product_id': data.product_child_id.id,
                    'product_uom_qty': data.quantity,
                    'product_uom': data.product_child_id.product_tmpl_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.picking_id.id
                })