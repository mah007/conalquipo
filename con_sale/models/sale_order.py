# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 (<http://www.ias.com.co>).
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
import time
from datetime import datetime, timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT, float_compare,
                        float_is_zero)

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_components(self):
        for pk in self.picking_ids:
            for ml in pk.move_lines:
                if ml.sale_line_id.components_ids:
                    ml.get_components_info()
        return True

    order_type = fields.Selection(
        [('rent', 'Rent'), ('sale', 'Sale')],
        string="Type", default="rent", track_visibility='onchange')
    purchase_ids = fields.One2many('purchase.order', 'sale_order_id',
                                   string='Purchase Orders')
    state = fields.Selection(selection_add=[
        ('merged', _('Merged')),
    ])
    sale_order_id = fields.Many2one('sale.order', 'Merged In')
    sale_order_ids = fields.One2many('sale.order', 'sale_order_id',
                                     string='Sale Orders related')
    project_id = fields.Many2one(
        'project.project', string="Project",
        track_visibility='onchange')
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(
        string="Shipping",
        compute="_get_merge_address",
        track_visibility='onchange')
    invoice_address = fields.Text(
        string="Billing",
        compute="_get_merge_address",
        track_visibility='onchange')
    signs_ids = fields.Many2many(
        'sign.request',
        compute='_compute_sign_ids',
        string="Main signs")
    operators_services = fields.Integer(
        string="Operator Services")
    carrier_type = fields.Selection(
        [('client', 'Client'),
         ('company', 'Company')],
        string='Carrier Responsible',
        default='client',
        track_visibility='onchange')
    vehicle = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Vehicle', ondelete='cascade',
        index=True, copy=False,
        track_visibility='onchange')
    delivery_price = fields.Float(
        string='Estimated Delivery Price',
        readonly=False, copy=False,
        track_visibility='onchange')
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task', ondelete='cascade',
        index=True, copy=False,
        track_visibility='onchange')
    product_count = fields.Integer(
        compute='_compute_product_count',
        string="Number of products on work",
        track_visibility='onchange')
    cancel_options = fields.Selection(
        [('no_vehicle_availability', 'No vehicle availability'),
         ('no_team_maintenance', 'There is no product for Maintenance'),
         ('no_operator', 'There is no operator'),
         ('no_stock', 'There is no stock'),
         ('hogh_prices', ' High prices'),
         ('i_got_it', 'I already got it'),
         ('not_need-it', 'He does not need it'),
         ('delay_response', 'Delay in response'),
         ('Other', 'Other')],
        string='Cancel reason')
    limit = fields.Float(
        'Credit limit', compute='_get_limit', store=True)
    available_amount = fields.Float(
        'Available amount', track_visibility='onchange')
    message_invoice = fields.Char(
        'Messages', track_visibility='onchange')
    message_invoice_inactive = fields.Boolean(
        'Message partner inactive')
    can_confirm = fields.Boolean('Can confirm')
    partner_inactive = fields.Boolean('Partner inactive')
    due_invoice_ids = fields.Many2many(
        "account.invoice", string='Related invoices',
        track_visibility='onchange')
    employee_id = fields.Many2one(
        "hr.employee", string='Employee',
        track_visibility='onchange',
        domain=lambda self: self.getemployee())
    employee_code = fields.Char('Employee code')
    approved_min_prices = fields.Boolean(
        'Approve min prices for products',
        default=True, track_visibility='onchange')
    approved_min_qty = fields.Boolean(
        'Approve min qty for products',
        default=True, track_visibility='onchange')
    approved_special_quotations = fields.Boolean(
        'Approve special quotations',
        default=True, track_visibility='onchange')
    approved_discount_modifications = fields.Boolean(
        'Approve discount modifications',
        default=True, track_visibility='onchange')
    amount_total_discount = fields.Monetary(
        string='Total discount',
        store=True, readonly=True,
        compute='_amount_all_discount',
        track_visibility='onchange')
    type_quotation = fields.Selection(
        [('special', 'Special'),
         ('no_special', 'No special')],
        string='Type of quotation',
        track_visibility='onchange')
    special_category = fields.Many2one(
        'product.category', 'Special category',
        track_visibility='onchange')
    template_id = fields.Many2one(
        'sale.order.template', 'Quotation Template',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        track_visibility='onchange')
    user_id = fields.Many2one(
        'hr.employee', string='Salesperson',
        index=True, track_visibility='onchange',
        default=lambda self: self.employee_id.id)
    payment_term_note = fields.Text(
        'Payment Terms and conditions')
    min_emptying = fields.Char('Min. Emptying')
    max_emptying = fields.Char('Max. Emptying')
    cap_emptying = fields.Char('Cap. Emptying')
    maximum_value_of_pipe = fields.Char('Maximun value of pipe')
    tip_load_capacity = fields.Char('Tip load capacity')
    useful_arm = fields.Char('Useful arm')
    maximum_load_capacity = fields.Char('Maximum load capacity')
    height = fields.Char('Height')
    speed = fields.Char('Vel.(m/min)')
    basket = fields.Char('Basket')
    towers = fields.Char('Towers')

    @api.multi
    def print_quotation2(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref(
            'con_sale.action_report_sale_con').report_action(self)

    @api.onchange('payment_term_id')
    def onchange_payment_term(self):
        if self.payment_term_id:
            self.payment_term_note = self.payment_term_id.note

    @api.onchange('type_quotation')
    def onchange_type_quotation(self):
        # Domain for the templates
        if self.type_quotation:
            self.special_category = False
            self.template_id = False
            cat_list = []
            cats = self.env.user.company_id.special_quotations_categories
            for data in cats:
                cat_list.append(data.id)
            return {'domain': {'special_category': [('id', 'in', cat_list)]}}

    @api.onchange('special_category')
    def get_templates(self):
        # Domain for the templates
        self.template_id = []
        cat_list = []
        cats = self.env.user.company_id.special_quotations_categories
        for data in cats:
            cat_list.append(data.id)
        if self.special_category:
            cat_list.remove(self.special_category.id)
        template = self.env[
            'sale.order.template'].search(
                [('special_category', 'not in', cat_list)])
        return {'domain': {'template_id': [('id', 'in', template._ids)]}}

    @api.depends('order_line.price_total')
    def _amount_all_discount(self):
        """
        Compute the total discounts of the SO.
        """
        for order in self:
            price_discount = 0.0
            price_unit = 0.0
            total_discounts = 0.0
            for line in order.order_line:
                quantity = line.bill_uom_qty * line.product_uom_qty
                price_unit += line.price_unit * quantity
                price_discount += line.price_subtotal
            total_discounts = price_unit - price_discount
            order.update({
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
    def getemployee(self):
        # Domain for the employee
        employee_list = []
        actual_user = self.env.user
        other = actual_user.employee_ids
        for data in other:
            employee_list.append(data.id)
        return [('id', 'in', employee_list)]

    @api.multi
    def approve_quotation(self):
        """
        Approve quotation
        """
        # Approve Small qty of products or prices
        actual_user = self.env.uid
        users_list = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                    'con_base.group_sale_small_qty').name]])
        if groups:
            for data in groups:
                for users in data.users:
                    users_list.append(users.id)
        if not self.approved_min_prices \
                and actual_user not in users_list:
            if self.order_line:
                raise UserError(_(
                    "You can't approve, small qty or prices!"
                ))
        else:
            self.approved_min_prices = True
            self.approved_min_qty = True
        # Approve special quotations
        users_list_sp_q = []
        groups_sp_q = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_sale_special_quotations').name]])
        if groups_sp_q:
            for data in groups_sp_q:
                for users in data.users:
                    users_list_sp_q.append(users.id)
        if not self.approved_special_quotations \
                and actual_user not in users_list_sp_q:
            if self.order_line:
                raise UserError(_(
                    "You can't approve special quotations!"
                ))
        else:
            self.approved_special_quotations = True
        # Approve discount modifications
        users_list_dm = []
        groups_dm = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_sale_discount_modifications').name]])
        if groups_dm:
            for data in groups_dm:
                for users in data.users:
                    users_list_dm.append(users.id)
        if not self.approved_discount_modifications \
                and actual_user not in users_list_dm:
            if self.order_line:
                raise UserError(_(
                    "You can't modify products discounts!"
                ))
        else:
            self.approved_discount_modifications = True

    @api.multi
    def check_limit(self):
        """
        Checks the limits
        """
        # Init data
        actual_user = self.env.user.id
        amount_residual = 0.0
        amount = 0.0
        msg = ''

        # Need products on sale lines validation
        self.ensure_one()
        if not self.order_line:
            raise UserError(_('You need to add products!'))
        else:
            if self.carrier_id and self.vehicle:
                carrier_lst = []
                for data in self.order_line:
                    if data.product_id.product_tmpl_id.for_shipping:
                        carrier_lst.append(data.id)
                if len(carrier_lst) == 0:
                    raise UserError(_(
                        'You need to add delivery method!'))

        # Users can confirm sales overlimit
        users_list = []
        users_list_active_partner = []
        groups_overlimit = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_sale_overlimit').name]])
        if groups_overlimit:
            for data in groups_overlimit:
                for users in data.users:
                    users_list.append(users.id)
        # users can active partners
        groups_acp = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_inactive_partners').name]])
        if groups_acp:
            for data in groups_acp:
                for users in data.users:
                    users_list_active_partner.append(users.id)
        # Invoices
        today_dt = datetime.now().strftime('%Y-%m-%d')
        invoice_obj = self.env['account.invoice']
        invoices = invoice_obj.search(
            [('partner_id', '=', self.partner_id.id),
             ('state', '=', 'open')])
        invoices_list = []
        self.due_invoice_ids = [(5,)]
        self.message_invoice = ''
        if users_list:
            if invoices:
                for data in invoices:
                    if not data.date_due:
                        preffix = data.sequence_number_next_prefix
                        pre_number = data.sequence_number_next
                        document = preffix + pre_number
                        raise UserError(_(
                            "The invoice %s don't have due date, check please!"
                        ) % document)
                    amount_residual += data.residual
                    due = datetime.strptime(data.date_due, '%Y-%m-%d')
                    today = datetime.strptime(today_dt, '%Y-%m-%d')
                    amount = self.partner_id.credit_limit - (
                        amount_residual + self.amount_total)
                    invoices_list.append((4, data.id))

                    if actual_user not in users_list and \
                            not self.partner_id.over_credit:
                        # Not credit define and due invoice
                        if self.partner_id.credit_limit == 0.0 and \
                                due < today:
                            msg = _("Has an expired bill!")
                            self.write({'message_invoice': msg,
                                        'due_invoice_ids': invoices_list,
                                        'can_confirm': False,
                                        'message_invoice_inactive': False,
                                        'available_amount': amount})

                        # Credit define and due invoice
                        elif self.partner_id.credit_limit > 0.0 and \
                                due < today and amount < -1:
                            msg = _("Exceeds limit and has expired invoice!")
                            self.write({'message_invoice': msg,
                                        'due_invoice_ids': invoices_list,
                                        'can_confirm': False,
                                        'message_invoice_inactive': False,
                                        'available_amount': amount})

                        # Credit define and not due invoice but pending
                        elif self.partner_id.credit_limit > 0.0 and \
                                due > today and amount < -1:
                            msg = _("Exceeds limit on outstanding invoices!")
                            self.write({'message_invoice': msg,
                                        'due_invoice_ids': invoices_list,
                                        'can_confirm': False,
                                        'message_invoice_inactive': False,
                                        'available_amount': amount})
                        # Invoice but pending and not exceeds
                        elif self.partner_id.credit_limit > 0.0 \
                                and due < today:
                            msg = _("Have outstanding invoices!")
                            self.write({'message_invoice': msg,
                                        'can_confirm': True,
                                        'message_invoice_inactive': False,
                                        'due_invoice_ids': invoices_list,
                                        'available_amount': amount})
            # Credit define and not invoice pending
            else:
                if self.partner_id.credit_limit != 0.0:
                    amount = self.partner_id.credit_limit - (
                        amount_residual + self.amount_total)
                    if amount < -1 and \
                            actual_user not in users_list and \
                            not self.partner_id.over_credit:
                        msg = _("Exceeds credit limit!")
                        self.write({'message_invoice': msg,
                                    'can_confirm': False,
                                    'message_invoice_inactive': False,
                                    'due_invoice_ids': [(5,)],
                                    'available_amount': amount})
            if self.partner_id.credit_limit == 0.0:
                msg = _("Without credit limit define!")
                self.write({
                    'can_confirm': True,
                    'available_amount': 0.0,
                    'message_invoice_inactive': False,
                    'due_invoice_ids': invoices_list,
                    'message_invoice': msg})
            if self.partner_id.over_credit:
                self.write({'can_confirm': True})
            # Check partner invoice activity
            if self.partner_inactive:
                if actual_user in users_list_active_partner:
                    self.write({'can_confirm': True})
                else:

                    self.write({
                        'can_confirm': False,
                        'partner_inactive': True,
                        'message_invoice_inactive': True})
            else:
                self.write({
                    'partner_inactive': False,
                    'can_confirm': True,
                    'message_invoice_inactive': False})
            return True

    @api.depends('partner_id')
    def _get_limit(self):
        """
        Show in sale order form the limit amount
        and get all invoices to check activity
        """
        for data in self:
            data.limit = data.partner_id.credit_limit

    @api.onchange('amount_total', 'partner_id')
    def change_can_confirm(self):
        """
        Show in sale order form the limit amount
        """
        self.update({'can_confirm': False,
                     'due_invoice_ids': [],
                     'message_invoice': '',
                     'available_amount': 0.0})

    def _compute_product_count(self):
        """
        Method to count the products on works
        """
        for record in self:
            product_qty_in = 0.0
            product_qty_out = 0.0
            picking = self.env[
                'stock.picking'].search(
                    [['partner_id', '=', record.partner_id.id],
                     ['location_dest_id.usage', 'in',
                      ['customer', 'internal']],
                     ['project_id', '=', record.project_id.id]])
            for data in picking:
                moves = self.env[
                    'stock.move'].search(
                        [['picking_id', '=', data.id],
                         ['location_dest_id',
                          '=',
                          data.location_dest_id.id],
                         ['state', '=', 'done']])
                if moves:
                    for p in moves:
                        if not p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'customer' and \
                           p.picking_id.location_id.usage \
                           == 'internal':
                            product_qty_in += p.product_uom_qty
                        if p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'internal' and \
                           p.picking_id.location_id.usage \
                           == 'customer':
                            product_qty_out += p.product_uom_qty
            record.product_count = product_qty_in - product_qty_out

    @api.multi
    @api.onchange('order_line')
    def order_line_change(self):
        """On Changed function on line orders.

          This function count the line that have a operator and update the
          field operators_service with a integer value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              None: Not return any value, only update the operator_service
              fields on sale order.

        """
        cat_lists = []
        product_eval_price = []
        product_eval_qty = []
        discount_eval = []
        list_note = []
        if self.order_line:
            operators = self.order_line.filtered(
                lambda line: line.add_operator)
            self.operators_services = len(operators)
            for data in self.order_line:
                # Get min qty and price of product
                product_muoms = data.product_id.product_tmpl_id.multiples_uom
                if not product_muoms:
                    if data.price_unit < \
                     data.product_id.product_tmpl_id.list_price:
                        product_eval_price.append(data.product_id.id)
                    if data.bill_uom_qty < \
                            data.product_id.product_tmpl_id.min_qty_rental:
                        product_eval_qty.append(data.product_id.id)
                else:
                    if not data.product_id.product_tmpl_id.uoms_ids:
                        raise UserError(_(
                            """You need to define product units, quantities """
                            """and prices values (Multiple values)"""))
                    for uom_list in data.product_id.product_tmpl_id.uoms_ids:
                        if data.bill_uom.id == uom_list.uom_id.id:
                            if data.price_unit < uom_list.cost_byUom:
                                product_eval_price.append(data.product_id.id)
                            if data.bill_uom_qty < uom_list.quantity:
                                product_eval_qty.append(data.product_id.id)
                # Approve to change discount
                if self.pricelist_id:
                    for datadisc in self.pricelist_id.item_ids:
                        if data.product_id.product_tmpl_id.id \
                                == datadisc.product_tmpl_id.id:
                            if data.discount < datadisc.percent_price or \
                                    data.discount > datadisc.percent_price:
                                discount_eval.append(data.product_id.id)
                        else:
                            if data.discount > 0.0:
                                discount_eval.append(data.product_id.id)
                # Get categories for special quotations
                cat_lists.append(data.product_id.product_tmpl_id.categ_id.id)
                # Get more information from products
                if data.product_id.product_tmpl_id.more_information:
                    list_note.append(
                        data.product_id.product_tmpl_id.more_information)
        if list_note:
            self.note = '\n \n '.join(list_note)
        cats = self.env.user.company_id.special_quotations_categories
        a = list(cats._ids)
        b = cat_lists
        inter = bool(set(a).intersection(b))
        if inter:
            self.approved_special_quotations = False
        else:
            self.approved_special_quotations = True
        # Min for qty and prices
        if product_eval_price:
            self.approved_min_prices = False
        else:
            self.approved_min_prices = True
        # Min for qty and prices
        if product_eval_qty:
            self.approved_min_qty = False
        else:
            self.approved_min_qty = True
        # Change discount
        if discount_eval:
            self.approved_discount_modifications = False
        else:
            self.approved_discount_modifications = True

    def _compute_sign_ids(self):
        """
        Get the products sign attachments
        """
        for data in self:
            signs_ids = self.env[
                'sign.request'].search([
                    ('sale_id', '=', data.id)]).ids
            data.signs_ids = list(
                set(signs_ids))

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.project_id = False
            # Check invoice activity
            invoice_obj = self.env['account.invoice']
            invoices = invoice_obj.search(
                [('partner_id', '=', self.partner_id.id)],
                order='id desc', limit=1)
            if invoices:
                for data in invoices:
                    if data.date_invoice:
                        today_year = datetime.now()
                        last_inv_date = datetime.strptime(
                            data.date_invoice, '%Y-%m-%d')
                        calc_days = today_year - last_inv_date
                        if calc_days.days >= 365:
                            self.partner_inactive = True
                        else:
                            self.partner_inactive = False
            else:
                self.partner_inactive = False

    @api.depends('project_id')
    def _get_merge_address(self):
        """
        This function verify if a project has been selected and return a
        merge address for shipping and invoice to the user.

        :return: None
        """
        for sale in self:
            if sale.project_id:
                p = sale.project_id
                sale.shipping_address = sale.merge_address(
                    p.street1 or '', p.street1_2 or '', p.city or '',
                    p.municipality_id.name or '', p.state_id.name or '',
                    p.zip or '', p.country_id.name or '', p.phone1 or '',
                    p.email or '')
                sale.invoice_address = sale.merge_address(
                    p.street2_1 or '', p.street2_2 or '', p.city2 or '',
                    p.municipality2_id.name or '', p.state2_id.name or '',
                    p.zip2 or '', p.country2_id.name or '', p.phone2 or '',
                    p.email or '')

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

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales
        order.
        This method may be overridden to implement custom invoice
        generation (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'project_id': self.project_id.id,
            'invoice_type': self.order_type
        })
        return invoice_vals

    @api.onchange('state')
    def onchange_state(self):
        for purchase_id in self.purchase_ids:
            if self.state in ['done', 'cancel']:
                purchase_id.write({'state': self.state})
            if self.state == 'sale':
                purchase_id.button_confirm()

    def _convert_qty_company_hours(self):
        company_time_uom_id = self.env.user.company_id.project_time_mode_id
        if self.product_uom.id != company_time_uom_id.id and \
                self.product_uom.category_id.id \
                == company_time_uom_id.category_id.id:
            planned_hours = self.product_uom._compute_quantity(
                self.product_uom_qty, company_time_uom_id)
        else:
            planned_hours = self.product_uom_qty
        return planned_hours

    @api.multi
    def action_confirm(self):
        if self.order_line:
            for pr in self.order_line:
                if not pr.bill_uom:
                    raise UserError(_(
                        "You need define a sale uom for product: %s"
                    ) % pr.product_id.name)
                if pr.bill_uom_qty <= 0.0:
                    raise UserError(_(
                        "You need specify a quantity for product: %s"
                    ) % pr.product_id.name)

        for purchase_id in self.purchase_ids:
            purchase_id.button_confirm()

        if self.partner_id:
            # If partner have documents
            attachment_ids = self.env[
                'ir.attachment'].search([
                    ('partner_id', '=', self.partner_id.id)])
            if not attachment_ids:
                raise UserError(_(
                    "You need to attach the client's validation documents"))
            if not self.partner_id.documents_delivered:
                raise UserError(_(
                    "The client has not delivered all the documents"))
            order_id = self.search([('partner_id', '=', self.partner_id.id),
                                    ('state', '=', 'sale'),
                                    ('project_id', '=', self.project_id.id)],
                                   limit=1)
            if order_id:
                cats = \
                 self.env.user.company_id.special_quotations_categories
                cat_lists = []
                inter = True
                for line in self.order_line:
                    # Quotations cant merge
                    cat_lists.append(
                        line.product_id.product_tmpl_id.categ_id.id)
                    a = list(cats._ids)
                    b = cat_lists
                    inter = bool(set(a).intersection(b))
                    if not inter:
                        line_copy = line.copy({'order_id': order_id.id})
                        order_id.write({'order_line': [(4, line_copy.id)]})
                if not inter:
                    self.update({'state': 'merged',
                                 'sale_order_id': order_id.id,
                                 'confirmation_date': fields.Datetime.now()})
                else:
                    self.update({
                        'state': 'sale',
                        'confirmation_date': fields.Datetime.now()})
                    # Create task for product
                    for data in self.order_line:
                        if data.bill_uom.id and data.bill_uom.id not in \
                            self.env.user.company_id.default_uom_task_id._ids \
                            and not \
                                data.is_delivery and not data.is_component \
                                and not data.task_id:
                            task_values = {
                                'name': "Task for: " +
                                str(self.project_id.name) +
                                " - " +
                                str(data.product_id.name) +
                                " - " +
                                str(data.bill_uom.name),
                                'project_id': self.project_id.id,
                                'sale_line_id': data.id,
                                'product_id': data.product_id.id,
                                'partner_id': self.partner_id.id,
                                'company_id': self.company_id.id,
                                'email_from': self.partner_id.email,
                                'user_id': False,
                                'uom_id': data.bill_uom.id,
                                'planned_hours': data.bill_uom_qty,
                                'remaining_hours': data.bill_uom_qty,
                            }
                            task = self.env[
                                'project.task'].create(task_values)
                            data.write({'task_id': task.id})
                    if self.env.context.get('send_email'):
                        self.force_quotation_send()
                res = True
            else:
                # Create task for product
                for data in self.order_line:
                    if data.bill_uom.id and data.bill_uom.id not in \
                     self.env.user.company_id.default_uom_task_id._ids \
                            and not \
                            data.is_delivery and not data.is_component \
                            and not data.task_id:
                        task_values = {
                            'name': "Task for: " +
                            str(self.project_id.name) +
                            " - " + str(data.product_id.name) +
                            " - " +
                            str(data.bill_uom.name),
                            'project_id': self.project_id.id,
                            'sale_line_id': data.id,
                            'product_id': data.product_id.id,
                            'partner_id': self.partner_id.id,
                            'company_id': self.company_id.id,
                            'email_from': self.partner_id.email,
                            'user_id': False,
                            'uom_id': data.bill_uom.id,
                            'planned_hours': data.bill_uom_qty,
                            'remaining_hours': data.bill_uom_qty,
                        }
                        task = self.env[
                            'project.task'].create(task_values)
                        data.write({'task_id': task.id})
                res = super(SaleOrder, self).action_confirm()
        self._propagate_picking_project()
        self._get_components()
        self.function_add_picking_owner()
        # Groups notifications for specific templates
        users = []
        mail_users = []
        body = _(
            'Attention: The order %s are created by %s with template: %s') % (
                self.name, self.create_uid.name, self.template_id.name)
        if self.template_id:
            groups = self.template_id.groups_ids
            for groupdata in groups:
                user_groups = groupdata.users
                for datausers in user_groups:
                    users.append(datausers.id)
                    mail_users.append(datausers.email)
            new_users = list(set(users))
            new_mail_users = list(set(mail_users))
            self.send_followers(body, new_users)
            self.send_to_channel(body, new_users)
            # Test smtp connection
            server = self.env['ir.mail_server'].sudo().search([])
            smtp = False
            for data in server:
                try:
                    smtp = data.connect(mail_server_id=data.id)
                except Exception as e:
                    pass
                else:
                    self.send_mail_wtemplate(body, new_mail_users)
            ###########################
        # FIXME: Put this code in a function and call here
        # ~ dl_ids: Deliveries Lines Ids
        dl_ids = self.env['sale.order.line'].search(
            [('delivery_direction', 'in', ['out']),
             ('picking_ids', '=', False),
             ('order_id', '=', self.id)])
        customer_location = self.env.ref('stock.stock_location_customers')
        if customer_location:
            for picking in self.picking_ids:
                if picking.state not in ['done', 'cancel'] and \
                        picking.location_dest_id.id == customer_location.id:
                    dl_ids.write({'picking_ids': [(4, picking.id)]})
        return res

    @api.multi
    def send_mail_wtemplate(self, body, recipients):
        mail_template = None
        if recipients:
            html_escape_table = {
                "&": "&amp;",
                '"': "&quot;",
                "'": "&apos;",
                ">": "&gt;",
                "<": "&lt;",
            }
            formated = "".join(
                html_escape_table.get(c, c) for c in recipients)
            # Mail template
            template = self.env.ref(
                'con_sale.create_order_email_template')
            if template:
                mail_template = self.env[
                    'mail.template'].browse(template.id)
            # senders
            uid = SUPERUSER_ID
            user_id = self.env[
                'res.users'].browse(uid)
            date = time.strftime('%d-%m-%Y')
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': body,
                'date': date,
            })
            # Send mail
            if mail_template:
                # Test smtp connection
                server = self.env['ir.mail_server'].sudo().search([])
                for data in server:
                    smtp = False
                    try:
                        smtp = data.connect(mail_server_id=data.id)
                    except Exception as e:
                        pass
                    else:
                        mail_template.with_context(ctx).send_mail(
                            self.id, force_send=True, raise_exception=True)
                ###########################

    @api.multi
    def _propagate_picking_project(self):
        """
        This function write the `project_id` of the `sale_order` on the Stock
        Picking Order.

        :return: True
        """
        for picking in self.picking_ids:
            picking.write({'project_id': self.project_id.id})
        return True

    @api.multi
    def function_add_picking_owner(self):
        # This function adds the owner of the product to the
        # corresponding line in the  output inventory movement

        for pk in self.picking_ids:
            for ml in pk.move_lines:
                owner = self.function_product_subleased(ml.product_id)
                for mvl in ml.move_line_ids:
                    if owner:
                        mvl.write({'owner_id': owner.id})

    @api.multi
    def function_product_subleased(self, product):
        # This function adds the owner of the product to the  corresponding
        #  line on the invoice.

        for line in self.order_line:
            if line.product_id == product and line.product_subleased:
                return line.owner_id
        return False

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(
            grouped, final)
        for data in self:
            for inv in data.invoice_ids:
                for inv_ids in inv.invoice_line_ids:
                    owner = data.function_product_subleased(
                        inv_ids.product_id)
                    if owner:
                        inv_ids.write({'owner_id': owner.id})
                    inv_ids.invoice_type = data.order_type
        return res

    @api.multi
    def action_advertisement(self):

        wizard_id = self.env['sale.order.advertisement.wizard'].create(
            {'partner_id': self.partner_id.id,
                  'project_id': self.project_id.id,
                  'sale_order_id': self.id,
                  'location_id': self.env.ref(
                      'stock.stock_location_customers').id})
        return {
            'name': 'Advertisement Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.advertisement.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_cancel_wizard(self):
        wizard_id = self.env['sale.order.cancel.wizard'].create(
            {'partner_id': self.partner_id.id,
             'project_id': self.project_id.id,
             'sale_order_id': self.id})
        return {
            'name': 'Cancellation Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.cancel.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def create(self, values):
        # Overwrite sale order create
        res = super(SaleOrder, self).create(values)
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_commercial_director').name]])
        # Send notification to users when works is created
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_commercial_director').name]])
        if groups:
            for data in groups:
                for users in data.users:
                    recipients.append(users.email)
        if recipients:
            body = _(
                'Attention: The order %s are created by %s') % (
                    res.name, res.create_uid.name)
            res.send_followers(body, recipients)
            res.send_to_channel(body, recipients)
            # Test smtp connection
            # server = self.env['ir.mail_server'].sudo().search([])
            # for data in server:
            #     smtp = False
            #     try:
            #         smtp = data.connect(mail_server_id=data.id)
            #     except Exception as e:
            #         pass
            #     else:
            #         res.send_mail(body)
            ###########################
            if res.project_id:
                return res
            else:
                raise UserError(_(
                    'You need specify a work in this sale order'))

    def send_followers(self, body, recipients):
        if recipients:
            self.message_post(body=body, type="notification",
                              subtype="mt_comment",
                              partner_ids=recipients)

    def send_to_channel(self, body, recipients):
        if recipients:
            ch_ob = self.env['mail.channel']
            ch = ch_ob.sudo().search([('name', 'ilike', 'general')])
            ch.message_post(attachment_id=[],
                            body=body, content_subtype="html",
                            message_type="comment", partner_ids=recipients,
                            subtype="mail.mt_comment")
            return True

    @api.multi
    def send_mail(self, body):
        # Recipients
        recipients = []
        mail_template = None
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_base.group_commercial_director').name]])
        if groups:
            for data in groups:
                for users in data.users:
                    recipients.append(users.email)
        else:
            return False
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        formated = "".join(
            html_escape_table.get(c, c) for c in recipients)
        if recipients:
            # Mail template
            template = self.env.ref(
                'con_sale.create_order_email_template')
            if template:
                mail_template = self.env[
                    'mail.template'].browse(template.id)
            # senders
            uid = SUPERUSER_ID
            user_id = self.env[
                'res.users'].browse(uid)
            date = time.strftime('%d-%m-%Y')
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': body,
                'date': date,
            })
            # Send mail
            if mail_template:
                # Test smtp connection
                server = self.env['ir.mail_server'].sudo().search([])
                for data in server:
                    smtp = False
                    try:
                        smtp = data.connect(mail_server_id=data.id)
                    except Exception as e:
                        pass
                    else:
                        mail_template.with_context(ctx).send_mail(
                            self.id, force_send=True, raise_exception=True)
                ###########################

    @api.multi
    def send_mail_sale_order_check(self):
        """
        Sale order checks mails
        """
        check_orders = self.search(
            [('state', 'in', ['draft', 'sent'])])
        val_activity = 0
        val_email = 0
        if check_orders:
            for data in check_orders:
                body = 'The order needs attention: ' + str(
                    data.name)
                # Values
                res_config_obj = self.env['res.config.settings']
                values = res_config_obj.search([])
                for vals in values:
                    val_activity = vals.days_activities
                    val_email = vals.days_expiration
                now = datetime.now()
                date_order = datetime.strptime(
                    data.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
                end_date_activity = (
                    now + timedelta(
                        days=val_activity))
                end_date_email = (
                    date_order + timedelta(
                        days=val_email))
                if date_order < end_date_activity and now != end_date_email:
                    # Create activity
                    activity_obj = self.env['mail.activity']
                    res_model_id = self.env['ir.model'].search(
                        [('model', '=', 'sale.order')],
                        limit=1)
                    activity_info = {
                        'res_id': data.id,
                        'res_model_id': res_model_id.id,
                        'res_model': 'sale.order',
                        'activity_type_id': 1,
                        'summary': body,
                        'res_name': data.name,
                        'note': '<p>The order needs attention<br></p>',
                        'date_deadline': end_date_activity
                    }
                    activity_obj.create(activity_info)
                # Send email notifications
                if now >= end_date_email:
                    # Test smtp connection
                    server = self.env['ir.mail_server'].sudo().search([])
                    for data in server:
                        smtp = False
                        try:
                            smtp = data.connect(mail_server_id=data.id)
                        except Exception as e:
                            pass
                        else:
                            self.send_mail(body)
                    ###########################

    @api.multi
    def write(self, values):
        # Overwrite sale order write
        values['employee_code'] = False
        res = super(SaleOrder, self).write(values)
        if 'project_id' in values and values['project_id'] is False:
            raise UserError(_(
                'You need specify a work in this sale order'))
        return res

    # Fleet
    @api.onchange('carrier_type')
    def onchange_carrier_type(self):
        """
        On changed method that allow adds automatically the cost product
        shipping to the order lines, and deleted the product when the shipping
        option is `Client`
        :return: None
        """
        if self.carrier_type == 'company' and self.project_id:
            delivery = self.env['delivery.carrier'].search(
                [('country_ids', '=',
                  self.project_id.country_id.id),
                 ('state_ids', '=',
                  self.project_id.state_id.id),
                 ('municipality_ids', '=',
                  self.project_id.municipality_id.id)],
                limit=1
                )
            self.update({
                'carrier_id': delivery,
            })
        else:
            if self.partner_id:
                self.update({'carrier_id': None, 'vehicle': None})

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        """
        Overloaded function that checks the if a carrier is seated and
        search all the vehicle linked to it and create a domain en polish
        notation.

        :return:
            Dict(str, Dict(str, list(tuple))): A Dictionary of dictionaries
            with domain values in polish notation list(tuple).
        """
        super(SaleOrder, self).onchange_carrier_id()
        domain = {}
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)])
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            domain = {'vehicle': [('id', 'in', veh_ids)]}
        return {'domain': domain}

    @api.onchange('vehicle')
    def onchange_vehicle_id(self):
        # Get vehicle price
        if self.vehicle:
            for data in self.carrier_id.delivery_carrier_cost:
                if self.vehicle.id == data.vehicle.id:
                    self.update({'delivery_price': data.cost})
                    self.delivery_price = data.cost

    @api.depends('carrier_id', 'order_line')
    def _compute_delivery_price(self):
        """
        Overloaded function that verify the order state for update the field
        delivery_price with the values of the carrier selected.

        :return: None
        """
        if self.vehicle:
            for order in self:
                if order.state != 'draft':
                    continue
                elif order.carrier_id.delivery_type != 'grid' and \
                        not order.order_line:
                    continue
                else:
                    veh_carrier = self.env['delivery.carrier.cost'].search(
                        [('vehicle', '=', order.vehicle.id),
                         ('delivery_carrier_id', '=', order.carrier_id.id)])
                    order.delivery_price = veh_carrier.cost
        else:
            super(SaleOrder, self)._compute_delivery_price()

    @api.multi
    def set_delivery_line(self):
        """
        Overloaded function that check is a vehicle is selected and create
        the delivery line on orders lines and set the delivery price on the
        order if not have a vehicle the function run a super over the function.

        :return: None
        """
        for rec in self:
            if rec.vehicle:
                veh_carrier = self.env['delivery.carrier.cost'].search(
                    [('vehicle', '=', rec.vehicle.id),
                     ('delivery_carrier_id', '=', rec.carrier_id.id)])
                rec._create_delivery_line(
                    rec.carrier_id, veh_carrier.cost, False, True)
                rec.delivery_price = veh_carrier.cost
            else:
                super(SaleOrder, self).set_delivery_line()

    def _create_delivery_line(self, carrier, price_unit, picking_ids=False,
                              receipt=False):
        """
        Overwrote function that create the line of the delivery on the sale
        order lines, this function have been modified for add the delivery
        output line and delivery input line by cargo cost.

        :param carrier: carrier's recordset.
        :param price_unit: price of the cargo.
        :param receipt: Flag parameter that receipt a boolean value False
         for only the output cargo and True for the output/input cargo.

        :return: boolean value.
        """
        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, carrier.product_id, self.partner_id).ids
        # Create the sales order line
        for x in range(2):
            values = {
                'order_id': self.id or self._origin.id,
                'name': '{} - {}'.format(
                    carrier.name, _('Delivery') if x == 0 else
                    _('Receive')),
                'product_uom_qty': 1,
                'bill_uom_qty': 1,
                'layout_category_id':
                carrier.product_id.product_tmpl_id.layout_sec_id.id,
                'product_uom': carrier.product_id.uom_id.id,
                'bill_uom': carrier.product_id.uom_id.id,
                'product_id': carrier.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
                'delivery_direction': 'out' if x == 0 else 'in',
                'picking_ids': picking_ids,
                'vehicle_id': self.vehicle.id,
                'carrier_id': carrier.id
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            self.update({'order_line': [(0, 0, values)]})
            if not receipt:
                break
        return True

    @api.onchange('template_id')
    def onchange_template_id(self):
        res = super(SaleOrder, self).onchange_template_id()
        self.order_lines = [(5, 0, 0)]
        self.note = ''
        template = self.template_id.with_context(lang=self.partner_id.lang)
        new_order_lines = []
        for line in template.sale_order_template_line_ids:
            discount = 0
            if self.pricelist_id:
                price = self.pricelist_id.with_context(
                    uom=line.product_uom_id.id).get_product_price(
                        line.product_id, 1, False)
                if self.pricelist_id.discount_policy == 'without_discount' \
                        and line.price_unit:
                    discount = (
                        line.price_unit - price) / line.price_unit * 100
                    price = line.price_unit
            else:
                price = line.price_unit
            data = {
                'name': line.name,
                'price_unit': price,
                'discount': 100 - ((100 - discount) * (
                    100 - line.discount)/100),
                'product_id': line.product_id.id,
                'layout_category_id': line.layout_category_id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom_id.id,
                'bill_uom_qty': line.bill_uom_qty,
                'bill_uom': line.bill_uom.id,
                'website_description': line.website_description,
                'state': 'draft',
                'customer_lead': self._get_customer_lead(
                    line.product_id.product_tmpl_id),
            }
            if self.pricelist_id:
                data.update(self.env['sale.order.line']._get_purchase_price(
                    self.pricelist_id, line.product_id,
                    line.product_uom_id, fields.Date.context_today(self)))
            new_order_lines.append((0, 0, data))
        self.order_line = new_order_lines
        self.order_line._compute_tax_id()

        if template.note:
            self.note = template.note
        return res
