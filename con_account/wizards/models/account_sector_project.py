from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError


class AccountSectorProject(models.TransientModel):
    _name = "account.invoice.sector.project"

    date_from = fields.Date()
    date_to = fields.Date()
    project_ids = fields.Many2many('project.project')
    partner_ids = fields.Many2many('res.partner')
    sector_ids = fields.Many2one('res.partner.sector')
    secondary_sector_ids = fields.Many2one(
        'res.partner.sector', domain="[('parent_id', '=', sector_ids)]")
    invoice_ids = fields.Many2many('account.invoice')
    can_print = fields.Boolean(default=False)

    @api.multi
    @api.onchange(
        'date_from', 'date_to', 'project_ids', 'partner_ids',
        'sector_ids', 'secondary_sector_ids')
    def onchage_invoice_sectors(self):
        invoice = self.env['account.invoice']
        for record in self:
            domain = [
                ('state', 'in', ['open', 'paid']),
                ('date_invoice', '>=', record.date_from),
                ('date_invoice', '<=', record.date_to),
            ]
            if record.project_ids:
                domain += [('project_id', 'in', record.project_ids.ids)]
            if record.partner_ids:
                domain += [('partner_id', 'in', record.partner_ids.ids)]
            if record.sector_ids:
                domain += [('sector_id', 'in', record.sector_ids.ids)]
            if record.secondary_sector_ids:
                domain += [
                    ('secondary_sector_ids', 'in',
                     record.secondary_sector_ids.ids)]
            invoice_ids = invoice.search(domain)
            record.can_print = invoice_ids and True or False
            record.invoice_ids = [(6, 0, invoice_ids.ids)]

    def group_lines(self):
        res = {}
        for inv in self.invoice_ids:
            sector_id = inv.sector_id.id
            secondary_sector_id = inv.secondary_sector_ids.id
            partner_id = inv.partner_id.id
            project_id = inv.project_id
            if not sector_id:
                continue
            if sector_id not in res:
                res[sector_id] = {
                    secondary_sector_id: {partner_id: []}}
            res[sector_id][secondary_sector_id][partner_id].append({
                'project_id': project_id.name,
                'amount_total': inv.amount_total})
        return res

    def get_percentage(self, amount, total):
        if isinstance(amount, str):
            amount = float(amount)
        if isinstance(total, str):
            total = float(total)
        if not total:
            return 0.0
        total = 100 * amount / total
        return "{}%".format(total)
        
    def total_sector(self, sector_id):
        res = self.invoice_ids.filtered(
            lambda x: x.sector_id.id == sector_id)
        res = sum(res.mapped('amount_total'))
        return res

    def total_subsector(self, sector_id, sub_id):
        res = self.invoice_ids.filtered(
            lambda x: x.sector_id.id == sector_id and
            x.secondary_sector_ids.id == sub_id)
        return sum(res.mapped('amount_total'))
        
    def percentage_subsector(self, sector_id, sub_id, total):
        res = self.invoice_ids.filtered(
            lambda x: x.sector_id.id == sector_id and
            x.secondary_sector_ids.id == sub_id)
        amount = sum(res.mapped('amount_total'))
        return self.get_percentage(amount, total)

    def total_partner(self, sector_id, sub_id, partner_id):
        res = self.invoice_ids.filtered(
            lambda x: x.sector_id.id == sector_id and
            x.secondary_sector_ids.id == sub_id and
            x.partner_id.id == partner_id)
        res = sum(res.mapped('amount_total'))
        return res

    def percentage_partner(self, sector_id, sub_id, partner_id, total):
        res = self.invoice_ids.filtered(
            lambda x: x.sector_id.id == sector_id and
            x.secondary_sector_ids.id == sub_id and
            x.partner_id.id == partner_id)
        amount = sum(res.mapped('amount_total'))
        return self.get_percentage(amount, total)

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
            'currency_id': currency_id,
        }
        datas['form'] = vals
        return self.env.ref(
            'con_account.action_project_sector_report').with_context(
                landscape=True).report_action([], data=datas)
        
