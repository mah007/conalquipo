# coding: utf-8
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by: Humberto Arocha <hbto@vauxoo.com>
#    Planified by: Rafael Silva <rsilvam@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################


from odoo import models, fields, api, _
from odoo.exceptions import Warning


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_approval = fields.Boolean(default=False,
                                   help='''Setting this field to True,
                                   allow to approve Sale 
                                   Orders after the shipping.''')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[
        ('waiting', _('waiting for approval')),
    ])
    approval_date = fields.Datetime(string="Approval date")

    @api.multi
    def action_confirm(self):
        approbal = self.env.user.company_id.sale_approval
        print approbal
        for order in self:
            order.state = 'sale' if not approbal else 'waiting'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            if not approbal:
                order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default(
                'sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True

    @api.multi
    def action_approval(self):
        if self.user_has_groups('sale_double_validation.sale_approval_team'):
            for order in self:
                order.state = 'sale'
                order.approval_date = fields.Datetime.now()
                if self.env.context.get('send_email'):
                    self.force_quotation_send()
                order.order_line._action_procurement_create()
            if self.env['ir.values'].get_default(
                    'sale.config.settings', 'auto_done_setting'):
                self.action_done()
            return True
        else:
            raise Warning(_('You are not a member of approval team'))
