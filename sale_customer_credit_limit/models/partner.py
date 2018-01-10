# -*- coding: utf-8 -*-
# © 2016 Tobias Zehntner
# © 2016 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Monetary(string='Credit Limit',
        default=lambda self: self.env.user.company_id.default_credit_limit,
        help='Total amount this customer is allowed to purchase on credit.')

    @api.constrains('credit_limit')
    @api.onchange('credit_limit')
    @api.multi
    def check_amount(self):
        for customer in self:
            if customer.credit_limit < 0:
                raise exceptions.Warning(
                    'Credit Limit cannot be a negative number')
