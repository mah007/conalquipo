import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProjectProductAvailable(models.TransientModel):
    _name = "project.product.available"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company

    @api.onchange(
        'selectionby', 'typeselection', 'partner_ids', 'project_ids',
        'query_date')
    def _get_data_report(self):
        # Data
        products_lst = []
        partners = []
        projects = []
        pickings = []
        all_partners = self.env['res.partner'].search(
            [('company_id', '=', self.company_id.id)])
        all_projects = self.env['project.project'].search(
            [('company_id', '=', self.company_id.id)])
        start = ''
        end = ''

        # Enviroments
        bill_periods = self.env['account.invoice.year.period'].search(
            [('state', 'in', ['open']),
             ('company_id', '=', self.company_id.id)])

        if not bill_periods:
            raise ValidationError(_("You need defined a billing year and "
                                    "periods"))

        # Searching the period of the query date
        for period in bill_periods.periods_ids:
            if self.query_date >= period.start_date and self.query_date <= \
                    period.end_date:
                start = period.start_date
                end = period.end_date

        # Selections
        if self.typeselection == 'all' and self.selectionby == 'partner':
            partners = list(all_partners._ids)
            projects = list(all_projects._ids)
        elif self.typeselection == 'all' and self.selectionby == 'project':
            projects = list(all_projects._ids)
            partners = list(all_partners._ids)
        elif self.typeselection == 'manual' and self.selectionby == 'partner':
            partners = self.partner_ids._ids
            projects = list(all_projects._ids)
        elif self.typeselection == 'manual' and self.selectionby == 'project':
            projects = self.project_ids._ids
            partners = list(all_partners._ids)

        # Pickings
        if partners:
            # Historical Ids
            move_ids = self.env['stock.move.history'].search(
                [('partner_id', 'in', partners),
                 ('company_id', '=', self.company_id.id)]
            )
        else:
            move_ids = self.env['stock.move.history'].search(
                [('project_id', 'in', projects),
                 ('company_id', '=', self.company_id.id)]
            )

        # Filtering by period range
        move_ids = move_ids.search(
            [('picking_id.scheduled_date', '<=', end),
             ('picking_id.scheduled_date', '>=', start)])

        for info in self:
            info.products_ids = products_lst
            info.project_ids = projects
            info.partner_ids = partners
            info.move_ids = move_ids

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self._default_company())
    selectionby = fields.Selection(
        selection=[('partner', 'Partner'),
                   ('project', 'Project')],
        string="Selection by", default="partner")
    typeselection = fields.Selection(
        selection=[('all', 'All'),
                   ('manual', 'Manual')],
        string="Selection type", default="all")
    query_date = fields.Date(string="Date", default=fields.Date.today())
    partner_ids = fields.Many2many(
        'res.partner', string="Partners")
    project_ids = fields.Many2many(
        'project.project',
        string="Projects")
    move_ids = fields.Many2many('stock.move.history', string="History")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'selectionby', 'typeselection', 'partner_ids',
             'project_ids', 'move_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        _logger.warning(res)
        return self.env.ref(
            'con_project.action_report_product_project'
        ).with_context(landscape=True).report_action([], data=datas)
