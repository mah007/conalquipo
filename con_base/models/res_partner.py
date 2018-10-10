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

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class ResPartnerCode(models.Model):
    _inherit = "res.partner"

 
    def _default_category(self):
        return self.env[
            'res.partner.category'].browse(
                self._context.get('category_id'))

    partner_code = fields.Char(
        string='Partner Code')
    l10n_co_document_type = fields.Selection(
        [('nit', 'NIT'),
         ('citizenship_card', 'Citizenship card'),
         ('id_card', 'Tarjeta de Identidad'),
         ('passport', 'Pasaporte'),
         ('foreign_id_card', 'Cedula de Extranjeria'),
         ('external_id', 'ID del Exterior')],
        string='Document Type',
        help='Indicates to what document the information in here belongs to.'
        )
    category_id = fields.Many2many(
        'res.partner.category',
        column1='partner_id',
        column2='category_id',
        string='Tradename',
        default=_default_category)
    property_product_pricelist = fields.Many2one(
        'product.pricelist',
        'Sale Pricelist',
        compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist",
        company_dependent=False,
        help="""
            This pricelist will be used, instead of the default one,
            for sales to the current partner""",
        track_visibility='onchange')
    can_edit_pricelist = fields.Boolean(
        compute='_compute_can_edit_pricelist')
    documents_delivered = fields.Boolean(
        string='Documents delivered',
        track_visibility='onchange')
    can_edit_doc_delivered = fields.Boolean(
        compute='_compute_can_edit_doc_delivered')
    is_administrative_assistant = fields.Boolean(
        compute='_compute_is_administrative_assistant',
        default=True)
    start_day = fields.Integer(
        string='Invoice start day',
        track_visibility='onchange',
        default=1)
    end_day = fields.Integer(
        string='Invoice end day',
        track_visibility='onchange',
        default=15)
    week_list = fields.Selection([
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ], string='Invoice Weekday', track_visibility='onchange')
    messages_id = fields.Many2many(
        'res.partner.messages',
        string="Sale Messages",
        ondelete="restrict",
        track_visibility='onchange')
    messages_picking_id = fields.Many2many(
        'res.partner.messages',
        string="Picking Messages",
        ondelete="restrict",
        track_visibility='onchange')
    messages_account_id = fields.Many2many(
        'res.partner.messages',
        string="Account Messages",
        ondelete="restrict",
        track_visibility='onchange')
    over_credit = fields.Boolean(
        'Allow Over Credit?', track_visibility='onchange')
    contact_person = fields.Boolean(
        'Contact person?', track_visibility='onchange')
    employee_id = fields.Many2one(
        "hr.employee", string='Employee',
        track_visibility='onchange',
        domain=lambda self: self._getemployee())
    employee_code = fields.Char('Employee code')

    @api.onchange('property_product_pricelist')
    def onchange_pricelist(self):
        if self.property_product_pricelist and self.customer:
            invoices = self.env[
                'account.invoice'].search(
                    [('partner_id', '=', self._origin.id),
                     ('state', 'in', ['draft', 'open'])], limit=1)
            sale_order = self.env[
                'sale.order'].search(
                    [('partner_id', '=', self._origin.id),
                     ('state', '!=', 'done')], limit=1)
            if invoices:
                raise exceptions.Warning(_(
                    'This customer has a invoices on '
                    'draft or open state. You can not change '
                    'pricelist'))
            if sale_order:
                raise exceptions.Warning(_(
                    'This customer has a sale orders/quotations on '
                    'draft or open state. You can not change '
                    'pricelist'))

    @api.onchange('property_payment_term_id')
    def onchange_payment_term(self):
        if self.property_payment_term_id and self.customer:
            invoices = self.env[
                'account.invoice'].search(
                    [('partner_id', '=', self._origin.id),
                     ('state', 'in', ['draft', 'open'])], limit=1)
            sale_order = self.env[
                'sale.order'].search(
                    [('partner_id', '=', self._origin.id),
                     ('state', '!=', 'done')], limit=1)
            if invoices:
                raise exceptions.Warning(_(
                    'This customer has a invoices on '
                    'draft or open state. You can not change '
                    'payment term'))
            if sale_order:
                raise exceptions.Warning(_(
                    'This customer has a sale orders/quotations on '
                    'draft or open state. You can not change '
                    'pricelist'))

    @api.onchange('employee_code')
    def onchange_employe_code(self):
        if self.employee_code:
            employee_list = []
            actual_user = self.env.user
            other = actual_user.employee_ids
            for data in other:
                employee_list.append(data.id)
            code = self.env[
                'hr.employee'].search(
                    [('employee_code', '=', self.employee_code)], limit=1)
            if code.id in employee_list:
                self.employee_id = code.id
            else:
                raise exceptions.Warning(_(
                    'This employee code in not member of '
                    'this group.'))
        else:
            self.employee_id = False

    @api.model
    def _getemployee(self):
        # Domain for the employee
        employee_list = []
        actual_user = self.env.user
        other = actual_user.employee_ids
        for data in other:
            employee_list.append(data.id)
        return [('id', 'in', employee_list)]

    @api.onchange('type')
    def onchange_type_contact(self):
        if self.type != 'contact':
            self.contact_person = False

    @api.onchange('sale_warn', 'messages_id')
    def onchange_sale_messages(self):
        list_msg = []
        self.sale_warn_msg = ""
        if self.sale_warn in ['warning', 'block']:
            self.sale_warn_msg = ""
            if self.messages_id:
                for data in self.messages_id:
                    list_msg.append(data.name)
            self.sale_warn_msg = ' - '.join(list_msg)
        else:
            self.messages_id = False
            self.update({'sale_warn_msg': ""})

    @api.onchange('picking_warn', 'messages_picking_id')
    def onchange_picking_messages(self):
        list_msg = []
        self.picking_warn_msg = ""
        if self.picking_warn in ['warning', 'block']:
            self.picking_warn_msg = ""
            if self.messages_picking_id:
                for data in self.messages_picking_id:
                    list_msg.append(data.name)
            self.picking_warn_msg = ' - '.join(list_msg)
        else:
            self.messages_picking_id = False
            self.update({'picking_warn_msg': ""})

    @api.onchange('invoice_warn', 'messages_account_id')
    def onchange_account_messages(self):
        list_msg = []
        self.invoice_warn_msg = ""
        if self.invoice_warn in ['warning', 'block']:
            self.invoice_warn_msg = ""
            if self.messages_account_id:
                for data in self.messages_account_id:
                    list_msg.append(data.name)
            self.invoice_warn_msg = ' - '.join(list_msg)
        else:
            self.messages_account_id = False
            self.update({'invoice_warn_msg': ""})

    @api.onchange('start_day', 'end_day')
    def onchange_days(self):
        if self.end_day < self.start_day:
            raise exceptions.Warning(_('The end day can not be less than '
                                       'start day.'))
        if self.start_day > 31 or self.end_day > 31:
            raise exceptions.Warning(_('The days can not be greater than '
                                       '31.'))

    def _compute_is_administrative_assistant(self):
        for data in self:
            data.is_administrative_assistant = self.env.user.has_group(
                'con_profile.group_administrative_assistant')

    @api.constrains('sector_id', 'secondary_sector_ids')
    def _check_sectors(self):
        if self.sector_id in self.secondary_sector_ids:
            raise exceptions.Warning(_('The main sector must be different '
                                       'from the secondary sectors.'))

    def _compute_can_edit_doc_delivered(self):
        for data in self:
            data.can_edit_doc_delivered = self.env.user.has_group(
                'con_profile.group_commercial_director')

    def _compute_can_edit_pricelist(self):
        for data in self:
            data.can_edit_pricelist = self.env.user.has_group(
                'con_profile.group_commercial_director')

    @api.multi
    @api.depends('country_id')
    def _compute_product_pricelist(self):
        for p in self:
            if not isinstance(p.id, models.NewId):  # if not onchange
                p.property_product_pricelist = self.env[
                    'product.pricelist']._get_partner_pricelist(p.id)

    @api.model
    def create(self, values):
        values['partner_code'] = self.env[
            'ir.sequence'].next_by_code('res.partner.code')
        res = super(ResPartnerCode, self).create(values)
        pay_term = self.env.user.company_id.default_payment_term_id.id
        if pay_term:
            res.property_payment_term_id = pay_term
        else:
            raise exceptions.Warning(_(
                'You have to define a payment term in company config!'))
        return res

    @api.multi
    def write(self, values):
        # Overwrite sale order write
        values['employee_code'] = False
        res = super(ResPartnerCode, self).write(values)
        return res


class ResPartnerMessages(models.Model):
    _name = 'res.partner.messages'

    name = fields.Char('Message', translate=True)
