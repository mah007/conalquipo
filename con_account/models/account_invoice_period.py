# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2018 IAS (<http://www.ias.com.co>).
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
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT, float_compare,
                        float_is_zero)

_logger = logging.getLogger(__name__)


class AccountInvoiceYearPeriod(models.Model):
    _name = 'account.invoice.year.period'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    periods_ids = fields.One2many('account.invoice.period.period', 'year_id',
                                  string="Periods")
    interval = fields.Selection([('biweekly', 'Biweekly'),
                                 ('monthly', 'Monthly')])
    state = fields.Selection(
        [('draft', _('Draft')),
         ('open', _('Open')),
         ('closet', _('Closet'))],
        default="draft")
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)

    @api.multi
    def button_create_periods(self):
        # FIXME: Please fix the biweekly formula incorrect results
        period_obj = self.env['account.invoice.period.period']
        for rec in self:
            ds = datetime.strptime(rec.start_date, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < rec.end_date:
                if rec.interval == 'monthly':
                    de = ds + relativedelta(months=1, days=-1)
                else:
                    de = ds + relativedelta(weeks=2)

                if de.strftime('%Y-%m-%d') > rec.end_date:
                    de = datetime.strptime(rec.end_date, '%Y-%m-%d')

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'start_date': ds.strftime('%Y-%m-%d'),
                    'end_date': de.strftime('%Y-%m-%d'),
                    'year_id': rec.id,
                })
                if rec.interval == 'monthly':
                    ds = ds + relativedelta(months=1)
                else:
                    ds = ds + relativedelta(weeks=2, days=1)
        return True

    @api.multi
    def button_open_year(self):
        for rec in self:
            rec.write({'state': 'open'})
        return True

    @api.multi
    def button_closet_year(self):
        for rec in self:
            rec.write({'state': 'closet'})
        return True

    def button_activate(self):
        return True


class AccountInvoicePeriodPeriod(models.Model):
    _name = 'account.invoice.period.period'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    year_id = fields.Many2one('account.invoice.year.period', string="Year")
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    state = fields.Selection([('draft', _('Draft')), ('open', _('Open')),
                              ('closet', _('Closet'))], default="draft")
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)

    def button_activate(self):
        return True

    @api.multi
    def button_open_period(self):
        for rec in self:
            rec.write({'state': 'open'})
        return True

    @api.multi
    def button_closet_period(self):
        for rec in self:
            rec.write({'state': 'closet'})
        return True
