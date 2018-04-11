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


class StockPicking(Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one('project.project', string="Project")
    attachment_ids = fields.Many2many('ir.attachment', compute='_compute_attachment_ids', string="Main Attachments")
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(string="Shipping",
                                   compute="_get_merge_address")
    invoice_address = fields.Text(string="Billing",
                                  compute="_get_merge_address")
    repair_requests = fields.Boolean(string='Repair request')
    mess_operated = fields.Boolean('Message Operated', default=False)
    reason = fields.Selection([
        ('0', 'End project-work'),
        ('2', 'Change Because of Malfunction'),
        ('1', 'It seems very expensive'),
        ('3', 'Bad attention'),
        ('2', 'The equipment did not serve you'),
        ('0', 'No longer need it'),
    ], string="Reason")

    @api.one
    def generate_repair_requests(self):
        """
        Method to create massive repair requests from stock
        pickings
        return: None
        """
        mrp_repair_obj = self.env['mrp.repair']
        for l in self.move_lines:
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

    def _compute_attachment_ids(self):
        """
        Get the products attachments
        """
        for data in self:
            for products in data.move_lines:
                attachment_ids = self.env[
                    'ir.attachment'].search([
                        ('res_id', '=', products.product_tmpl_id.id), ('res_model', '=', 'product.template')]).ids
                message_attachment_ids = self.mapped(
                    'message_ids.attachment_ids').ids
                data.attachment_ids = list(
                    set(attachment_ids) - set(
                        message_attachment_ids))

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        super(StockPicking, self).onchange_picking_type()
        if self.partner_id:
            self.project_id = False

    @api.depends('project_id')
    def _get_merge_address(self):
        """
        This function verify if a project has been selected and return a
        merge address for shipping and invoice to the user.

        :return: None
        """
        for spk in self:
            if spk.project_id:
                p = spk.project_id
                spk.shipping_address = spk.merge_address(
                    p.street1 or '', p.street1_2 or '', p.city or '',
                    p.municipality_id.name or '', p.state_id.name or '',
                    p.zip or '', p.country_id.name or '', p.phone1 or '',
                    p.email or '')
                spk.invoice_address = spk.merge_address(
                    p.street2_1 or '', p.street2_2 or '', p.city2 or '',
                    p.municipality2_id.name or '', p.state2_id.name or '',
                    p.zip2 or '', p.country2_id.name or '', p.phone2 or '',
                    p.email or '')

    @staticmethod
    def merge_address(street, street2, city, municipality, state, zip_code,
                      country, phone, email):
        """
        This function receive text fields for merge the address fields.

        :param street: The text field for the address to merge.
        :param street2: The text field for the second line of
         the address to merge.
        :param city: The text field for the city of the address to merge.
        :param municipality: the text for the municipality to merge.
        :param state: The text for the state to merge.
        :param zip_code: the text for the zip code of the address.
        :param country: the text for the name of the country.
        :param phone: the phone in text.
        :param email: the email on string.

        :return: merge string with
        street+street2+city+municipality+state+zip+country
        """
        values = [street, ', ', street2, ', ', city, ', ', municipality, ', ',
                  state, ',', zip_code, ', ', country, ', ', phone, ', ',
                  email]
        out_str = ''
        for num in range(len(values)):
            out_str += values[num]
        return out_str

    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        # ~ Change the product state when is moved to other location.
        for picking in self:
            for move in picking.move_lines:
                if move.product_id.rental:
                    move.product_id.write(
                        {'state_id': move.location_dest_id.product_state.id,
                         'color': move.location_dest_id.color,
                         'location_id': move.location_dest_id.id})
                    move.product_id.product_tmpl_id.write(
                        {'state_id': move.location_dest_id.product_state.id,
                         'color': move.location_dest_id.color,
                         'location_id': move.location_dest_id.id})
        return result

    @api.model
    def create(self, vals):

        if vals.get('partner_id'):
            partner = self.env['res.partner'].search(
                [('id', '=', vals.get('partner_id'))])
            if partner.picking_warn == 'block':
                raise UserError(_(partner.picking_warn_msg))

        res = super(StockPicking, self).create(vals)
        return res
