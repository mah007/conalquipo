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


class PackOperation(models.Model):
    _inherit = "stock.pack.operation"

    operator_ids = fields.Many2one(comodel_name='hr.employee',
                                   string='Operator')
    is_operated = fields.Boolean('Is Operated')

    @api.multi
    @api.onchange('product_id', 'product_uom_id', 'operator_ids')
    def onchange_product_id(self):

        doamin = {}
        if self.product_id:

            self.lots_visible = self.product_id.tracking != 'none'
            if not self.product_uom_id or self.product_uom_id.category_id != \
                    self.product_id.uom_id.category_id:

                self.product_uom_id = self.product_id.uom_id.id
                doamin.update({'product_uom_id': [
                    ('category_id', '=', self.product_uom_id.category_id.id)]})

            if not self.operator_ids:

                self.operator_ids = self.product_id.employee_ids.ids
                doamin.update(
                    {'operator_ids': [('id', 'in',
                                       self.product_id.employee_ids.ids)]})
            if not self.is_operated:
                self.update({'is_operated': self.product_id.is_operated})
            else:
                self.update({'is_operated': self.product_id.is_operated})

            res = {'domain': doamin}
        else:
            res = {'domain': {'product_uom_id': []}}
        return res

    @api.multi
    def action_see_instructive(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product_id.product_tmpl_id.id)]
        attachment_view = \
            self.env.ref('con_stock.view_document_file_kanban_instructive')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to upload files to your product.
                       </p><p>
                           Use this feature to store any files, like
                           drawings or specifications.
                       </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" %
                       ('product.product', self.product_id.id)
        }


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_preoperation = fields.Boolean('Repor Reoperation', default=False)
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
    @api.onchange('pack_operation_product_ids')
    def onchange_pack_operation_product_ids(self):
        if self.pack_operation_product_ids:
            for ids in self.pack_operation_product_ids:
                if ids.operator_ids:
                    self.update({'is_preoperation': True})
                else:
                    self.update({'m_instructive': True})

    @api.multi
    def year(self):
        now = datetime.datetime.now()
        return now.year
