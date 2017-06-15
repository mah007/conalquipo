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


class StockPicking(models.Model):
    _name = "stock.picking"

    @api.onchange('partner_id')
    def onchange_partner_id_trust(self):
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        if partner.trust_code:
            if partner.trust_code.message_type == 'no-message' and \
                    partner.parent_id:
                partner = partner.parent_id

            if partner.trust_code.message_type != 'no-message':
                if partner.trust_code.message_type != 'block' and \
                        partner.parent_id and \
                                partner.trust_code.message_type == 'block':
                    partner = partner.parent_id

                title = ("Warning for %s") % partner.name
                message = partner.trust_code.message_body
                warning = {
                    'title': title,
                    'message': message,
                }

                if partner.trust_code.message_type == 'block':
                    self.update({'partner_id': False,
                                 'partner_invoice_id': False,
                                 'partner_shipping_id': False,
                                 'pricelist_id': False})
                    return {'warning': warning}

            if warning:
                return {'warning': warning}