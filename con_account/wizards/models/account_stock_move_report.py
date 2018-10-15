from odoo import models, api, _, fields
from odoo.exceptions import UserError


class AccountStockMoveReport(models.TransientModel):
    _name = "account.stock.move.report"

    date_from = fields.Date("Date from")
    date_to = fields.Date("Date to")
    project_ids = fields.Many2many('project.project', string="Work")
    partner_ids = fields.Many2many('res.partner', string="Partners")
    products_ids = fields.Many2many('product.product', string="Equipments")
    lines_ids = fields.Many2many(
        "account.stock.move.lines")
    can_print = fields.Boolean("Can print")

    @api.multi
    @api.onchange('project_ids', 'partner_ids', 'products_ids', 'date_from', 'date_to')
    def _compute_stock_move(self):
        lines = []
        stock_move = self.env["stock.move"]
        for record in self:
            if not all((record.date_from, record.date_to)):
                record.lines_ids = []
                record.can_print = False
                continue
            domain = [
                ('date', '>=', record.date_from),
                ('date', '<=', record.date_to)]
            if record.project_ids:
                domain += [('project_id', 'in', record.project_ids.ids)]
            if record.products_ids:
                domain += [('product_id', 'in', record.products_ids.ids)]
            if record.partner_ids:
                domain += [('partner_id', 'in', record.partner_ids.ids)]
            moves = stock_move.search(domain)
            record.can_print = moves and True or False
            for move in moves:
                vals = dict(
                    qty=self.get_product_count(move.id),
                    partner_id=move.partner_id.id,
                    product_id=move.product_id.id,
                    project_id=move.project_id.id,
                )
                res_id = self.env['account.stock.move.lines'].create(vals)
                lines.append(res_id.id)
            record.lines_ids = [(6, 0, lines)]

    @api.multi
    def get_product_count(self, move_id):
        domain = [('move_id', '=', move_id)]
        history = self.env["stock.move.history"].search(
            domain, order="id desc", limit=1)
        return history.product_count

    @api.multi
    def print_report(self):
        datas = {'ids': self.lines_ids.ids}
        datas['form'] = {}
        return self.env.ref(
            'con_account.action_account_stock_move_report'
        ).with_context(landscape=True).report_action([], data=datas)

    def sum_qty_lines(self, groups):
        res = []
        partner_group = {}
        for line in groups:
            partner_id = line.partner_id.id
            project_id = line.project_id.id
            if not partner_id or not project_id:
                continue
            if partner_id not in partner_group:
                partner_group[partner_id] = {}
            if project_id not in partner_group.get(partner_id, {}):
                partner_group[partner_id][project_id] = 0.0
            partner_group[partner_id][project_id] += line.qty
        for partner_id, groups in partner_group.items():
            for project_id, qty in groups.items():
                partner = self.env['res.partner'].browse(partner_id)
                project = self.env['project.project'].browse(project_id)
                res.append({
                    'partner_code': partner.partner_code,
                    'work_code': project.work_code,
                    'partner_name': partner.name,
                    'project_name': project.name,
                    'qty': qty,
                })
        return res
            
    @api.multi
    def group_lines(self):
        res = {}
        for line in self.lines_ids:
            if line.product_id.id not in res:
                group_line = self.lines_ids.filtered(
                    lambda x: x.product_id == line.product_id)
                res[line.product_id.id]= {
                    'lines': self.sum_qty_lines(group_line),
                    'total': float(sum(group_line.mapped('qty'))),
                }
        return res


class AccountReportClientLines(models.TransientModel):
    _name = "account.stock.move.lines"

    qty = fields.Integer(string="Qty")
    partner_id = fields.Many2one("res.partner")
    product_id = fields.Many2one("product.product")
    project_id = fields.Many2one('project.project')
