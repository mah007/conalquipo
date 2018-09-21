# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class ProdcuctPeplacements(models.TransientModel):
    _inherit = "product.replacements"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    init_date = fields.Date(
        string="initital date")
    end_date = fields.Date(
        string="End date")
    invoice_lines_ids = fields.One2many(
        'account.invoice.line', string="Lines")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'init_date', 'end_date', 'invoice_lines_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_account.action_product_replacements_report'
        ).with_context(landscape=True).report_action([], data=datas)