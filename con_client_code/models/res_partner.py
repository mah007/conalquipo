# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.tools.translate import _


class ResPartnerCode(models.Model):
    _inherit = "res.partner"

    partner_code = fields.Char(string='Partner Code', required=True)
