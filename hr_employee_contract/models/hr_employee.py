# -*- coding: utf-8 -*-

from odoo import fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    contract_id = fields.Many2one(
        'hr.contract', string="Contract")


class HrContract(models.Model):
    _inherit = "hr.contract"

    def _get_salary_type(self):
        types = [('7', _('weekly')),
                 ('15', _('biweekly')),
                 ('30', _('monthly')),
                 ('60', _('bimonthly')),
                 ('90', _('quarterly')),
                 ('180', _('semi-annually')),
                 ('360', _('annually')),
                 ]
        return types

    wage_type = fields.Selection('_get_salary_type', string="Salary Type",
                                 default='30')
