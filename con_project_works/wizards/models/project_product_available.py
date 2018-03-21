from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectProductAvailable(models.TransientModel):
    _name = "project.product.available.wizard"

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

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = 'date_from' in data['form'] and data['form']['date_from'] or False
        result['date_to'] = 'date_to' in data['form'] and data['form']['date_to'] or ''
        result['selectionby'] = data['form']['selectionby'] or False
        result['project_ids'] = data['form']['project_ids'] or False
        result['partner_ids'] = data['form']['partner_ids'] or False
        return result

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'selectionby', 'project_ids', 'partner_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref(
            'con_project_works.action_report_product_project'
        ).report_action(self, data=data)