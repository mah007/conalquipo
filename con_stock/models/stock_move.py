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

from odoo.models import Model, api, _
from odoo import fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class StockMove(Model):
    _inherit = "stock.move"

    project_id = fields.Many2one(
        'project.project', string="Project", compute='_get_project',
        store=True)
    partner_id = fields.Many2one(
        'res.partner', string="Partner", compute='_get_partner',
        store=True)
    button_pushed = fields.Boolean(
        string="Button pushed", default=False)
    child_product = fields.Boolean(
        string="Child product", default=False)
    mrp_repair_id = fields.Many2one(
        'mrp.repair', string='Repair request')

    def get_components_button(self):
        """
        Button to get the components of a product
        """
        trigger = False
        move_obj = self.env['stock.move']
        if not self.product_id.components_ids:
            raise UserError(_("The following product '%s' dont"
                              " have components") % self.product_id.name)
        if self.product_id.components_ids and not self.button_pushed:
            trigger = True
        if trigger:
            self.button_pushed = True
            for data in self.sale_line_id.components_ids:
                if not data.extra:
                    name = data.product_id.product_tmpl_id.name
                    uom = data.product_id.product_tmpl_id.uom_id.id
                    move_obj.create({
                        'name': _(
                            'Components:') + name,
                        'product_id': data.product_id.id,
                        'product_uom_qty': data.quantity,
                        'product_qty': data.quantity,
                        'product_uom': uom,
                        'origin': self.origin,
                        'partner_id': self.partner_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'picking_id': self.picking_id.id,
                        'state': self.state,
                        'group_id': self.group_id.id,
                        'rule_id': self.rule_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'child_product': True,
                        'sale_line_id': self.sale_line_id.id
                    })
        else:
            raise UserError(_("The following product '%s' already"
                              " has its components"
                              ) % self.product_id.name)

    def _get_project(self):
        for data in self:
            data.project_id = data.picking_id.project_id.id

    def _get_partner(self):
        for data in self:
            data.partner_id = data.picking_id.partner_id.id

class StockMoveLine(Model):
    _inherit = "stock.move.line"

    project_id = fields.Many2one(
        'project.project', string="Project", compute='_get_project',
        store=True)
    partner_id = fields.Many2one(
        'res.partner', string="Partner", compute='_get_partner',
        store=True)
    project_id = fields.Many2one('project.project', string='Work')
    assigned_operator = fields.Many2one(
        'res.users', string="Assigned Operator")

    def _get_project(self):
        for data in self:
            data.project_id = data.picking_id.project_id.id

    def _get_partner(self):
        for data in self:
            data.partner_id = data.picking_id.partner_id.id

    @api.model
    def create(self, vals):
        res = super(StockMoveLine, self).create(vals)

        if res.product_id.is_operated \
                and res.move_id.sale_line_id.service_operator:
            res.picking_id.update({'mess_operated': True})

        return res

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):
        if self.assigned_operator:
            mess_operated = False
            for line in self.move.move_line_ids:
                if not line.assigned_operator:
                    mess_operated = True
            self.move.picking_id.write({'mess_operated': mess_operated})
