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
import logging
_logger = logging.getLogger(__name__)
from odoo.models import Model, api, _
from odoo import fields, SUPERUSER_ID
from odoo.exceptions import UserError


class StockPicking(Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one(
        'project.project', string="Project", track_visibility='onchange')
    employee_id = fields.Many2one(
        "hr.employee", string='Employee',
        track_visibility='onchange',
        domain=lambda self:self._getemployee())
    attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_attachment_ids',
        string="Main Attachments", track_visibility='onchange')
    # ~Fields for shipping and invoice address
    shipping_address = fields.Text(
        string="Shipping",
        compute="_get_merge_address", track_visibility='onchange')
    invoice_address = fields.Text(
        string="Billing",
        compute="_get_merge_address", track_visibility='onchange')
    repair_requests = fields.Boolean(string='Repair request')
    mess_operated = fields.Boolean('Message Operated', default=False)
    reason = fields.Selection([
        ('0', 'End project-work'),
        ('2', 'Change Because of Malfunction'),
        ('1', 'It seems very expensive'),
        ('3', 'Bad attention'),
        ('2', 'The equipment did not serve you'),
        ('0', 'No longer need it'),
    ], string="Reason", track_visibility='onchange')
    type_sp = fields.Integer(
        related='picking_type_id.id',
        store=True, track_visibility='onchange')
    carrier_type = fields.Selection(
        related='sale_id.carrier_type',
        store=True, track_visibility='onchange')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle',
        related='sale_id.vehicle',
        onchange='onchange_vehicle_id',
        track_visibility='onchange', store=True)
    license_plate = fields.Char(
        related='vehicle_id.license_plate',
        string='License Plate',
        store=True, track_visibility='onchange')
    driver_client = fields.Char(
        string='Driver', track_visibility='onchange')
    id_driver_client = fields.Char(
        string='Identification No Driver',
        store=True, track_visibility='onchange')
    driver_ids = fields.One2many(
        'shipping.driver',
        'stock_picking_id',
        string='Shipping Driver',
        copy=True, track_visibility='onchange')
    vehicle_client = fields.Char(
        string='Vehicle', track_visibility='onchange')
    in_hour = fields.Float(
        string='Hour Entry', track_visibility='onchange')
    out_hour = fields.Float(
        string='Hour Output', track_visibility='onchange')
    receipts_driver_ids = fields.One2many(
        'shipping.driver', 'stock_picking_id',
        string='Shipping Driver',
        copy=True)
    responsible = fields.Char(
        string='Responsible',
        track_visibility='onchange')
    id_number = fields.Char(
        string='Person identification',
        track_visibility='onchange')
    job_title = fields.Char(
        string='Job title', track_visibility='onchange')
    carrier_tracking_ref = fields.Char(
        string='Tracking Reference',
        compute='_carrier_tracking_ref')
    cancel_reason = fields.Text(
        strin="Cancel Reason",
        track_visibility='onchange')
    delivery_cost = fields.Many2many(
        'sale.order.line',
        'order_line_picking_rel',
        'sale_order_line_id', 'picking_id',
        string="Delivery Cost", track_visibility='onchange')

    @api.model
    def _getemployee(self):
        # Domain for the employee
        employee_list = []
        actual_user = self.env.user
        other = actual_user.employee_ids
        for data in other:
            employee_list.append(data.id)
        return [('id', 'in', employee_list)]

    @api.multi
    def _product_availibility_on_project(self, partner_id=False,
                                         project_id=False,
                                         product_id=False):

        if not any([product_id, partner_id, project_id]): return False

        def sum_reduce(object=False):
            if not object: return 0
            return sum([x.quantity_done for x in object])

        self.ensure_one()

        out_pickings = self.env['stock.picking'].search(
            [('partner_id', '=', partner_id),
             ('project_id', '=', project_id),
             ('state', '=', 'done'),
             ('location_dest_id', '=', self.env.ref(
                 'stock.stock_location_customers').id)])

        in_pickings = self.env['stock.picking'].search(
            [('partner_id', '=', partner_id),
             ('project_id', '=', project_id),
             ('state', '=', 'done'),
             ('location_id', '=', self.env.ref(
                 'stock.stock_location_customers').id)])
        out_moves = self.env['stock.move'].search(
            [('product_id', '=', product_id), ('state', '=', 'done'),
             ('location_dest_id', '=', self.env.ref(
                 'stock.stock_location_customers').id),
             ('picking_id', 'in', out_pickings._ids)]) or False

        in_moves = self.env['stock.move'].search(
            [('product_id', '=', product_id), ('state', '=', 'done'),
             ('location_id', '=', self.env.ref(
                 'stock.stock_location_customers').id),
             ('picking_id', 'in', in_pickings._ids)]) or False
        in_qty = sum_reduce(in_moves)
        out_qty = sum_reduce(out_moves)
        return out_qty - in_qty

    @api.multi
    def action_equipment_change(self):
        line = []
        for ml in self.move_lines:
            line.append((0, 0, {
                'ant_product_id': ml.product_id.id,
                'move_line': ml.id}))

        wizard_id = self.env['stock.picking.equipment.change.wizard'].create(
            vals={'picking_id': self.id,
                  'product_ids': line})
        return {
            'name': 'Equipment Change Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking.equipment.change.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('carrier_type')
    def onchange_carrier_type(self):
        """
        Wipe the values in the following fields:
        carrier_id and vehicle_id are False if carrier_type is 'client'
        vehicle_client and driver client are '' if carrier type is different
        to client.
        :return: None
        """
        if self.carrier_type == 'client':
            self.carrier_id = False
            self.vehicle_id = False
        else:
            self.vehicle_client = ''
            self.driver_client = ''

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """
        Check the vehicles available for the carrier selected and return
        a exception if the same is not available in that zone
        :return: a empty dictionary if process is ok and warning if have a
        exception
        """
        res = {}
        if not self.vehicle_id or not self.carrier_id:
            return res
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)], limit=10)
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            if self.vehicle_id.id not in veh_ids:
                self.vehicle_id = self.vehicle_id.id
                res['warning'] = {'title': _('Warning'), 'message': _(
                    'Selected vehicle is not available for the shipping '
                    'area. please select another vehicle.')}
                self.vehicle_id = self.vehicle_id.id
            else:
                return res
        return res

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        """
        Search all vehicle available for a carrier and send the dynamic
        domain to the field vehicle_id.
        :return: A dictionary with a domain in polish notation
        """
        domain = {}
        if self.carrier_id:
            veh_carrier = self.env['delivery.carrier.cost'].search(
                [('delivery_carrier_id', '=', self.carrier_id.id)], limit=10)
            veh_ids = []
            for veh in veh_carrier:
                veh_ids.append(veh.vehicle.id)
            vehicle = self.env['fleet.vehicle'].search(
                [('id', 'in', veh_ids)], limit=10)
            domain = {'vehicle_id': [('id', 'in', vehicle.ids)]}
        return {'domain': domain}

    @api.one
    @api.depends('scheduled_date', 'carrier_id', 'vehicle_id',
                 'vehicle_client')
    def _carrier_tracking_ref(self):
        """
        This function merge the following fields in a simple string,
        for create a tracking code:
            scheduled_date : date
            carrier_id: int
            vehicle_id.license_plate: int
            location_id.location_id.name: str
        :return: a joined string tracker code
        """
        if self.carrier_id:
            ref = [str(self.scheduled_date), str(self.carrier_id.id),
                   str(self.vehicle_id.license_plate or ''),
                   str(self.location_id.location_id.name or '')]
        else:
            ref = [str(self.scheduled_date), str(self.vehicle_client or ''),
                   self.location_id.location_id.name or '']
        self.carrier_tracking_ref = str("".join(ref)).replace("-", "").\
            replace(" ", "").replace(":", "")

    @api.multi
    def action_cancel(self):
        if self._context.get('wizard_cancel'):
            wizard_id = self.env['stock.picking.cancel.wizard'].create(
                vals={'picking_ids': [(4, self._ids)]})

            return {
                'name': 'Cancellation Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking.cancel.wizard',
                'res_id': wizard_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        else:
            return self.action_do_cancel()

    @api.multi
    def action_do_cancel(self):
        self.mapped('move_lines')._action_cancel()
        self.write({'is_locked': True})
        return True

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
                if move.sale_line_id.add_operator and not move.employee_id \
                   and move.picking_id.location_dest_id.usage \
                   == 'customer':
                    raise UserError(
                        _('You need specify a operator for: %s'
                         ) % move.sale_line_id.product_id.name)
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

    @api.multi
    def send_mail_notification_diary(self):
        """
        Stock mail diary notifications
        """
        # senders
        uid = SUPERUSER_ID
        user_id = self.env[
            'res.users'].browse(uid)
        # Recipients
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  'Can receive stock notifications email diary']])
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
        # Stock move objects
        move_line_ids = self.env[
            'stock.move'].search(
                [['date', '>=', time.strftime('%Y-%m-%d 00:00:00')],
                 ['date', '<=', time.strftime('%Y-%m-%d 23:59:59')],
                 ['state', '=', 'done']])
        # Generate data for template
        products_lst = []
        move_in = []
        move_out = []
        for data in move_line_ids:
            if data.sale_line_id:
                products_lst.append(data.product_id)
            if not data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'customer' and \
                data.picking_id.location_id.usage \
                == 'internal':
                move_in.append(data)
            if data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'internal' and \
                data.picking_id.location_id.usage \
                == 'customer':
                move_out.append(data)
        if recipients:
            # Mail template
            template = self.env.ref(
                'con_stock.stock_automatic_email_template')
            mail_template = self.env['mail.template'].browse(template.id)
            # Mail subject
            date = time.strftime('%d-%m-%Y')
            subject = "Notificación diaria de movimientos: " + str(date)
            # Update the context
            new_product_lst = sorted(list(set(products_lst)))
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': subject,
                'date': date,
                'products_lst': new_product_lst,
                'move_in': move_in,
                'move_out': move_out
            })
            # Send mail
            if mail_template and move_in and new_product_lst:
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)

    @api.multi
    def send_mail_notification_biweekly(self):
        """
        Stock mail weekly notifications
        """
        # senders
        uid = SUPERUSER_ID
        user_id = self.env[
            'res.users'].browse(uid)
        # Recipients
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  'Can receive stock notifications email biweekly']])
        if groups:
            for data in groups:
                for users in data.users:
                    recipients.append(users.email)
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        formated = "".join(
            html_escape_table.get(c, c) for c in recipients)
        # Stock move objects
        move_line_ids = self.env[
            'stock.move'].search(
                [['date', '>=', time.strftime('%Y-%m-01 00:00:00')],
                 ['date', '<=', time.strftime('%Y-%m-15 23:59:59')],
                 ['state', '=', 'done']])
        # Generate data for template
        products_lst = []
        move_in = []
        move_out = []
        for data in move_line_ids:
            if data.sale_line_id:
                products_lst.append(data.product_id)
            if not data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'customer' and \
                data.picking_id.location_id.usage \
                == 'internal':
                move_in.append(data)
            if data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'internal' and \
                data.picking_id.location_id.usage \
                == 'customer':
                move_out.append(data)
        if recipients:
            # Mail template
            template = self.env.ref(
                'con_stock.stock_automatic_email_template')
            mail_template = self.env['mail.template'].browse(template.id)
            # Mail subject
            date = time.strftime('%d-%m-%Y')
            subject = "Notificación quincenal de movimientos: " + str(date)
            # Update the context
            new_product_lst = sorted(list(set(products_lst)))
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': subject,
                'date': date,
                'products_lst': new_product_lst,
                'move_in': move_in,
                'move_out': move_out
            })
            # Send mail
            if mail_template and move_in and new_product_lst:
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)

    @api.multi
    def send_mail_notification_monthly(self):
        """
        Stock mail monthly notifications
        """
        # senders
        uid = SUPERUSER_ID
        user_id = self.env[
            'res.users'].browse(uid)
        # Recipients
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  'Can receive stock notifications email monthly']])
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
        # Stock move objects
        move_line_ids = self.env[
            'stock.move'].search(
                [['date', '>=', time.strftime('%Y-%m-01 00:00:00')],
                 ['date', '<=', time.strftime('%Y-%m-28 23:59:59')],
                 ['state', '=', 'done']])
        # Generate data for template
        products_lst = []
        move_in = []
        move_out = []
        for data in move_line_ids:
            if data.sale_line_id:
                products_lst.append(data.product_id)
            if not data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'customer' and \
                data.picking_id.location_id.usage \
                == 'internal':
                move_in.append(data)
            if data.returned \
                and data.picking_id.location_dest_id.usage \
                == 'internal' and \
                data.picking_id.location_id.usage \
                == 'customer':
                move_out.append(data)
        if recipients:
            # Mail template
            template = self.env.ref(
                'con_stock.stock_automatic_email_template')
            mail_template = self.env['mail.template'].browse(template.id)
            # Mail subject
            date = time.strftime('%d-%m-%Y')
            subject = "Notificación mensual de movimientos: " + str(date)
            # Update the context
            new_product_lst = sorted(list(set(products_lst)))
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': subject,
                'date': date,
                'products_lst': new_product_lst,
                'move_in': move_in,
                'move_out': move_out
            })
            # Send mail
            if mail_template and move_in and new_product_lst:
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)

    @api.multi
    def do_print_picking2(self):
        self.write({'printed': True})
        return self.env.ref(
            'con_stock.action_report_delivery_con').report_action(self)

    def button_scrap(self):
        self.ensure_one()
        products = self.env['product.product']
        for move in self.move_lines:
            if move.state not in ('done') and move.product_id.type in ('product', 'consu'):
                products |= move.product_id
        return {
            'name': _('Scrap'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.scrap',
            'view_id': self.env.ref('stock.stock_scrap_form_view2').id,
            'type': 'ir.actions.act_window',
            'context': {'default_picking_id': self.id, 'product_ids': products.ids},
            'target': 'new',
        }