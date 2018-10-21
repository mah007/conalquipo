from odoo import models, api, _, fields
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError


class AccountInvoicePicking(models.TransientModel):
    _name = "account.invoice.picking"

    date_from = fields.Date()
    date_to = fields.Date()
    partner_ids = fields.Many2many('res.partner')
    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehicle')
    driver_ids = fields.Many2many('hr.employee', string='Employee')
    picking_ids = fields.Many2many('stock.picking')

    @api.multi
    @api.onchange(
        'date_from',
        'date_to',
        'partner_ids',
        'vehicle_ids',
        'driver_ids')
    def onchage_project(self):
        picking = self.env["stock.picking"]
        invoice = self.env["account.invoice.line"]
        for record in self:
            domain = [
                ('invoice_id.state', 'in', ['paid', 'open']),
                ('invoice_id.date_invoice', '>=', record.date_from),
                ('invoice_id.date_invoice', '<=', record.date_to),
                ('product_id.for_shipping', '=', True),
            ]
            if record.partner_ids:
                domain += [('partner_id', 'in', record.partner_ids.ids)]
            picking_ids = invoice.search(domain).mapped(
                'sale_line_ids').mapped("order_id.picking_ids")
            if record.driver_ids:
                picking_ids = picking_ids.filtered(
                    lambda x: x.driver_id.id in driver_ids.ids)
            if record.vehicle_ids:
                picking_ids = picking_ids.filtered(
                    lambda x: x.vehicle_id.id in vehicle_ids.ids)
            record.picking_ids = [(6, 0, picking_ids.ids)]

    def group_lines(self):
        res = {}
        lines = self.picking_ids
        for line in lines:
            for delivery in line.delivery_cost:
                partner_id = line.partner_id.id
                vehicle_id = line.vehicle_id.id
                driver_id = line.driver_ids.filtered(
                    lambda x: x.job_title == 'driver').driver_ids
                grouped = str((partner_id, vehicle_id))
                if grouped not in res:
                    res[grouped] = []
                res[grouped].append({
                    'date': line.scheduled_date,
                    'project': line.project_id.name,
                    'driver': driver_id.name,
                    'product': delivery.product_id.name,
                    'price': delivery.price_subtotal,
                    })
        return res

    def get_data_group(self, grouped):
        res = eval(grouped)
        return {
            'partner': self.env['res.partner'].browse(res[0]),
            'vehicle': self.env['fleet.vehicle'].browse(res[1])
        }

    def total_due(self):
        res = {}
        lines = self.picking_ids
        for line in lines:
            partner_id = line.partner_id.id
            vehicle_id = line.vehicle_id.id
            grouped = str((partner_id, vehicle_id))
            if grouped not in res:
                res[grouped] = 0.00
            res[grouped] += sum(line.delivery_cost.mapped(
                "price_subtotal"))
        return res

    def total_carries(self):
        amount = sum(self.picking_ids.mapped(
            "delivery_cost").mapped("price_subtotal"))
        return self.formatlang(amount)

    def formatlang(self, amount):
        currency = self.env.user.company_id.currency_id
        return formatLang(self.env, amount, currency_obj=currency)

    @api.multi
    def print_report(self):
        datas = {}
        lang_code = self.env.user.lang
        vals = {
            'from': format_date(
                self.env, self.date_from, lang_code=lang_code),
            'to': format_date(
                self.env, self.date_to, lang_code=lang_code),
            'group_lines': self.group_lines(),
            'total_due': self.total_due(),
        }
        datas['form'] = vals
        return self.env.ref(
            'con_account.action_account_invoice_picking_report').with_context(
                landscape=True).report_action([], data=datas)
        
