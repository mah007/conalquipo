import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CustomerPortfolio(models.TransientModel):
    _name = "customer.portfolio"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company

    @api.onchange(
        'typeselection', 'partner_ids', 'invoice_ids')
    def _get_data_report(self):
        # Data
        partners = []
        invoices_lst = []
        all_partners = self.env['res.partner'].search([])
        all_projects = self.env['project.project'].search([])

        # Selections
        if self.typeselection == 'all':
            partners = list(all_partners._ids)
        else:
            partners = self.partner_ids._ids

        if partners:
            invoices = self.env['account.invoice'].search(
                [('partner_id', 'in', partners)]) or False
            if invoices:
                invoices_lst = invoices._ids
                for info in self:
                    info.partner_ids = partners
                    info.invoice_ids = invoices_lst

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    typeselection = fields.Selection(
        selection=[('all', 'All'),
                   ('manual', 'Manual')],
        string="Selection type", default="all")
    partner_ids = fields.Many2many(
        'res.partner', string="Partners")
    invoice_ids = fields.Many2many(
        'account.invoice',
        string="Invoices")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'typeselection', 'partner_ids',
             'invoice_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_sale.action_report_customer_portfolio'
        ).with_context(landscape=True).report_action([], data=datas)