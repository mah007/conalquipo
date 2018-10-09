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

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    iso_logo = fields.Binary(string='Iso Logo')
    footer_logo = fields.Binary(string="Footer Logo")
    cover_page_logo = fields.Binary(string="Cover page Logo")
    account_extra_perm = fields.Many2many(
        'res.groups', string="Account extra permissions")
    default_payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Default customer payment terms")
    default_uom_task_id = fields.Many2many(
        'uom.uom',
        string="Default UOMs for products that don't generate tasks")
    default_validate_invoices = fields.Many2many(
        'res.users',
        string="Users can validate invoices")
    special_quotations_categories = fields.Many2many(
        'product.category',
        relation="special_quotations_company",
        string="Product categories for special quotations")
    billing_resolution = fields.Char(string='Billing Resolution')
    from_res = fields.Char(string='From')
    to_res = fields.Char(string='To')
    authorization_date = fields.Date('Date Authorization')
    invoice_note = fields.Text(string='Default Terms and Conditions Invoice')
