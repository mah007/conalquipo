# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class AccountInvoiceConfirm(models.TransientModel):
    _inherit = "account.invoice.confirm"

    custom_date = fields.Boolean(
        string="Set custom dates?", default=False,
        help="Set a custom dates for invoices.")
    new_date_invoice = fields.Date(
        string='New Invoice Date',
        help="New date for invoices")

    @api.multi
    def invoice_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['account.invoice'].browse(active_ids):
            if record.state != 'draft':
                raise UserError(_(
                    "Selected invoice(s) cannot be confirmed as they are not "
                    "in 'Draft' state."
                ))
            if self.custom_date and self.new_date_invoice:
                record.date_invoice = self.new_date_invoice
            record.action_invoice_open()
        return {'type': 'ir.actions.act_window_close'}
