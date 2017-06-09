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

from odoo import fields, models, api
from calendar import monthrange
import datetime
import logging
import calendar

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_operator = fields.Boolean('Is Operator')
    product_ids = fields.Many2many(comodel_name='product.template',
                                   string='Product', search='hr_products',
                                   track_visibility='onchange')

    @api.onchange('is_operator')
    def onchange_is_operator(self):
        if not self.is_operator:
                self.write({'product_ids': None})


class Product(models.Model):
    _inherit = 'product.template'

    employee_ids = fields.Many2many(comodel_name='hr.employee',
                                    string='Employee', search='hr_employee',
                                    track_visibility='onchange')
    is_operated = fields.Boolean('Is Operated')


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_preoperation = fields.Boolean('Report Reoperation', default=False)

    m_instructive = fields.Boolean('Instructive Menssage', default=False)

    @api.multi
    def num_day(self):
        now = datetime.datetime.now()
        days = monthrange(now.year, now.month)
        calen = {}
        for day in xrange(1, days[1]+1):
            day = int(day)
            my_date = datetime.datetime(year=now.year, month=now.month,
                                        day=day)
            name = calendar.day_name[my_date.weekday()]
            calen.update({day: [my_date.strftime('%d'), name]})

        return calen

    @api.multi
    def month(self):
        now = datetime.datetime.now()
        month_int = int(now.month)
        month = calendar.month_name[month_int]
        return month

    @api.multi
    def fortnight(self):
        now = datetime.datetime.now()
        fortnight = ""
        if now.day < 15 or now.day == 15:
            fortnight = "Primera"
        else:
            fortnight = "Segunda"

        return fortnight

    @api.multi
    def year(self):
        now = datetime.datetime.now()
        return now.year
