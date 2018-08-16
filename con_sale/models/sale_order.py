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
import time
from datetime import timedelta
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_components(self):
        for pk in self.picking_ids:
            for ml in pk.move_lines:
                if ml.sale_line_id.components_ids:
                    ml.get_components_info()
        return True

    def _get_default_template(self):
        template = self.env.ref(
            'website_quote.website_quote_template_default',
            raise_if_not_found=False)
        return template and template.active and template or False

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
        'signature.request',
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
        'Approve min and prices for products',
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
        'sale.quote.template', 'Quotation Template',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_get_default_template,
        track_visibility='onchange')
    user_id = fields.Many2one(
        'hr.employee', string='Salesperson',
        index=True, track_visibility='onchange',
        default=lambda self: self.employee_id.id)
    payment_term_note = fields.Text(
        'Payment Terms and conditions')

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
            return {'domain':{'special_category':[('id', 'in', cat_list)]}}

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
            'sale.quote.template'].search(
                [('special_category', 'not in', cat_list)])
        return {'domain':{'template_id':[('id', 'in', template._ids)]}}

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
                  'con_profile.group_sale_small_qty').name]])
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
        # Approve special quotations
        users_list_sp_q = []
        groups_sp_q = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_profile.group_sale_special_quotations').name]])
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
                      'con_profile.group_sale_discount_modifications').name]])
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
                      'con_profile.group_sale_overlimit').name]])
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
                      'con_profile.group_inactive_partners').name]])
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
                        elif self.partner_id.credit_limit > 0.0 and due < today:
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
        self.write({'can_confirm': False,
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
                     ['project_id', '=', record.project_id.id]
                    ])
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
        product_eval = []
        discount_eval = []
        list_note = []
        if self.order_line:
            operators = self.order_line.filtered(
                lambda line: line.add_operator)
            self.operators_services = len(operators)
            for data in self.order_line:
                # Get min qty and price of product
                product_muoms = data.product_id.product_tmpl_id.multiples_uom
                if product_muoms != True:
                    if data.price_unit < \
                     data.product_id.product_tmpl_id.list_price:
                        product_eval.append(data.product_id.id)
                    if data.bill_uom_qty < \
                     data.product_id.product_tmpl_id.min_qty_rental:
                        product_eval.append(data.product_id.id)
                else:
                    for uom_list in data.product_id.product_tmpl_id.uoms_ids:
                        if data.bill_uom.id == uom_list.uom_id.id:
                            if data.price_unit < uom_list.cost_byUom:
                                product_eval.append(data.product_id.id)
                            if data.bill_uom_qty < uom_list.quantity:
                                product_eval.append(data.product_id.id)
                # Approve to change discount
                if self.pricelist_id:
                    for datadisc in self.pricelist_id.item_ids:
                        if data.product_id.product_tmpl_id.id \
                        == datadisc.product_tmpl_id.id:
                            if data.discount < datadisc.percent_price or \
                            data.discount > datadisc.percent_price:
                                discount_eval.append(data.product_id.id)
                # Get categories for special quotations
                cat_lists.append(data.product_id.product_tmpl_id.categ_id.id)
                # Get more information from products
                if not data.product_id.product_tmpl_id.type == 'service' and\
                 data.product_id.product_tmpl_id.more_information:
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
        if product_eval:
            self.approved_min_prices = False
        else:
            self.approved_min_prices = True
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
                'signature.request'].search([
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
            'project_id': self.project_id.id
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
        self.product_uom.category_id.id == company_time_uom_id.category_id.id:
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
                    dl_ids.update({'picking_ids': [(4, picking.id)]})

        if self.partner_id:
            # If partner have documents
            attachment_ids = self.env[
                'ir.attachment'].search([
                    ('res_id', '=', self.partner_id.id),
                    ('res_model', '=', 'res.partner')])
            if not attachment_ids:
                raise UserError(_(
                    "You need to attach the client's validation documents"))
            if not self.partner_id.documents_delivered:
                raise UserError(_(
                    "The client has not delivered all the documents"))
            order_id = self.search([('partner_id', '=', self.partner_id.id),
                                    ('state', '=', 'sale'),
                                    ('project_id', '=', self.project_id.id)
                                   ], limit=1)
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
                                 'confirmation_date': fields.Datetime.now()
                                })
                else:
                    self.update({
                        'state': 'sale',
                        'confirmation_date': fields.Datetime.now()})
                    # Create task for product
                    for data in self.order_line:
                        if data.bill_uom.id in \
                        self.env.user.company_id.default_uom_task_id._ids \
                        and not \
                        data.is_delivery:
                            task_values = {
                                'name': "Task for: " \
                                + str(self.project_id.name) \
                                + " - " \
                                + str(data.product_id.name) \
                                + " - " + \
                                str(data.bill_uom.name),
                                'project_id': self.project_id.id,
                                'sale_line_id': data.id,
                                'so_line': data.id,
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
                    if data.bill_uom.id in \
                     self.env.user.company_id.default_uom_task_id._ids \
                     and not \
                       data.is_delivery:
                        task_values = {
                            'name': "Task for: " \
                             + str(self.project_id.name) \
                             + " - " \
                             + str(data.product_id.name) \
                             + " - " + \
                             str(data.bill_uom.name),
                            'project_id': self.project_id.id,
                            'sale_line_id': data.id,
                            'so_line': data.id,
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
            self.send_mail_wtemplate(body, new_mail_users)
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
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)

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
            vals={'partner_id': self.partner_id.id,
                  'project_id': self.project_id.id,
                  'sale_order_id': self.id,
                  'location_id': self.env.ref(
                      'stock.stock_location_customers').id,
                  })
        return {
            'name': 'Advertisement Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.advertisement.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def create(self, values):
        # Overwrite sale order create
        res = super(SaleOrder, self).create(values)
        # Send notification to users when works is created
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  self.env.ref(
                      'con_profile.group_commercial_director').name]])
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
            res.send_mail(body)
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
                      'con_profile.group_commercial_director').name]])
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
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)

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
                    self.send_mail(body)

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
                self.write({'carrier_id': None, 'vehicle': None})

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
                    self.write({'delivery_price': data.cost})
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
                'product_uom': carrier.product_id.uom_id.id,
                'bill_uom': carrier.product_id.uom_id.id,
                'product_id': carrier.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
                'delivery_direction': 'out' if x == 0 else 'in',
                'picking_ids': picking_ids,
                'vehicle_id': self.vehicle.id,
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
        if template.note:
            self.note = template.note
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    READONLY_STATES_OWNER = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _compute_uoms(self):
        # Compute availables uoms for product
        uom_list = []
        for data in self:
            uoms = data.product_id.product_tmpl_id.uoms_ids
            if data.product_id:
                if uoms:
                    for p in uoms:
                        uom_list.append(p.uom_id.id)
                    data.compute_uoms = uom_list
                else:
                    data.compute_uoms = \
                    [data.product_id.product_tmpl_id.sale_uom.id]

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order")
    bill_uom = fields.Many2one(
        'product.uom',
        string='Unit of Measure to Sale')
    compute_uoms = fields.Many2many(
        'product.uom',
        compute='_compute_uoms',
        store=False)
    owner_id = fields.Many2one('res.partner', string='Supplier',
                               states=READONLY_STATES_OWNER,
                               change_default=True, track_visibility='always')
    product_subleased = fields.Boolean(string="Subleased", default=False)
    bill_uom_qty = fields.Float('Quantity to Sale',
                                digits=dp.get_precision('Product Unit'
                                                        ' of Measure'))
    purchase_order_line = fields.One2many('purchase.order.line',
                                          'sale_order_line_id',
                                          string="Purchase Order Line",
                                          readonly=True, copy=False)
    stock_move_status = fields.Text(
        string="Stock move status", compute="_compute_move_status",
        store=True)
    # Components
    product_components = fields.Boolean('Have components?')
    product_uoms  = fields.Boolean('Multiple uoms?')
    is_component = fields.Boolean('Component')
    is_extra = fields.Boolean('Extra')
    parent_component = fields.Many2one(
        'product.product', 'Parent component')
    components_ids = fields.One2many(
        'sale.product.components', 'sale_line_id', string='Components')
    # Operators
    add_operator = fields.Boolean('Add Operator')
    mess_operated = fields.Boolean('Message Operated', default=False)
    product_operate = fields.Many2one('product.product',
                                      string='Product Operate',
                                      domain=[('sale_ok', '=', True),
                                              ('type', '=', 'service')],
                                      change_default=True, ondelete='restrict')
    assigned_operator = fields.Many2one(
        'res.users', string="Assigned Operator")
    parent_line = fields.Many2one(
        'sale.order.line', 'Parent line')
    min_sale_qty = fields.Float('Min QTY')
    # Fleet
    delivery_direction = fields.Selection([('in', 'collection'),
                                           ('out', 'delivery')],
                                          string="Delivery Type")
    picking_ids = fields.Many2many(
        'stock.picking', 'order_line_picking_rel',
        'picking_id', 'sale_order_line_id',
        string="Pickings",
        help="Linked picking to the delivery cost")
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string="Vehicle",
        help="Linked vehicle to the delivery cost")
    salesman_id = fields.Many2one(
        related='order_id.user_id',
        store=True,
        string='Salesperson',
        readonly=True)

    @api.multi
    def name_get(self):
        res = []
        if self._context.get('special_display', False):
            for rec in self:
                vehicle = "{} {}".format(rec.vehicle_id.model_id.name,
                                          rec.vehicle_id.license_plate)
                name = "{} - {} - {}".format(rec.name, rec.price_unit, vehicle)
                res.append((rec.id, name))
        else:
            res = super(SaleOrderLine, self).name_get()
        return res

    @api.one
    @api.constrains('start_date', 'end_date')
    def validate_dates(self):
        """
        Start date and end date validation
        """
        if self.end_date and self.start_date:
            date_format = '%Y-%m-%d'
            d1 = datetime.strptime(
                self.start_date, date_format
                ).date()
            d2 = datetime.strptime(
                self.end_date, date_format
                ).date()
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date")) 

    @api.onchange('start_date', 'end_date')
    def _check_dates(self):
        """
        Start date and end date validation
        """
        if self.end_date and self.start_date:
            date_format = '%Y-%m-%d'
            d1 = datetime.strptime(
                self.start_date, date_format
                ).date()
            d2 = datetime.strptime(
                self.end_date, date_format
                ).date()
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date")) 

    @api.onchange('assigned_operator')
    def assigned_operator_change(self):
        """On Changed function on assigned_operator that update the field
        when is change from the move_line linked to the picking order.

          Args:
              self (record): Encapsulate instance object.

          Returns:
              None: Not return any value, only update the operator_service
              fields on sale order.

        """
        if self.assigned_operator:
            self.mess_operated = False
            move = self.env['stock.move'].search(
                [('sale_line_id', '=', self.id)])
            for line in move.move_line_ids:
                line.write({'assigned_operator': self.assigned_operator})

    def _timesheet_create_task_prepare_values(self):
        """Overloaded function for preparate fields values to create the new
        task.

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the task information.

        """
        result = super(SaleOrderLine,
                       self)._timesheet_create_task_prepare_values()
        result.update({'product_id': self.product_operate.id})
        return result

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        """Overloaded on changed function for product_id.

          This overload check if the line have a componentes and update the
          field product_components with a boolean value:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: A dict with the product information.

        """
        result = super(SaleOrderLine, self).product_id_change()
        self.product_components = False
        self.product_uoms = False
        self.components_ids = [(5,)]
        self.uoms_ids = [(5,)]
        products_ids = []
        uoms_list = []
        components_ids = self.product_id.product_tmpl_id.components_ids
        uoms_ids = self.product_id.product_tmpl_id.uoms_ids
        if components_ids:
            self.product_components = True
            for p in components_ids:
                values = {}
                values['quantity'] = p.quantity
                values['product_id'] = p.product_child_id.id
                values['extra'] = False
                products_ids.append((0, 0, values))
        if uoms_ids:
            self.product_uoms = True
            for p in uoms_ids:
                uoms_list.append(p.uom_id.id)
            result['domain'] = {
                'bill_uom': [('id', 'in', uoms_list)]}
        else:
            self.bill_uom = self.product_id.product_tmpl_id.sale_uom.id
            self.bill_uom_qty = self.product_uom_qty
            result['domain'] = {
                'bill_uom': [
                    ('id',
                     'in',
                     [self.product_id.product_tmpl_id.sale_uom.id])]}
        if self.product_id.is_operated:
            self.mess_operated = True
        else:
            self.mess_operated = False
            self.add_operator = False
            self.service_operator = None
        self.components_ids = products_ids
        self.layout_category_id = \
        self.product_id.product_tmpl_id.layout_sec_id.id
        return result

    def _compute_move_status(self):
        """
        Get the products stock move status
        """
        for data in self:
            move = self.env[
                'stock.move'].search([
                    ('product_id', '=', data.product_id.id),
                    ('sale_line_id', '=', data.id)])
            for m in move:
                data.stock_move_status = m.state

    @api.onchange('owner_id')
    def onchange_owner_id(self):
        # This function changes to true or false the field product_subleased
        # depending on whether or not there is owner in the order line

        if self.owner_id:
            self.product_subleased = True
        else:
            self.product_subleased = False

    @api.multi
    def function_management_buy(self, line):
        # This function creates the purchase or rental orders associated with
        # this sale, if a purchase order already exists, the same supplier only
        # adds a line to this order otherwise it creates the complete order
        existing_purchase = False
        for purchase in line.order_id.purchase_ids:
            if purchase.partner_id.id == line.owner_id.id and \
             purchase.state == line.order_id.state:
                self.function_purchase_line_create(line, purchase)
                existing_purchase = True

        if not existing_purchase:
            po = self.function_purchase_create(line)
            self.function_purchase_line_create(line, po)
            line.order_id.write({'purchase_ids': [(4, po.id)]})

    @api.multi
    def function_purchase_create(self, line):
        # This function forms the purchase data and creates it
        # return: the new purchase
        purchase = {
            'partner_id': line.owner_id.id,
            'company_id': line.company_id.id,
            'currency_id':
                line.owner_id.property_purchase_currency_id.id or
                self.env.user.company_id.currency_id.id,
            'origin': line.order_id.name,
            'payment_term_id':
                line.owner_id.property_supplier_payment_term_id.id,
            'date_order': datetime.strptime(line.order_id.date_order,
                                            DEFAULT_SERVER_DATETIME_FORMAT),
            'fiscal_position_id': line.order_id.fiscal_position_id,
            'order_type': 'rent',
        }
        po = self.env['purchase.order'].create(purchase)
        return po

    @api.multi
    def function_purchase_line_create(self, line, purchase):
        # This function forms the data of the purchase line and creates it
        pol = self.env['purchase.order.line'].create({
            'name': line.product_id.name,
            'product_qty': line.product_uom_qty,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom.id,
            'price_unit': line.price_unit,
            'date_planned': datetime.strptime(
                line.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT),
            'taxes_id': [(6, 0, line.tax_id.ids)],
            'order_id': purchase.id,
            'bill_uom': line.bill_uom.id,
            'bill_uom_qty': line.bill_uom_qty,
            'sale_order_line_id': line.id
        })
        line.write({'purchase_order_line': [(4, pol.id)]})

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line
        for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        quantity = 0.0
        if self.bill_uom_qty > 0:
            quantity = self.bill_uom_qty
        else:
            quantity = res['quantity']

        res['bill_uom'] = self.bill_uom.id
        res['qty_shipped'] = self.product_uom_qty
        res['quantity'] = quantity
        return res

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    data = {
                        'out_invoice': lambda qty_invoice:
                        qty_invoice +
                        invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom,
                            rent=True),
                        'out_refund': lambda qty_invoiced:
                        qty_invoiced -
                        invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom,
                            rent=True)
                    }
                    qty_invoiced = data.get(invoice_line.invoice_id.type,
                                            lambda: 0)(qty_invoiced)
            line.qty_invoiced = qty_invoiced

    @api.model
    def create(self, values):
        # Overwrite sale order line create
        line = super(SaleOrderLine, self).create(values)
        # Check owner
        if line.owner_id:
            self.function_management_buy(line)
        # Create in lines extra products for components
        if line.components_ids:
            for data in line.components_ids:
                if data.extra:
                    qty = data.quantity * line.product_uom_qty
                    new_line_extra = {
                        'product_id': data.product_id.id,
                        'name': 'Extra ' + '%s' % (
                            line.product_id.default_code or ''),
                        'parent_component': line.product_id.id,
                        'parent_line': line.id,
                        'order_id': line.order_id.id,
                        'product_uom_qty': qty,
                        'bill_uom_qty': qty,
                        'owner_id': data.owner_id.id,
                        'is_extra': True,
                        'bill_uom': data.product_id.product_tmpl_id.uom_id.id
                    }
                    self.create(new_line_extra)
                else:
                    qty = data.quantity * line.product_uom_qty
                    new_line_components = {
                        'product_id': data.product_id.id,
                        'name': 'Comp ' + '%s' % (
                            line.product_id.default_code or ''),
                        'parent_component': line.product_id.id,
                        'parent_line': line.id,
                        'order_id': line.order_id.id,
                        'product_uom_qty': qty,
                        'bill_uom_qty': qty,
                        'price_unit': 0.0,
                        'owner_id': data.owner_id.id,
                        'is_component': True,
                        'bill_uom': data.product_id.product_tmpl_id.uom_id.id
                    }
                    self.create(new_line_components)
        # Dates validations
        if line.end_date and line.start_date:
            date_format = '%Y-%m-%d'
            d1 = datetime.strptime(
                line.start_date, date_format
                ).date()
            d2 = datetime.strptime(
                line.end_date, date_format
                ).date()
            if d2 < d1:
                raise UserError(
                    _("The end date can't be less than start date"))
        # Fleet
        if line.is_delivery:
            line.update({
                'price_unit': line.order_id.delivery_price})
        if line.is_component:
            line.update({
                'price_unit': 0.0})
        return line

    @api.multi
    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        for rec in self:
            if values.get('owner_id') and not rec.purchase_order_line:
                rec.function_management_buy(rec)
            if rec.purchase_order_line and values.get('product_uom_qty'):
                values['product_qty'] = values.get('product_uom_qty')
                rec.purchase_order_line.write(values)
            # Write lines extra products for componentes
            if rec.components_ids:
                for data in rec.components_ids:
                    if data.extra:
                        component = self.env['sale.order.line'].search(
                            [('is_component', '=', True),
                             ('parent_component', '=', rec.product_id.id),
                             ('order_id', '=', rec.order_id.id),
                             ('product_id', '=', data.product_id.id)
                            ])
                        qty = data.quantity * rec.product_uom_qty
                        new_line_component = {
                            'product_id': data.product_id.id,
                            'name': 'Component ' + '%s'%(
                                rec.product_id.name),
                            'parent_component': rec.product_id.id,
                            'order_id': rec.order_id.id,
                            'product_uom_qty': qty,
                            'bill_uom_qty': qty,
                            'is_component': True,
                            'bill_uom':\
                                data.product_id.product_tmpl_id.uom_id.id
                        }
                        component.write(new_line_component)
                    else:
                        extra = self.env['sale.order.line'].search(
                            [('is_extra', '=', True),
                             ('parent_component', '=', rec.product_id.id),
                             ('order_id', '=', rec.order_id.id),
                             ('product_id', '=', data.product_id.id)
                            ])
                        qty = data.quantity * rec.product_uom_qty
                        new_line_extra = {
                            'product_id': data.product_id.id,
                            'name': 'Extra ' + '%s'%(
                                rec.product_id.name),
                            'parent_component': rec.product_id.id,
                            'order_id': rec.order_id.id,
                            'product_uom_qty': qty,
                            'bill_uom_qty': qty,
                            'is_extra': True,
                            'bill_uom':\
                                data.product_id.product_tmpl_id.uom_id.id
                        }
                        extra.write(new_line_extra)
            # Dates validations
            if rec.end_date and rec.start_date:
                date_format = '%Y-%m-%d'
                d1 = datetime.strptime(
                    rec.start_date, date_format
                    ).date()
                d2 = datetime.strptime(
                    rec.end_date, date_format
                    ).date()
                if d2 < d1:
                    raise UserError(
                        _("The end date can't be less than start date"))
        return res

    @api.depends('discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            quantity = line.bill_uom_qty * line.product_uom_qty
            if quantity == 0.0 or False:
                line.update({
                    'bill_uom_qty': 1,
                    'product_uom_qty': 1
                })
            price = line.price_unit
            price_discount = line.price_unit * (
                1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price_discount, line.order_id.currency_id, quantity,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id)
            line.update({
                'price_unit': price,
                'price_tax': sum(
                    t.get(
                        'amount', 0.0) for t in taxes.get(
                            'taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice',
                 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that
        there is nothing to invoice. This is also hte default value if the
        conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to
        metho _get_to_invoice_qty()` for more information on how this quantity
        is calculated.
        - upselling: this is possible only for a product invoiced on ordered
        quantities for which we delivered more than expected. The could arise
        if, for example, a project took more time than expected but we decided
        not to invoice the extra cost to the client. This occurs onyl in state
        'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity
        ordered.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice,
                                   precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' \
                    and line.product_id.invoice_policy == 'order' \
                    and float_compare(line.qty_delivered,
                                      line.product_uom_qty,
                                      precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty,
                               precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty',
                 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the
        quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            qty = 0.0
            if line.bill_uom_qty > 0:
                qty = line.bill_uom_qty
            else:
                qty = line.product_uom_qty

            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = \
                        (line.qty_delivered - line.qty_invoiced)
            else:
                line.qty_to_invoice = 0

    @api.depends('price_total', 'bill_uom_qty', 'product_uom_qty')
    def _get_price_reduce_tax(self):
        data = 1.0
        for line in self:
            if not line.bill_uom_qty > 0.0:
                line.bill_uom_qty = data
            else:
                data = line.bill_uom_qty
            line.price_reduce_taxinc = \
                line.price_total / data

    @api.depends('price_subtotal', 'bill_uom_qty', 'product_uom_qty')
    def _get_price_reduce_notax(self):
        data = 1.0
        for line in self:
            if line.bill_uom_qty:
                if not line.bill_uom_qty > 0.0:
                    line.bill_uom_qty = data
                else:
                    data = line.bill_uom_qty
                line.price_reduce_taxexcl = \
                    line.price_subtotal / data
            else:
                line.price_reduce_taxexcl = 0.0

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
                  'tax_id', 'bill_uom_qty')
    def _onchange_discount(self):
        discount_policy = self.order_id.pricelist_id.discount_policy
        res_group = self.env.user.has_group('sale.group_discount_per_so_line')
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                discount_policy == 'without_discount' and res_group):
            return

        context_partner = dict(self.env.context,
                               partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order)
        pricelist_context = dict(context_partner, uom=self.product_uom.id)
        qty = 0.0
        if self.bill_uom_qty > 0:
            qty = self.bill_uom_qty
        else:
            qty = self.product_uom_qty
        price, rule_id = self.order_id.pricelist_id.with_context(
            pricelist_context).get_product_price_rule(self.product_id,
                                                      qty or 1.0,
                                                      self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(
            context_partner)._get_real_price_currency(
                self.product_id, rule_id, qty, self.product_uom,
                self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price,
                # which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(
                    currency_id).with_context(context_partner).compute(
                    new_list_price, self.order_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(
                pricelist=self.order_id.pricelist_id.id).price
        final_price, rule_id = \
            self.order_id.pricelist_id.get_product_price_rule(
                self.product_id, self.bill_uom_qty or 1.0,
                self.order_id.partner_id)
        context_partner = dict(self.env.context,
                               partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order)
        base_price, currency_id = self.with_context(
            context_partner)._get_real_price_currency(
            self.product_id, rule_id, self.bill_uom_qty, self.product_uom,
            self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(
                currency_id).with_context(context_partner).compute(
                base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_uom')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),
                bill_uom_qty=self.bill_uom_qty,
                bill_uom=self.bill_uom,
                owner_id=self.owner_id,
                start_date=self.start_date,
                end_date=self.end_date,
                product_subleased=self.product_subleased,
            )
            self.price_unit = self.env[
                'account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id,
                self.tax_id, self.company_id)

    @api.onchange('bill_uom')
    def price_bill_qty(self):
        """
        Get price for specific uom of product
        """
        product_muoms = self.product_id.product_tmpl_id.multiples_uom
        if product_muoms != True:
            self.price_unit = self.product_id.product_tmpl_id.list_price
            self.min_sale_qty = \
                self.product_id.product_tmpl_id.min_qty_rental
            self.bill_uom_qty = \
                self.product_id.product_tmpl_id.min_qty_rental
        else:
            for uom_list in self.product_id.product_tmpl_id.uoms_ids:
                if self.bill_uom.id == uom_list.uom_id.id:
                    self.price_unit = uom_list.cost_byUom
                    self.min_sale_qty = uom_list.quantity
                    self.bill_uom_qty = uom_list.quantity

    @api.multi
    def _action_launch_procurement_rule(self):
        res = super(SaleOrderLine, self)._action_launch_procurement_rule()
        self._propagate_picking_project()
        return res

    @api.multi
    def _propagate_picking_project(self):
        """
        This function write the `project_id` of the `sale_order` on the Stock
        Picking Order.

        :return: True
        """
        for order in self.mapped('order_id'):
            for picking in order.picking_ids:
                picking.write({'project_id': order.project_id.id})
        return True


class SaleProductComponents(models.Model):
    _name = "sale.product.components"
    _description = "A model for store and manage the products components"
    rec_name = "product_id"

    sale_line_id = fields.Many2one(
        'sale.order.line', string="Sale line")
    product_id = fields.Many2one(
        'product.product', string="Product component")
    quantity = fields.Integer('Default quantity', default=1)
    extra = fields.Boolean('Extra product')
    owner_id = fields.Many2one(
        'res.partner', string='Supplier',
        change_default=True, track_visibility='always')
