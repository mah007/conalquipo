# -*- coding: utf-8 -*-

import time
import logging
_LOGGER = logging.getLogger(__name__)
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError


class ProjectWorks(models.Model):
    _inherit = "project.project"

    @api.one
    @api.depends('partner_id')
    def _get_partner_code(self):
        if self.partner_id:
            self.partner_code = self.partner_id.partner_code
            self.country2_id = self.partner_id.country_id.id
            self.state2_id = self.partner_id.state_id.id
            self.municipality2_id = self.partner_id.municipality_id.id
            self.city2 = self.partner_id.city
            self.phone2 = self.partner_id.phone
            self.phone2 = self.partner_id.phone
            self.street2_1 = self.partner_id.street
            self.street2_2 = self.partner_id.street2
            self.zip2 = self.partner_id.zip

    @api.model
    def default_get(self, flds):
        # ~Todo: What that hell is flds?, change to a descriptive variable name
        result = super(ProjectWorks, self).default_get(flds)
        return result

    @api.model
    def _get_default_country(self):
        country = self.env[
            'res.country'].search([('code', '=', 'CO')], limit=1)
        return country

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
        default=_get_default_country,
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
        ondelete='restrict',
        track_visibility='onchange')
    municipality2_id = fields.Many2one(
        'res.country.municipality',
        string='Municipality',
        track_visibility='onchange')
    country2_id = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict',
        default=_get_default_country,
        track_visibility='onchange')
    product_count = fields.Integer(
        compute='_compute_product_count',
        string="Number of products on work",
        track_visibility='onchange')
    sector_id = fields.Many2one(
        comodel_name='res.partner.sector',
        string='Work Sector',
        track_visibility='onchange')
    secondary_sector_ids = fields.Many2one(
        comodel_name='res.partner.sector',
        string="Secondary work sectors",
        domain="[('parent_id', '=', sector_id)]",
        track_visibility='onchange')
    sector_id2 = fields.Many2one(
        comodel_name='res.partner.sector',
        string='Invoice Sector',
        track_visibility='onchange')
    secondary_sector_ids2 = fields.Many2one(
        comodel_name='res.partner.sector',
        string="Secondary invoice sectors",
        domain="[('parent_id', '=', sector_id2)]",
        track_visibility='onchange')
    is_comercial = fields.Boolean(
        compute='_compute_is_comercial',
        default=True)
    is_director_comercial = fields.Boolean(
        compute='_compute_is_director_comercial',
        default=True)
    is_logistic = fields.Boolean(
        compute='_compute_is_logistic',
        default=True)
    is_director_logistic = fields.Boolean(
        compute='_compute_is_director_logistic',
        default=True)
    employee_id = fields.Many2one(
        "hr.employee", string='Employee',
        track_visibility='onchange',
        domain=lambda self:self._getemployee())

    @api.model
    def _getemployee(self):
        # Domain for the employee
        employee_list = []
        actual_user = self.env.user
        other = actual_user.employee_ids
        for data in other:
            employee_list.append(data.id)
        return [('id', 'in', employee_list)]

    def _compute_is_comercial(self):
        for data in self:
            data.is_comercial = self.env.user.has_group(
                'con_profile.group_commercial')

    def _compute_is_director_comercial(self):
        for data in self:
            data.is_director_comercial = self.env.user.has_group(
                'con_profile.group_commercial_director')

    def _compute_is_logistic(self):
        for data in self:
            data.is_logistic = self.env.user.has_group(
                'con_profile.group_logistic')

    def _compute_is_director_logistic(self):
        for data in self:
            data.is_director_logistic = self.env.user.has_group(
                'con_profile.group_logistic_director')

    @api.constrains('sector_id', 'secondary_sector_ids')
    def _check_sectors(self):
        if self.sector_id in self.secondary_sector_ids:
            raise UserError(_('The main sector must be different '
                              'from the secondary sectors.'))

    @api.constrains('sector_id2', 'secondary_sector_ids2')
    def _check_sectors(self):
        if self.sector_id2 in self.secondary_sector_ids2:
            raise UserError(_('The main sector must be different '
                              'from the secondary sectors.'))

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
            if groups:
                for data in groups:
                    for users in data.users:
                        recipients.append(users.email)
            if recipients:
                body = _(
                    'Attention: The work %s are created by %s') % (
                        res.name, res.create_uid.name)
                res.send_followers(body, recipients)
                res.send_to_channel(body, recipients)
                res.send_mail(body)
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

    @api.multi
    def send_mail(self, body):
        recipients = []
        # Recipients
        recipients = []
        groups = self.env[
            'res.groups'].search(
                [['name',
                  '=',
                  'Administrative assistant']])
        if groups:
            for data in groups:
                for users in data.users:
                    recipients.append(users.email)
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        formated = "".join(
            html_escape_table.get(c, c) for c in recipients)
        if recipients:
            # Mail template
            template = self.env.ref(
                'con_project.create_work_email_template')
            mail_template = self.env[
                'mail.template'].browse(template.id)
            # senders
            uid = SUPERUSER_ID
            user_id = self.env[
                'res.users'].browse(uid)
            date = time.strftime('%d-%m-%Y')
            ctx = dict(self.env.context or {})
            ctx.update({
                'senders': user_id,
                'recipients': formated,
                'subject': body,
                'date': date,
            })
            # Send mail
            if mail_template:
                mail_template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=True)
