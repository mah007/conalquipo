# -*- coding: utf-8 -*-

from openerp import models, fields


class MailMessage(models.Model):
    _inherit = 'mail.message'

    from_outlook = fields.Boolean(string='Added from Outlook', default=False)
