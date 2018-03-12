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


from odoo import models, api, SUPERUSER_ID
import time
import logging
_logger = logging.getLogger(__name__)


class StockEmailNotification(models.Model):
    _inherit = "stock.picking"

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
        for data in groups:
            for users in data.users:
                recipients.append(users.login)
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        formated = "".join(
            html_escape_table.get(c,c) for c in recipients)
        # Stock move objects
        move_line_ids = self.env[
            'stock.move.line'].search(
                [['date', '>=', time.strftime('%Y-%m-%d 00:00:00')],
                 ['date', '<=', time.strftime('%Y-%m-%d 23:59:59')]])
        # Generate data for template
        partner_lst = []
        works_lst = []
        for data in move_line_ids:
            partner_lst.append(data.picking_id.partner_id)
            works_lst.append(data.picking_id.project_id)
        # Mail template
        template = self.env.ref(
            'con_stock_mail_automatic.stock_automatic_email_template')
        mail_template = self.env['mail.template'].browse(template.id)
        # Mail subject
        date = time.strftime('%d-%m-%Y') 
        subject = "Stock movements diary notification: " + str(date) 
        # Update the context
        ctx = dict(self.env.context or {})
        ctx.update({
            'senders': user_id,
            'recipients': formated,
            'subject': subject,
            'date': date,
            'partner_lst': list(set(partner_lst)),
            'works_lst': list(set(works_lst)),
            'move_line_ids': list(set(move_line_ids))
        })
        # Send mail
        if mail_template:
            mail_template.with_context(ctx).send_mail(
                self.id, force_send=True, raise_exception=True)