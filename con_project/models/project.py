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

    work_code = fields.Char(
        string='Work Code', track_visibility='onchange')
    work_date_creation = fields.Date(
        string="Work date creation",
        default=fields.Date.today(),
        track_visibility='onchange')
    invoice_limit_date = fields.Date(
        string="Invoice limit date",
        track_visibility='onchange')
    email = fields.Char(
        track_visibility='onchange')
    observations = fields.Html(
        string='Observations',
        required=False,
        track_visibility='onchange')
    partner_code = fields.Char(
        string='Partner Code',
        compute='_get_partner_code',
        store=True,
        track_visibility='onchange')
    legal_cont_responsible = fields.Many2one(
        'res.partner',
        string='Legal Responsible',
        track_visibility='onchange')
    contact_number = fields.Char(
        string='contact Number',
        track_visibility='onchange')
    work_responsible = fields.Many2one(
        'res.partner',
        string='Work Responsible',
        track_visibility='onchange')
    work_resident = fields.Many2one(
        'res.partner',
        string='Work Resident',
        track_visibility='onchange')
    work_storer = fields.Many2one(
        'res.partner',
        string='Work Storer',
        track_visibility='onchange')
    work_contact = fields.Many2one(
        'res.partner',
        string='Work contact',
        track_visibility='onchange')
    work_phone = fields.Char(
        string='Work Phone',
        track_visibility='onchange')
    work_owner = fields.Many2one(
        'res.partner',
        string='Work Owner',
        track_visibility='onchange')
    owner_phone = fields.Char(
        string='Owner Phone',
        track_visibility='onchange')
    work_interventor = fields.Many2one(
        'res.partner',
        string='Work Interventor',
        track_visibility='onchange')
    business_name = fields.Char(
        string='Business name',
        track_visibility='onchange')
    interventor_phone = fields.Char(
        string='Interventor Phone',
        track_visibility='onchange')
    street1 = fields.Char(
        track_visibility='onchange')
    street1_2 = fields.Char(
        track_visibility='onchange')
    phone1 = fields.Char(
        string='Phone',
        track_visibility='onchange')
    zip = fields.Char(
        change_default=True,
        track_visibility='onchange')
    city = fields.Char(
        track_visibility='onchange')
    state_id = fields.Many2one(
        "res.country.state",
        string='State',
        ondelete='restrict',
        track_visibility='onchange')
    municipality_id = fields.Many2one(
        'res.country.municipality',
        string='Municipality',
        track_visibility='onchange')
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict',
        track_visibility='onchange')
    street2_1 = fields.Char(
        track_visibility='onchange')
    street2_2 = fields.Char(
        track_visibility='onchange')
    phone2 = fields.Char(
        string='Phone',
        track_visibility='onchange')
    zip2 = fields.Char(
        change_default=True,
        track_visibility='onchange')
    city2 = fields.Char(
        track_visibility='onchange')
    state2_id = fields.Many2one(
        "res.country.state",
        string='State',
        ondelete='restrict')
    municipality2_id = fields.Many2one(
        'res.country.municipality',
        string='Municipality',
        track_visibility='onchange')
    country2_id = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict',
        track_visibility='onchange')
    product_count = fields.Integer(
        compute='_compute_product_count',
        string="Number of products on work",
        track_visibility='onchange')

    def _compute_product_count(self):
        """
        Method to count the products on works
        """
        for record in self:
            product_qty_in = 0.0
            product_qty_out = 0.0
            picking = self.env[
                'stock.picking'].search(
                    [['partner_id', '=', record.partner_id.id],
                     ['location_dest_id.usage', 'in',
                      ['customer', 'internal']],
                     ['project_id', '=', record.id]
                    ])
            for data in picking:
                moves = self.env[
                    'stock.move'].search(
                        [['picking_id', '=', data.id],
                         ['location_dest_id',
                          '=',
                          data.location_dest_id.id],
                         ['state', '=', 'done']])
                if moves:
                    for p in moves:
                        if not p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'customer' and \
                           p.picking_id.location_id.usage \
                           == 'internal':
                            product_qty_in += p.product_uom_qty
                        if p.returned \
                           and p.picking_id.location_dest_id.usage \
                           == 'internal' and \
                           p.picking_id.location_id.usage \
                           == 'customer':
                            product_qty_out += p.product_uom_qty
            record.product_count = product_qty_in - product_qty_out

    @api.multi
    def product_tree_view(self):
        self.ensure_one()
        domain = []
        moves_data = []
        picking = self.env[
            'stock.picking'].search(
                [['partner_id', '=', self.partner_id.id],
                 ['location_dest_id.usage', 'in',
                  ['customer', 'internal']],
                 ['project_id', '=', self.id]
                ])
        for data in picking:
            move = self.env[
                'stock.move'].search(
                    [['picking_id', '=', data.id],
                     ['location_dest_id', '=',
                      data.location_dest_id.id],
                     ['state', '=', 'done']])
            for p1 in move:
                if not p1.returned and p1.sale_line_id:
                    moves_data.append(p1.id)
            for p2 in move:
                if p2.returned and p2.returned in moves_data:
                    moves_data.remove(p2.returned)

        domain = [('id', 'in', moves_data)]
        return {
            'name': _('Products'),
            'domain': domain,
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 20,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.id)
        }

    @api.model
    def create(self, values):
        res = super(ProjectWorks, self).create(values)
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
            res.work_code = str(p_code) + '-' + str(max_number)
            # Send notification to users when works is created
            recipients = []
            groups = self.env[
                'res.groups'].search(
                    [['name',
                    '=',
                    'Administrative assistant']])
            for data in groups:
                for users in data.users:
                    recipients.append(users.login)
            body = _(
                'Attention: The work %s are created by %s') % (
                    res.name, res.create_uid.name)
            res.send_followers(body, recipients)
            res.send_to_channel(body, recipients)
        else:
            raise UserError(_("You need to select a client!"))
        return res

    def send_followers(self, body, recipients):
        if recipients:
            self.message_post(body=body, type="notification",
                              subtype="mt_comment",
                              partner_ids=recipients)

    def send_to_channel(self, body, recipients):
        if recipients:
            ch_ob = self.env['mail.channel']
            ch = ch_ob.sudo().search([('name', 'ilike', 'general')])
            ch.message_post(attachment_id=[],
                            body=body, content_subtype="html",
                            message_type="comment", partner_ids=recipients,
                            subtype="mail.mt_comment")
            return True