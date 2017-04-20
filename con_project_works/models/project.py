# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


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
        result['use_tasks'] = False
        return result

    work_code = fields.Char(string='Work Code', required=True)
    work_date_creation = fields.Date(
        string="Work date creation", required=True)
    invoice_limit_date = fields.Date(
        string="Invoice limit date", required=True)
    email = fields.Char()
    observations = fields.Html(string='Observations', required=False)
    partner_code = fields.Char(
        string='Partner Code', compute='_get_partner_code', store=True)
    legal_cont_responsible = fields.Many2one(
        'res.partner', string='Legal Responsible', required=True)
    contract_number = fields.Char(string='Contract Number', required=True)
    work_responsible = fields.Many2one(
        'res.partner', string='Work Responsible', required=True)
    work_resident = fields.Many2one(
        'res.partner', string='Work Resident', required=True)
    work_storer = fields.Many2one(
        'res.partner', string='Work Storer', required=True)
    work_contract = fields.Many2one(
        'res.partner', string='Work Contract', required=True)
    work_phone = fields.Char(string='Work Phone', required=True)
    work_owner = fields.Many2one(
        'res.partner', string='Work Owner', required=True)
    owner_phone = fields.Char(string='Owner Phone', required=True)
    work_interventor = fields.Many2one(
        'res.partner', string='Work Interventor', required=True)
    interventor_phone = fields.Char(string='Interventor Phone', required=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", string='State', ondelete='restrict')
    municipality_ids = fields.Many2many('res.country.municipality',
                                        'project_municipality_rel',
                                        'project_id',
                                        'municipality_ids', 'Municipality')
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
    street2 = fields.Char()
    street2_2 = fields.Char()
    zip2 = fields.Char(change_default=True)
    city2 = fields.Char()
    state2_id = fields.Many2one(
        "res.country.state", string='State', ondelete='restrict')
    country2_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
