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
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = "repair.order"

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        track_visibility='onchange')

    @api.multi
    def write(self, values):
        # Overwrite repair write
        res = super(RepairOrder, self).write(values)
        if self.invoice_id and self.project_id:
            mrp_name = self.name
            code = '[' + self.product_id.default_code + ']'
            name = self.product_id.product_tmpl_id.name
            total_desc = mrp_name + ' - ' + code + ' ' + name
            self.invoice_id.write({
                'project_id': self.project_id.id,
                'name': total_desc})
        return res
