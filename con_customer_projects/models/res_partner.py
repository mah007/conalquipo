# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.tools.translate import _


class ResPartnerProject(models.Model):
    _inherit = "res.partner"

    project_ids = fields.One2many('project.project', 'partner_id')
