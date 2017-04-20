# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResCountryMunicipality(models.Model):
    _name = 'res.country.municipality'

    _description = "Municipality"
    _order = 'sequence, id'

    ''''''
    sequence = fields.Integer(help="Determine the display order", default=10)
    name = fields.Char(string="Name")
    state_id = fields.Many2one('res.country.state', string='State')
    code = fields.Char(string="Code")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    municipality_ids = fields.Many2many('res.country.municipality',
                                        'delivery_carrier_municipality_rel',
                                        'carrier_id',
                                        'municipality_ids', 'Municipality')

    @api.onchange('state_ids')
    def onchange_states(self):
        self.country_ids = [(6, 0, self.country_ids.ids +
                             self.state_ids.mapped('country_id.id'))]
        self.municipality_ids = [(6, 0, self.municipality_ids.ids +
                                  self.municipality_ids.mapped('state_id.id'))
                                 ]