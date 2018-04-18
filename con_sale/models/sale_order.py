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

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, \
    DEFAULT_SERVER_DATETIME_FORMAT
import logging
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

    order_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')],
                                  string="Type", default="rent")
    purchase_ids = fields.One2many('purchase.order', 'sale_order_id',
                                   string='Purchase Orders')
    state = fields.Selection(selection_add=[
        ('merged', _('Merged')),
    ])
    sale_order_id = fields.Many2one('sale.order', 'Merged In')
    sale_order_ids = fields.One2many('sale.order', 'sale_order_id',
                                     string='Sale Orders related')
    project_id = fields.Many2one('project.project', string="Project")
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(string="Shipping",
                                   compute="_get_merge_address")
    invoice_address = fields.Text(string="Billing",
                                  compute="_get_merge_address")
    signs_ids = fields.Many2many(
        'signature.request',
        compute='_compute_sign_ids',
        string="Main signs")
    operators_services = fields.Integer(string="Operator Services")
    # Fleet
    carrier_type = fields.Selection(
        [('client', 'Client'), ('company', 'Company')],
        string='Carrier Responsible', default='client')
    vehicle = fields.Many2one(comodel_name='fleet.vehicle',
                              string='Vehicle', ondelete='cascade',
                              index=True, copy=False,
                              track_visibility='onchange')
    delivery_price = fields.Float(
        string='Estimated Delivery Price',
        readonly=False, copy=False)

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
        if self.order_line:
            operators = self.order_line.filtered(lambda line: line.add_operator)
            _logger.info("Operators %s" % operators)
            self.operators_services = len(operators)

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
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
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

    @api.multi
    def action_confirm(self):
        for purchase_id in self.purchase_ids:
            purchase_id.button_confirm()
        # ~ dl_ids: Deliveries Lines Ids
        dl_ids = self.env['sale.order.line'].search(
            [('delivery_direction', 'in', ['out']),
             ('picking_ids', '=', False),
             ('order_id', '=', self.id)])
        customer_location = self.env.ref('stock.stock_location_customers')
        for picking in self.picking_ids:
            if picking.state not in ['done', 'cancel'] and \
                    picking.location_dest_id.id == customer_location.id:
                dl_ids.update({'picking_ids': [(4, picking.id)]})

        if self.partner_id:
            order_id = self.search([('partner_id', '=', self.partner_id.id),
                                    ('state', '=', 'sale'),
                                    ('project_id', '=', self.project_id.id)
                                    ], limit=1)
            if order_id:
                for line in self.order_line:
                    line_copy = line.copy({'order_id': order_id.id})
                    order_id.write({'order_line': [(4, line_copy.id)]})
                self.update({'state': 'merged',
                             'sale_order_id': order_id.id,
                             'confirmation_date': fields.Datetime.now()
                             })
                if self.env.context.get('send_email'):
                    self.force_quotation_send()
                res = True
            else:
                res = super(SaleOrder, self).action_confirm()
        self._propagate_picking_project()
        self._get_components()
        self.function_add_picking_owner()
        return res

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
        res = super(SaleOrder, self).action_invoice_create(grouped, final)

        for inv in self.invoice_ids:
            for inv_ids in inv.invoice_line_ids:
                owner = self.function_product_subleased(inv_ids.product_id)
                _logger.info(owner)
                if owner:
                    inv_ids.write({'owner_id': owner.id})
                inv_ids.invoice_type = self.order_type
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
        if res.project_id:
            return res
        else:
            raise UserError(_('You need specify a work in this sale order'))
            
    @api.multi
    def write(self, values):
        # Overwrite sale order write
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
                lines = list()
                order_line = self.env['sale.order.line']
                del_ids = order_line.search(
                    [('order_id', '=', self._origin.id),
                     ('is_delivery', '=', True)])._ids
                link_ids = order_line.search(
                    [('order_id', '=', self._origin.id),
                     ('is_delivery', '!=', True)])
                # ~ Data Backup
                for new in link_ids:
                    lines.append({
                        'order_id': self._origin.id,
                        'name': new.name,
                        'product_uom_qty': new.product_uom_qty,
                        'product_uom': new.product_uom.id,
                        'product_id': new.product_id.id,
                        'price_unit': new.price_unit,
                        'tax_id': new.tax_id,
                        'is_delivery': False
                    })
                # ~ Deleted the records
                self.update({
                    'order_line': [(2, del_ids)],
                })
                # ~ link new records
                for new in lines:
                    self.update({'order_line': [(0, 0, new)]})
                self.write({'carrier_id': None})

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
                'product_uom': carrier.product_id.uom_id.id,
                'product_id': carrier.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
                'is_delivery': True,
                'delivery_direction': 'out' if x == 0 else 'in',
                'picking_ids': picking_ids,
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            self.update({'order_line': [(0, 0, values)]})
            if not receipt:
                break
        return True
        

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    READONLY_STATES_OWNER = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    start_date = fields.Date(string="Start")
    end_date = fields.Date(string="End")
    order_type = fields.Selection(related='order_id.order_type',
                                  string="Type Order")
    bill_uom = fields.Many2one('product.uom', string='Unit of Measure to Sale')
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
    service_operator = fields.Many2one('product.product',
                                       string='Service Operator',
                                       domain=[('sale_ok', '=', True),
                                               ('type', '=', 'service')],
                                       change_default=True, ondelete='restrict')
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
    picking_ids = fields.Many2many('stock.picking', 'order_line_picking_rel',
                                  'picking_id', 'sale_order_line_id',
                                   string="Pickings",
                                   help="Linked picking to the delivery cost")

    @api.one
    @api.constrains('start_date', 'end_date')
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
        self.bill_uom_qty = 1.0
        self.bill_uom = False
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
            self.bill_uom = self.product_uom.id
            self.bill_uom_qty = self.product_uom_qty
        if self.product_id.is_operated:
            self.mess_operated = True
        else:
            self.mess_operated = False
            self.add_operator = False
            self.service_operator = None
        self.components_ids = products_ids
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
        if values.get('service_operator'):
            new_line_operator = {
                'product_id': values['service_operator'],
                'name': 'Operator ' + '%s'%(
                    line.product_id.default_code or ''),
                'product_operate': values['product_id'],
                'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                'order_id': line.order_id.id,
                'parent_line': self.id,
                'bill_uom': line.product_id.product_tmpl_id.uom_id.id,
                'bill_uom_qty': line.product_uom_qty,
            }
            # ~ Create new record for operator
            self.create(new_line_operator)
        # Check owner
        if line.owner_id:
            self.function_management_buy(line)
        # Get min qty and uom of product
        product_muoms = line.product_id.product_tmpl_id.multiples_uom
        if product_muoms != True:
            line.price_unit = line.product_id.product_tmpl_id.list_price
            line.min_sale_qty = \
                self.product_id.product_tmpl_id.min_qty_rental             
        else:
            for uom_list in line.product_id.product_tmpl_id.uoms_ids:
                if line.bill_uom.id == uom_list.uom_id.id:
                    line.price_unit = uom_list.cost_byUom
                    line.min_sale_qty = uom_list.quantity      
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
                        component = self.search(
                            [('is_component', '=', True),
                             ('parent_component', '=', rec.product_id.id),
                             ('order_id', '=', rec.order_id.id),
                             ('product_id', '=', data.product_id.id)
                            ])
                        qty = data.quantity * rec.product_uom_qty
                        new_line = {
                            'product_id': data.product_id.id,
                            'name': 'Extra: ' + '%s'%(
                                rec.product_id.name),
                            'parent_component': rec.product_id.id,
                            'order_id': rec.order_id.id,
                            'product_uom_qty': qty,
                            'bill_uom_qty': qty,
                            'is_component': True,
                            'bill_uom': data.product_id.product_tmpl_id.uom_id.id
                        } 
                        component.write(new_line)
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

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'bill_uom_qty')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            quantity = 0.0
            if line.bill_uom_qty > 0:
                quantity = line.bill_uom_qty
            else:
                quantity = line.product_uom_qty

            price = line.price_unit * (
                1 - (line.discount or 0.0) / 100.0)

            taxes = line.tax_id.compute_all(
                price, line.order_id.currency_id, quantity,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id)
            line.update({
                'price_unit': price,
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice',
                 'qty_invoiced', 'bill_uom_qty')
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
                 'order_id.state', 'bill_uom_qty')
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

    @api.depends('price_total', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = line.price_total / line.bill_uom_qty\
                if line.bill_uom_qty else 0.0

    @api.depends('price_subtotal', 'product_uom_qty', 'bill_uom_qty')
    def _get_price_reduce_notax(self):
        for line in self:
            if line.bill_uom_qty:
                line.price_reduce_taxexcl =\
                    (line.price_subtotal / line.bill_uom_qty)
            else:
                line.price_reduce_taxexcl = 0.0

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty',
                  'tax_id', 'bill_uom_qty')
    def _onchange_discount(self):
        self.discount = 0.0
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
            return product.with_context(pricelist=self.order_id.pricelist_id.id
                                        ).price
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

    @api.onchange(
        'product_uom', 'product_uom_qty', 'bill_uom_qty')
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
        else:
            for uom_list in self.product_id.product_tmpl_id.uoms_ids:
                if self.bill_uom.id == uom_list.uom_id.id:
                    self.price_unit = uom_list.cost_byUom   
                    self.min_sale_qty = uom_list.quantity

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