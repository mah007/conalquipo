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

    @api.onchange(
        'selectionby',
        'partner_ids',
        'project_ids',
        'date_from', 'date_to')
    def onchange_picking(self):
        projects_ids = []
        partners_ids = []
        moves_lines_ids = []
        pickings_ids = []
        if self.selectionby == 'partner':
            projects = self.env[
                'project.project'].search(
                    [['partner_id', 'in', self.partner_ids._ids]])
            for pro_data in projects:
                pickings = self.env[
                'stock.picking'].search(
                    [['project_id', '=', pro_data.id],
                     ['date', '>=', self.date_from],
                     ['date', '<=', self.date_to],
                     ['location_dest_id.usage',
                       '=', 'customer']])
                pickings_ids.append(pickings.id)
                projects_ids.append(pro_data.id)
            self.project_ids = projects_ids
        else:
            projects = self.env[
                'project.project'].search(
                    [['id', 'in', self.project_ids._ids]])
            for part_data in projects:
                pickings = self.env[
                'stock.picking'].search(
                    [['project_id', '=', part_data.id],
                     ['date', '>=', self.date_from],
                     ['date', '<=', self.date_to],
                     ['location_dest_id.usage',
                       '=', 'customer']])
                pickings_ids.append(pickings.id)
                partners_ids.append(part_data.partner_id.id)
            self.partner_ids = partners_ids
        moves = self.env[
        'stock.move.line'].search(
            [['picking_id', 'in', pickings_ids],
             ['state', '=', 'done']])
        for m in moves:
            moves_lines_ids.append(m.id)
        self.move_line_ids = moves_lines_ids

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    date_from = fields.Datetime(
        string="From")
    date_to = fields.Datetime(
        string="To")
    selectionby = fields.Selection(selection=[('partner', 'Partner'),
                                              ('project', 'Project')],
                                   string="Selection by")
    project_ids = fields.Many2many('project.project',
                                  string="projects")
    partner_ids = fields.Many2many('res.partner',
                                  string="Partners")
    move_line_ids = fields.Many2many(
        'stock.move.line', string="Partners")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'date_from', 'date_to',
             'selectionby', 'project_ids', 'partner_ids',
             'move_line_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref(
            'con_project_works.action_report_product_project'
        ).with_context(
            landscape=True).report_action([], data=datas)
