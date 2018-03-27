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

from odoo.models import Model, api
from odoo import fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class StockMove(Model):
    _inherit = "stock.move"

    project_id = fields.Many2one(
        'project.project', string="Project", compute='_get_project')
    partner_id = fields.Many2one(
        'res.partner', string="Partner", compute='_get_partner')

    def _get_project(self):
        for data in self:
            data.project_id = data.picking_id.project_id.id

    def _get_partner(self):
        for data in self:
            data.partner_id = data.picking_id.partner_id.id

class StockMoveLine(Model):
    _inherit = "stock.move.line"

    project_id = fields.Many2one(
        'project.project', string="Project", compute='_get_project')
    partner_id = fields.Many2one(
        'res.partner', string="Partner", compute='_get_partner')

    def _get_project(self):
        for data in self:
            data.project_id = data.picking_id.project_id.id

    def _get_partner(self):
        for data in self:
            data.partner_id = data.picking_id.partner_id.id