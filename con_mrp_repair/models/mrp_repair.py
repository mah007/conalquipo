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


class MRPRepair(models.Model):
    _inherit = "mrp.repair"

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        track_visibility='onchange')

    @api.multi
    def write(self, values):
        # Overwrite mrp repair write
        res = super(MRPRepair, self).write(values)
        _logger.warning(self)
        _logger.warning(values)
        _logger.warning(res)
        if self.invoice_id and self.project_id:
            self.invoice_id.write({
                'project_id': self.project_id.id})
        return res
