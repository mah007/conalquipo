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
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    owner_id = fields.Many2one('res.partner', 'Owner')
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure of Sale')
    qty_shipped = fields.Float(
        'Quantity to be shipped',
        digits=dp.get_precision('Product Unit of Measure'))


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
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        compute="_get_sale_pricelist",
        help="Pricelist for current sales order.")
    amount_total_discount = fields.Monetary(
        string='Total discount',
        store=True, readonly=True,
        compute='_amount_all_discount',
        track_visibility='onchange')

    def _get_sale_pricelist(self):
        """
        This function get the default state configured on the product states
        models and return to the `product_template` model else return False

        :return: Recordset or False
        """
        for data in self:
            sale_ob = self.env['sale.order']
            sale_origin = sale_ob.search(
                [('name', '=', data.origin),
                 ('state', '=', 'sale')])
            data.pricelist_id = sale_origin.pricelist_id.id

    @api.depends('invoice_line_ids.price_subtotal')
    def _amount_all_discount(self):
        """
        Compute the total discounts of the SO.
        """
        for inv in self:
            sale_ob = self.env['sale.order']
            sale_origin = sale_ob.search(
                [('name', '=', inv.origin),
                 ('state', '=', 'sale')])
            cond = sale_origin.pricelist_id.item_ids
            for data in cond:
                if data.compute_price == 'on_total':
                    amount_total = 0.0
                    price_discount = 0.0
                    for line in inv.invoice_line_ids:
                        if line.product_id.product_tmpl_id.categ_id \
                         == data.categ_id:
                            quantity = line.quantity
                            amount_total += line.price_unit * quantity
                    price_discount = (
                        amount_total * data.percent_price_total) / 100
                    inv.update({
                        'amount_total_discount': price_discount})
                else:
                    price_discount = 0.0
                    price_unit = 0.0
                    total_discounts = 0.0
                    for line in inv.invoice_line_ids:
                        quantity = line.quantity
                        price_unit += line.price_unit * quantity
                        price_discount += line.price_subtotal
                    total_discounts = price_unit - price_discount
                    inv.update({
                        'amount_total_discount': total_discounts})

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

    @api.depends('project_id')
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
        street, street2, city, municipality, state, zip_code,
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
            'qty_shipped': qty,
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
            raise UserError(_(
                "You can't validate invoces. Check your permissions!"))
