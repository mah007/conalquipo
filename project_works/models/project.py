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
    observations = fields.Html(string='Observations', required=False)
    partner_code = fields.Char(
        string='Partner Code', compute='_get_partner_code', store=True)
