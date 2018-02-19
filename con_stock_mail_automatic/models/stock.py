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
import time
from prettytable import PrettyTable
import logging
_logger = logging.getLogger(__name__)


class StockEmailNotification(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def send_mail_notification(self):
        # Stock picking objects
        move_ids = self.env[
            'stock.move'].search(
                [['date', '>=', time.strftime('%Y-01-%d 00:00:00')],
                 ['date', '<=', time.strftime('%Y-12-%d 23:59:59')]])
        # Mail objects
        template = self.env.ref(
            'con_stock_mail_automatic.notification_email_template')
        mail_template = self.env['mail.template'].browse(template.id)
        subject = "Notificación de movimientos de stock: %s" % (
            time.strftime('%d-%m-%Y'))

        html = None
        t = PrettyTable(
            ['Producto',
             'Cantidad',
             'Ubicación origen',
             'Ubicación destino',
             'Fecha estimada',
             'Estado'])
        for a in move_ids:
            t.add_row(
                [a.product_id.name,
                 a.product_uom_qty,
                 a.location_id.name,
                 a.location_dest_id.name,
                 a.date_expected,
                 a.state])
        html = t.get_html_string(
            attributes={"border": "1"})

        mail_template.write({'email_to': 'dmpineda@conalquipo.com',
                             'email_from': 'dmpineda@conalquipo.com',
                             'subject': subject,
                             'body_html': html})
        # Send mail
        if mail_template:
            mail_template.send_mail(
                self.id, force_send=True, raise_exception=True)
