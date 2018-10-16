from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError


class AccountInvoiceProject(models.TransientModel):
    _name = "account.invoice.project"

    date_from = fields.Date()
    date_to = fields.Date()
    project_ids = fields.Many2many('project.project')
    partner_ids = fields.Many2many('res.partner')
    invoice_ids = fields.Many2many('account.invoice')
    can_print = fields.Boolean(default=False)

    @api.multi
    @api.onchange('date_from', 'date_to', 'project_ids', 'partner_ids')
    def onchage_project(self):
        invoice = self.env['account.invoice']
        for record in self:
            domain = [
                ('state', '=', 'open'),
                ('date_invoice', '>=', record.date_from),
                ('date_invoice', '<=', record.date_to),
            ]
            if record.project_ids:
                domain += [('project_id', 'in', record.project_ids.ids)]
            if record.partner_ids:
                domain += [('partner_id', 'in', record.partner_ids.ids)]
            invoice_ids = invoice.search(domain)
            record.can_print = invoice_ids and True or False
            record.invoice_ids = [(6, 0, invoice_ids.ids)]

    def group_lines(self):
        res = {}
        for inv in self.invoice_ids:
            partner_id = inv.partner_id.id
            project_id = inv.project_id.id
            if partner_id not in res:
                res[partner_id] = {}
            if inv.project_id.partner_id.id == partner_id and project_id not in res[partner_id]:
                res[partner_id][project_id] = []
            refunds = inv.refund_invoice_ids
            currency = inv.currency_id
            res[partner_id][project_id].append({
                'date_invoice': inv.date_invoice,
                'number': inv.number,
                'total': formatLang(
                    self.env, inv.amount_total, currency_obj=currency),
                'due': formatLang(
                    self.env, inv.residual, currency_obj=currency),
                'credit': formatLang(
                    self.env, inv.amount_total - inv.residual,
                    currency_obj=currency),
                'residual': inv.residual,
                'credit_note': ",".join(refunds.mapped("number") or []),
                'credit_note_value': formatLang(
                    self.env, sum(refunds.mapped("amount_total")),
                    currency_obj=currency),
            })
        return res

    def total_due(self):
        res = {}
        group_lines = self.group_lines()
        for partner_id, works in group_lines.items():
            for project_id, lines in group_lines[partner_id].items():
                if partner_id not in res:
                    res[partner_id] = {'total_client': 0.00, 'works': {}}
                if project_id not in res[partner_id]['works']:
                    res[partner_id]['works'] = {project_id: 0.00}
                res[partner_id]['total_client'] += sum([i['residual'] for i in lines])
                res[partner_id]['works'][project_id] += sum([i['residual'] for i in lines])
        return res

    def formatlang(self, amount):
        currency = (
            self.invoice_ids and self.invoice_ids[0].currency_id or
            self.env.user.company_id.currency_id)
        return formatLang(self.env, amount, currency_obj=currency)

    @api.multi
    def print_report(self):
        datas = {}
        lang_code = self.env.user.lang
        currency_id = (
            self.invoice_ids and self.invoice_ids[0].currency_id or
            self.env.user.company_id.currency_id)
        vals = {
            'from': format_date(
                self.env, self.date_from, lang_code=lang_code),
            'to': format_date(
                self.env, self.date_to, lang_code=lang_code),
            'group_lines': self.group_lines(),
            'total_due': self.total_due(),
            'currency_id': currency_id,
        }
        datas['form'] = vals
        return self.env.ref(
            'con_account.action_project_invoice_report').with_context(
                landscape=True).report_action([], data=datas)
        
