# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductReplacements(models.TransientModel):
    _name = "product.replacements"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company

    @api.onchange(
        'product_category_id', 'init_date', 'end_date')
    def _get_data_report(self):
        qty = 0.0
        qty_invoices = 0.0
        self.replacement_lines = []
        if self.init_date and self.end_date:
            invoice_lines_ids = self.env['account.invoice.line'].search(
                [('invoice_id.init_date_invoice', '>=', self.init_date),
                 ('invoice_id.end_date_invoice', '<=', self.end_date)])
            for data in invoice_lines_ids:
                if data.product_id.product_tmpl_id.categ_id.id ==\
                 self.product_category_id.id and data.invoice_id.state == \
                        'paid':
                    qty += data.quantity
                    qty_invoices += data.price_subtotal
                    self.replacement_lines = [(0, 0, {
                        'replacement_id': self.id,
                        'product_id': data.product_id.id,
                        'qty': qty,
                        'qty_invoices': qty_invoices})]

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    init_date = fields.Date(
        string="initital date")
    end_date = fields.Date(
        string="End date")
    product_category_id = fields.Many2one(
        'product.category', string="Product category")
    replacement_lines = fields.One2many(
        'product.replacements.lines', 'replacement_id', string="Lines")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id',
             'product_category_id',
             'init_date',
             'end_date',
             'replacement_lines'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_account.action_product_replacements_report'
        ).with_context(landscape=True).report_action([], data=datas)


class ProdcuctReplacementsLines(models.TransientModel):
    _name = "product.replacements.lines"

    replacement_id = fields.Many2one(
        'product.replacements', string="Replacement")
    product_id = fields.Many2one(
        'product.product', string="Product")
    qty = fields.Integer(
        string="Quantity")
    qty_invoices = fields.Integer(
        string="Amount invoiced")
