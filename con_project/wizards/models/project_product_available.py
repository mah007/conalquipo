import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectProductAvailable(models.TransientModel):
    _name = "project.product.available"

    @api.model
    def _default_company(self):
        # Get the company
        company = self.env['res.users'].browse([self._uid]).company_id
        return company

    @api.onchange(
        'selectionby', 'typeselection', 'products_ids',
        'in_move_ids', 'out_move_ids', 'partner_ids', 'project_ids')
    def _get_data_report(self):
        # Data
        products_lst = []
        partners = []
        projects = []
        pickings = []
        all_partners = self.env['res.partner'].search([])
        all_projects = self.env['project.project'].search([])

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
        if partners or projects:
            out_pickings = self.env['stock.picking'].search(
                [('partner_id', 'in', partners),
                 ('project_id', 'in', projects),
                 ('state', '=', 'done'),
                 ('location_dest_id', '=', self.env.ref(
                     'stock.stock_location_customers').id)])
            in_pickings = self.env['stock.picking'].search(
                [('partner_id', 'in', partners),
                 ('project_id', 'in', projects),
                 ('state', '=', 'done'),
                 ('location_id', '=', self.env.ref(
                     'stock.stock_location_customers').id)])
            pickings = out_pickings + in_pickings

            # Moves
            out_moves = self.env['stock.move'].search(
                [('state', '=', 'done'),
                 ('location_dest_id', '=', self.env.ref(
                     'stock.stock_location_customers').id),
                 ('picking_id', 'in', out_pickings._ids)]) or False
            if out_moves:
                for data in out_moves:
                    if data.sale_line_id:
                        products_lst.append(data.product_id.id)
            in_moves = self.env['stock.move'].search(
                [('state', '=', 'done'),
                 ('location_id', '=', self.env.ref(
                     'stock.stock_location_customers').id),
                 ('picking_id', 'in', in_pickings._ids)]) or False
            if in_moves:
                for data in in_moves:
                    if data.sale_line_id:
                        products_lst.append(data.product_id.id)
            for info in self:
                info.products_ids = products_lst
                info.in_move_ids = in_moves
                info.out_move_ids = out_moves
                info.project_ids = projects
                info.partner_ids = partners
                info.picking_ids = pickings

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
    partner_ids = fields.Many2many(
        'res.partner', string="Partners")
    project_ids = fields.Many2many(
        'project.project',
        string="Projects")
    products_ids = fields.Many2many(
        'product.product', string="Products")
    picking_ids = fields.Many2many(
        'stock.picking', string="All pickings")
    in_move_ids = fields.Many2many(
        'stock.move', string="Moves in")
    out_move_ids = fields.Many2many(
        'stock.move', string="Moves out")

    @api.multi
    def print_report(self):
        """
        To get the date and print the report
        @return : return report
        """
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(
            ['company_id', 'selectionby', 'picking_ids',
             'typeselection', 'partner_ids', 'project_ids',
             'products_ids', 'in_move_ids', 'out_move_ids'])
        res = res and res[0] or {}
        datas['form'] = res
        _logger.warning(res)
        return self.env.ref(
            'con_project.action_report_product_project'
        ).with_context(landscape=True).report_action([], data=datas)