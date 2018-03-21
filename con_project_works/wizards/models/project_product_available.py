from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectProductAvailable(models.TransientModel):
    _name = "project.product.available"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company


    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    date_from = fields.Date(
        string="From")
    date_to = fields.Date(
        string="To")
    selectionby = fields.Selection(selection=[('partner', 'Partner'),
                                              ('project', 'Project')],
                                   string="Selection by")
    project_ids = fields.Many2many('project.project',
                                  string="projects")
    partner_ids = fields.Many2many('res.partner',
                                  string="Partners")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'date_from', 'date_to',
             'selectionby', 'project_ids', 'partner_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_project_works.action_report_product_project'
        ).report_action([], data=datas)
