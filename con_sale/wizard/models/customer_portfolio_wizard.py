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

    @api.onchange('typeselection')
    def _get_data_partners(self):
      # Selections
        self.invoice_ids = [(5,)]
        self.project_ids = [(5,)]
        all_partners = self.env['res.partner'].search([])
        if self.typeselection == 'manual':
            self.partner_ids = [(5,)]
            self.project_ids = [(5,)]
        else:
            self.partner_ids = list(all_partners._ids)

    @api.onchange('partner_ids', 'invoice_ids')
    def _get_data_report(self):
        # Data
        self.invoice_ids = [(5,)]
        self.project_ids = [(5,)]
        self.can_print = False
        partners = []
        invoices_lst = []
        project_lst = []
        all_partners = self.env['res.partner'].search([])

        # Selections
        if self.typeselection == 'all':
            partners = list(all_partners._ids)
        else:
            partners = self.partner_ids._ids
        if partners:
            invoices = self.env['account.invoice'].search(
                [('partner_id', 'in', partners),
                 ('state', 'in', ['draft', 'open'])]) or False
            if invoices:
                for data in invoices:
                    project_lst.append(data.project_id.id)
                invoices_lst = invoices._ids
                for info in self:
                    info.partner_ids = partners
                    info.invoice_ids = invoices_lst
                    info.project_ids = project_lst
                    if info.invoice_ids:
                        info.can_print = True

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
    project_ids = fields.Many2many(
        'project.project',
        string="Projects")
    can_print = fields.Boolean('Can print')

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'typeselection', 'partner_ids',
             'invoice_ids', 'project_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_sale.action_report_customer_portfolio'
        ).with_context(landscape=True).report_action([], data=datas)