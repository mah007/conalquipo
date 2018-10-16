from odoo import models, api, _, fields
from odoo.tools.misc import format_date
from odoo.exceptions import UserError


class AccountProjectClient(models.TransientModel):
    _name = "account.project.client"

    type_report = fields.Selection([
        ('client', 'To Client'),
        ('invoice', 'To Invoice'),
    ], required=True, default='client')
    date_from = fields.Date()
    date_to = fields.Date()
    project_ids = fields.Many2many('project.project')

    @api.multi
    @api.onchange('date_from', 'date_to')
    def onchage_project(self):
        project = self.env['project.project']
        for record in self:
            domain = [
                ('work_date_creation', '>=', record.date_from),
                ('work_date_creation', '<=', record.date_to),
            ]
            project_ids = project.search(domain)
            record.project_ids = [(6, 0, project_ids.ids)]

    @api.multi
    def invoiced_work(self):
        res = {}
        domain = [
            ('project_id', 'in', self.project_ids.ids),
            ('state', 'in', ['open'])
        ]
        invoices = self.env['account.invoice'].search(domain)
        for record in invoices:
            residual = record.residual
            amount_total = record.amount_total
            res[record.project_id.id] = {
                'invoiced': amount_total,
                'paid': amount_total - residual,
                'due': residual
            }
        return res
            
    @api.multi
    def print_report(self):
        lang_code = self.env.user.lang
        vals = {
            'from': format_date(
                self.env, self.date_from, lang_code=lang_code),
            'to': format_date(
                self.env, self.date_to, lang_code=lang_code),
            'project_ids': self.project_ids.ids,
            'invoiced_work': self.invoiced_work()
        }
        datas = {'ids': self.project_ids.ids}
        datas['form'] = vals
        return self.env.ref(
            'con_account.action_project_create_report').with_context(
                landscape=True).report_action([], data=datas)
        
