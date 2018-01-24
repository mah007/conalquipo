# -*- coding: utf-8 -*-

from odoo import models, fields, api


class projectWorks(models.Model):
    _inherit = "project.project"

    @api.one
    @api.depends('partner_id')
    def _get_partner_code(self):
        if self.partner_id:
            self.partner_code = self.partner_id.partner_code

    @api.model
    def default_get(self, flds):
        result = super(projectWorks, self).default_get(flds)
        return result

    work_code = fields.Char(string='Work Code')
    work_date_creation = fields.Date(
        string="Work date creation")
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
    business_name = fields.Many2one(
        'res.partner', string='Business name')
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
