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


from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class StockEmailNotification(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def send_mail_notification(self):
        # write your logic to find the time intervals(day 1, day 2, week)
        # based on the time interval trigger the mails.
        # use a loop to get the mail template id from the one2many
        template = self.env.ref(
            'con_stock_mail_automatic.notification_email_template')
        mail_template = self.env['mail.template'].browse(template.id)
        mail_template.write({'email_to': 'guadarramaangel@gmail.com',
                             'email_from': 'guadarramaangel@gmail.com',
                             'subject': 'Stock moves notification e-mail',
                             'body_html': 'Hola'})

        if mail_template:
            mail_template.send_mail(
                self.id, force_send=True, raise_exception=True)
