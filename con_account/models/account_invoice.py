# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2018 IAS (<http://www.ias.com.co>).
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
from datetime import timedelta
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    document = fields.Char(
        string='Document')
    date_move = fields.Date(
        string='Date')
    date_init = fields.Integer(
        string='Date init')
    date_end = fields.Integer(
        string='Date end')
    num_days = fields.Integer(
        string='Number days')
    qty_remmisions = fields.Float(
        string='Qty remmisions')
    qty_returned = fields.Float(
        string='Qty returned')
    products_on_work = fields.Float(
        string='Products on work')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    project_id = fields.Many2one(
        'project.project', string="Work", track_visibility='onchange')
    invoice_type = fields.Selection(
        [('rent', 'Rent'),
         ('purchase', 'Purchase'),
         ('sale', 'Sale')],
        string="Type", default="sale", track_visibility='onchange')
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(
        string="Shipping address",
        compute="_get_merge_address")
    invoice_address = fields.Text(
        string="Billing address",
        compute="_get_merge_address")
    sector_id = fields.Many2one(
        comodel_name='res.partner.sector',
        string='Work Sector',
        track_visibility='onchange')
    secondary_sector_ids = fields.Many2one(
        comodel_name='res.partner.sector',
        string="Secondary work sectors",
        domain="[('parent_id', '=', sector_id)]",
        track_visibility='onchange')
    sector_id2 = fields.Many2one(
        comodel_name='res.partner.sector',
        string='Invoice Sector',
        track_visibility='onchange')
    secondary_sector_ids2 = fields.Many2one(
        comodel_name='res.partner.sector',
        string="Secondary invoice sectors",
        domain="[('parent_id', '=', sector_id2)]",
        track_visibility='onchange')
    days_delivery = fields.Char(
        string='Days delivery',
        track_visibility='onchange')
    employee_id = fields.Many2one(
        "hr.employee", string='Employee',
        track_visibility='onchange',
        domain=lambda self: self._getemployee())
    employee_code = fields.Char('Employee code')
    pre_invoice = fields.Boolean(
        string='Pre-Invoice?')
    init_date_invoice = fields.Date(
        string='Init Date')
    end_date_invoice = fields.Date(
        string='End Date')

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
                raise UserError(_(
                    'This employee code in not member of '
                    'this group.'))
        else:
            self.employee_id = False

    @api.onchange('partner_id')
    def onchange_project(self):
        self.project_id = False

    @api.model
    def _getemployee(self):
        # Domain for the employee
        employee_list = []
        actual_user = self.env.user
        other = actual_user.employee_ids
        for data in other:
            employee_list.append(data.id)
        return [('id', 'in', employee_list)]

    @api.model
    def create(self, values):
        # Overwrite invoice create
        res = super(AccountInvoice, self).create(values)
        if res.refund_invoice_id:
            # Propagate parent data to refund invoices
            parent_invoice = self.search
            inv_ob = self.env['account.invoice']
            parent_invoice = inv_ob.search(
                [('number', '=', res.origin)])
            res.project_id = parent_invoice.project_id.id
            res.payment_term_id = \
             parent_invoice.partner_id.property_payment_term_id.id
            res.sector_id = parent_invoice.sector_id.id
            res.secondary_sector_ids = \
             parent_invoice.secondary_sector_ids.id
            res.sector_id2 = parent_invoice.sector_id2.id
            res.secondary_sector_ids2 = \
             parent_invoice.secondary_sector_ids2.id
        if res.project_id:
            # Update sectors on invoices
            res.sector_id = res.project_id.sector_id.id
            res.secondary_sector_ids = \
             res.project_id.secondary_sector_ids.id
            res.sector_id2 = res.project_id.sector_id2.id
            res.secondary_sector_ids2 = \
             res.project_id.secondary_sector_ids2.id
        return res

    @api.multi
    def write(self, values):
        values['employee_code'] = False
        # Overwrite account invoice write
        res = super(AccountInvoice, self).write(values)
        # Account extra permissions
        groups_company = []
        users_in_acc_groups = []
        actual_user = self.env.user.id
        user_company = self.env['res.users'].browse([self._uid]).company_id
        for acc_groups in user_company.account_extra_perm:
            groups_company.append(acc_groups)
        for data in groups_company:
            for acc_users in data.users:
                users_in_acc_groups.append(acc_users.id)
        if actual_user in users_in_acc_groups:
            return res
        else:
            raise UserError(_(
                "You don't have permission to edit the record!"))

    @api.depends('project_id', 'partner_id')
    def _get_merge_address(self):
        """
        This function verify if a project has been selected and return a
        merge address for shipping and invoice to the user.

        :return: None
        """
        for acc in self:
            if acc.project_id:
                p = acc.project_id
                acc.shipping_address = acc.merge_address(
                    p.street1 or '', p.street1_2 or '', p.city or '',
                    p.municipality_id.name or '', p.state_id.name or '',
                    p.zip or '', p.country_id.name or '', p.phone1 or '',
                    p.email or '')
                acc.invoice_address = acc.merge_address(
                    p.street2_1 or '', p.street2_2 or '', p.city2 or '',
                    p.municipality2_id.name or '', p.state2_id.name or '',
                    p.zip2 or '', p.country2_id.name or '', p.phone2 or '',
                    p.email or '')
            acc.sector_id = acc.project_id.sector_id.id
            acc.secondary_sector_ids = acc.project_id.secondary_sector_ids.id
            acc.sector_id2 = acc.project_id.sector_id2.id
            acc.secondary_sector_ids2 = acc.project_id.secondary_sector_ids2.id

    @staticmethod
    def merge_address(
        street, street2, city,
        municipality, state, zip_code,
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
        :param email: the text for the email.
        :param phone: the text for the phone number.

        :return: merge string with all the givens parameters
        """
        values = [street, ', ', street2, ', ', city, ', ', municipality, ', ',
                  state, ',', zip_code, ', ', country, ', ', phone, ', ',
                  email]
        out_str = ''
        for num in range(len(values)):
            out_str += values[num]
        return out_str

    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0,
                         precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        quantity = 0.0
        if line.bill_uom_qty > 0:
            quantity = line.bill_uom_qty
        else:
            quantity = line.product_qty
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context(
                {'journal_id': self.journal_id.id,
                 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.compute(
                line.price_unit, self.currency_id, round=False),
            'quantity': quantity,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            'bill_uom': line.bill_uom.id,
        }
        self.invoice_type = line.order_id.order_type
        account = invoice_line.get_invoice_line_account(
            'in_invoice', line.product_id, line.order_id.fiscal_position_id,
            self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    @api.multi
    def action_invoice_open(self):
        # Overwrite action_invoice_open
        res = super(AccountInvoice, self).action_invoice_open()
        # Account extra permissions
        users_company = []
        users_in_acc_validate_groups = []
        actual_user = self.env.user.id
        user_company = self.env['res.users'].browse([self._uid]).company_id
        for acc_groups in user_company.default_validate_invoices:
            users_company.append(acc_groups)
        for data in users_company:
            users_in_acc_validate_groups.append(data.id)
        if actual_user in users_in_acc_validate_groups:
            return res
        else:
            # Can not validate zero amount invoices
            if self.amount_total == 0.0:
                raise UserError(_(
                    "You can't validate zero invoces. Check your permissions!"
                ))
            raise UserError(_(
                "You can't validate invoces. Check your permissions!"))

    @api.multi
    def _get_printed_report_name(self):
        self.ensure_one()
        return  \
            self.type == 'out_invoice' and not self.pre_invoice \
             and self.state == 'draft' and _('Draft Invoice') or \
            self.type == 'out_invoice' and self.pre_invoice and \
             self.state == 'draft' and _('Pre Invoice') or \
            self.type == 'out_invoice' and self.state in ('open', 'paid') \
             and _('Invoice - %s') % (self.number) or \
            self.type == 'out_refund' and self.state == 'draft' \
             and _('Credit Note') or \
            self.type == 'out_refund' and _('Credit Note - %s') % (
                self.number) or \
            self.type == 'in_invoice' and self.state == 'draft' \
             and _('Vendor Bill') or \
            self.type == 'in_invoice' and self.state in ('open', 'paid') \
             and _('Vendor Bill - %s') % (self.number) or \
            self.type == 'in_refund' and self.state == 'draft' \
             and _('Vendor Credit Note') or \
            self.type == 'in_refund' and _(
                'Vendor Credit Note - %s') % (self.number)

    @api.multi
    def write(self, values):
        res = super(AccountInvoice, self).write(values)
        date_end = None
        date_format = "%Y-%m-%d %S:%M:%S"
        if 'init_date_invoice' in values and self.invoice_type == "rent":
            for data in self.invoice_line_ids:
                for sale_lines in data.sale_line_ids:
                    move_out = self.env['stock.move'].search(
                        [('product_id', '=', data.product_id.id),
                         ('project_id', '=', self.project_id.id),
                         ('partner_id', '=', self.partner_id.id),
                         ('date_expected', '>=', self.init_date_invoice),
                         ('date_expected', '<=', self.end_date_invoice),
                         ('sale_line_id', '=', sale_lines.id)])
                    move_in = self.env['stock.move'].search(
                        [('product_id', '=', data.product_id.id),
                         ('project_id', '=', self.project_id.id),
                         ('partner_id', '=', self.partner_id.id),
                         ('advertisement_date', '>=', self.init_date_invoice),
                         ('advertisement_date', '<=', self.end_date_invoice),
                         ('sale_line_id', '=', sale_lines.id)])
                    for mv in move_in:
                        qty = 0.0
                        date_end = fields.Date.from_string(
                            mv.advertisement_date)
                        if mv.returned and \
                         mv.location_dest_id.return_location \
                          and mv.picking_id.state == 'done':
                            # Get delta days
                            a = fields.Date.from_string(
                                self.end_date_invoice)
                            b = fields.Date.from_string(
                                mv.advertisement_date)
                            delta = a - b
                            # Get tasks values
                            if not sale_lines.is_extra and \
                             not sale_lines.is_component and \
                              sale_lines.bill_uom.name not in \
                               ["Día(s)", "Unidad(es)"]:
                                task = self.env['project.task'].search(
                                    [('sale_line_id', '=', sale_lines.id)])
                                for timesheet in task.timesheet_ids:
                                    if timesheet.create_date >= \
                                     self.init_date_invoice and \
                                      timesheet.create_date <= \
                                       self.end_date_invoice:
                                        qty += timesheet.unit_amount
                            elif sale_lines.bill_uom.name == "Día(s)":
                                qty = delta.days + 1
                            else:
                                qty = mv.product_uom_qty
                            # Get product count history
                            history = self.env['stock.move.history'].search(
                                [('sale_line_id', '=', sale_lines.id),
                                 ('move_id', '=', mv.id),
                                 ('code', '=', 'incoming')])
                            # Create returned product invoice
                            inv_line = {"date_move": mv.advertisement_date,
                                 "invoice_id": data.invoice_id.id,
                                 "name": data.name,
                                 "account_id": data.account_id.id,
                                 "price_unit": data.price_unit,
                                 "document": "DEV" + '-' + \
                                  mv.picking_id.name,
                                 "origin": data.origin,
                                 "uom_id": data.uom_id.id,
                                 "product_id": data.product_id.id,
                                 "bill_uom": data.bill_uom.id,
                                 "discount": data.discount,
                                 "qty_returned": history.quantity_done,
                                 "date_init": fields.Date.from_string(
                                     mv.advertisement_date).day,
                                 "date_end": fields.Date.from_string(
                                     self.end_date_invoice).day,
                                 "num_days": delta.days + 1,
                                 "quantity": qty,
                                 "products_on_work": history.product_count,
                                 "invoice_line_tax_ids": \
                                  [(6, 0, list(
                                      data.invoice_line_tax_ids._ids))],
                                  "layout_category_id": \
                                      sale_lines.layout_category_id.id}
                            self.write({
                                'invoice_line_ids': [(0, 0, inv_line)]})

                    for mv in move_out:
                        qty = 0.0
                        if mv.location_dest_id.usage \
                         == 'customer' and mv.picking_id.state \
                          == 'done':
                            # Get delta days
                            if not date_end:
                                date_end = fields.Date.from_string(
                                    self.end_date_invoice)
                            a = fields.Date.from_string(mv.date_expected)
                            b = date_end
                            delta = b - a
                            # Get tasks values
                            if not sale_lines.is_extra and \
                             not sale_lines.is_component and \
                              sale_lines.bill_uom.name not in \
                               ["Día(s)", "Unidad(es)"]:
                                task = self.env['project.task'].search(
                                    [('sale_line_id', '=', sale_lines.id)])
                                for timesheet in task.timesheet_ids:
                                    if timesheet.create_date >= \
                                     self.init_date_invoice and \
                                      timesheet.create_date <= \
                                       self.end_date_invoice:
                                        qty += timesheet.unit_amount
                            elif sale_lines.bill_uom.name == "Día(s)":
                                qty = delta.days + 1
                            else:
                                qty = mv.product_uom_qty
                            # Get product count history
                            history = self.env[
                                'stock.move.history'].search(
                                    [('sale_line_id', '=', sale_lines.id),
                                     ('move_id', '=', mv.id),
                                     ('code', '=', 'outgoing')])
                            # Create product on work invoice
                            inv_line = {"date_move": mv.date_expected,
                                     "invoice_id": data.invoice_id.id,
                                     "name": data.name,
                                     "account_id": data.account_id.id,
                                     "price_unit": data.price_unit,
                                     "document": "REM" + '-' + \
                                        mv.picking_id.name,
                                     "origin": data.origin,
                                     "uom_id": data.uom_id.id,
                                     "product_id": data.product_id.id,
                                     "bill_uom": data.bill_uom.id,
                                     "discount": data.discount,
                                     "qty_remmisions": \
                                        history.quantity_done,
                                     "date_init": fields.Datetime.from_string(
                                         mv.date_expected).day,
                                     "date_end": date_end.day,
                                     "num_days": delta.days + 1,
                                     "quantity": qty,
                                     "products_on_work": \
                                        history.product_count,
                                     "invoice_line_tax_ids": \
                                        [(6, 0, list(
                                            data.invoice_line_tax_ids._ids))],
                                     "layout_category_id": \
                                      sale_lines.layout_category_id.id
                                    }
                            self.write({
                                'invoice_line_ids': [(0, 0, inv_line)]})

                # Unlink old invoices lines for product and consu
                if data.product_id.product_tmpl_id.type != "service":
                    data.unlink()
                else:
                    data.document = 'ACAR'
            self.compute_taxes()
        return res
