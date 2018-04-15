# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProjectWorks(models.Model):
    _inherit = "project.project"

    @api.one
    @api.depends('partner_id')
    def _get_partner_code(self):
        if self.partner_id:
            self.partner_code = self.partner_id.partner_code
            self.country_id = self.partner_id.country_id.id
            self.country2_id = self.partner_id.country_id.id

    @api.model
    def default_get(self, flds):
        # ~Todo: What that hell is flds?, change to a descriptive variable name
        result = super(ProjectWorks, self).default_get(flds)
        return result

    work_code = fields.Char(string='Work Code')
    work_date_creation = fields.Date(
        string="Work date creation",
        default=fields.Date.today())
    invoice_limit_date = fields.Date(
        string="Invoice limit date")
    email = fields.Char()
    observations = fields.Html(string='Observations', required=False)
    partner_code = fields.Char(
        string='Partner Code', compute='_get_partner_code', store=True)
    legal_cont_responsible = fields.Many2one(
        'res.partner', string='Legal Responsible')
    contact_number = fields.Char(string='contact Number')
    work_responsible = fields.Many2one(
        'res.partner', string='Work Responsible')
    work_resident = fields.Many2one(
        'res.partner', string='Work Resident')
    work_storer = fields.Many2one(
        'res.partner', string='Work Storer')
    work_contact = fields.Many2one(
        'res.partner', string='Work contact')
    work_phone = fields.Char(string='Work Phone')
    work_owner = fields.Many2one(
        'res.partner', string='Work Owner')
    owner_phone = fields.Char(string='Owner Phone')
    work_interventor = fields.Many2one(
        'res.partner', string='Work Interventor')
    business_name = fields.Char(string='Business name')
    interventor_phone = fields.Char(string='Interventor Phone')
    street1 = fields.Char()
    street1_2 = fields.Char()
    phone1 = fields.Char(string='Phone')
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", string='State', ondelete='restrict')
    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
    street2_1 = fields.Char()
    street2_2 = fields.Char()
    phone2 = fields.Char(string='Phone')
    zip2 = fields.Char(change_default=True)
    city2 = fields.Char()
    state2_id = fields.Many2one(
        "res.country.state", string='State', ondelete='restrict')
    municipality2_id = fields.Many2one('res.country.municipality',
                                       string='Municipality')
    country2_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
    product_count = fields.Integer(
        compute='_compute_product_count',
        string="Number of products on work")
    stock_location_id = fields.Many2one('stock.location',
                                        string='Location the project')

    def _compute_product_count(self):
        """
        Method to count the products on works
        """
        for record in self:
            product_qty_in = 0.0
            picking = self.env[
                'stock.picking'].search(
                    [['partner_id', '=', record.partner_id.id],
                     ['location_dest_id.usage', '=', 'customer']])
            for data in picking:
                moves = self.env[
                    'stock.move.line'].search(
                        [['picking_id', '=', data.id],
                         ['location_dest_id',
                          '=',
                          data.location_dest_id.id],
                         ['state', '=', 'done']])
                if moves:
                    for p in moves:
                        product_qty_in += p.qty_done
            record.product_count = product_qty_in

    @api.multi
    def product_tree_view(self):
        self.ensure_one()
        domain = []
        moves_data = []
        picking = self.env[
            'stock.picking'].search(
                [['partner_id', '=', self.partner_id.id]])
        for data in picking:
            if data.location_dest_id.usage == 'customer':
                move = self.env[
                    'stock.move.line'].search(
                        [['picking_id', '=', data.id],
                        ['location_dest_id', '=', data.location_dest_id.id],
                        ['state', '=', 'done']])
                for m in move:
                    moves_data.append(m.id)
        domain = [('id', 'in', moves_data)]
        return {
            'name': _('Products'),
            'domain': domain,
            'res_model': 'stock.move.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.id)
        }

    @api.model
    def create(self, values):
        res = super(ProjectWorks, self).create(values)
        location_id = None
        if values['partner_id']:
            numbers = []
            max_number = 1
            # Get partner
            partner_obj = self.env['res.partner']
            partner = partner_obj.search([('id', '=', values['partner_id'])])
            p_code = partner.partner_code
            # Project code
            project_obj = self.env['project.project']
            projects = project_obj.search(
                [('partner_id', '=', values['partner_id'])])
            for a in projects:
                if a.work_code:
                    text = str(a.work_code)
                    code = int(text[text.find("-") + 1:])
                    numbers.append(code)
            if numbers:
                max_number = max(numbers) + 1
            values['work_code'] = str(p_code) + '-' + str(max_number)

            # Stock partner location
            stock_location = self.env['stock.location']
            stock_location_partner = stock_location.search([(
                'partner_id', '=', partner.id),
                ('name', '=', partner.name)])
            name_stock_location = partner.name + '/' + res.name
            if stock_location_partner:
                location_id = stock_location.create({
                    'usage': 'customer',
                    'partner_id': partner.id,
                    'name': name_stock_location,
                    'location_id': stock_location_partner,
                    'project_id': res.id,
                    })
            # else:
            #     location_partner = stock_location.create({
            #         'usage': 'customer',
            #         'partner_id': partner.id,
            #         'name': res.partner_id.name,
            #         'location_id': self.env.ref(
            #             'stock.stock_location_customers').id
            #     })
            #     location_id = stock_location.create({
            #         'usage': 'customer',
            #         'partner_id': partner.id,
            #         'name': name_stock_location,
            #         'location_id': location_partner.id,
            #         'project_id': res.id,
            #     })
            # res.update({'stock_location_id': location_id.id})
        else:
            raise UserError(_("You need to select a client!"))
        return res
