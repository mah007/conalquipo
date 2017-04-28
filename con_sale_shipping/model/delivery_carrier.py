# -*- coding: utf-8 -*-
##############################################################################
#
#    Ingeniería, Aplicaciones y Software S.A.S
#    Copyright (C) 2003-2017 Tiny SPRL (<http://www.ias.com.co>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models
import logging

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
    invoicing_area_id = fields.Many2one('invoicing.area',
                                        string='Invoicing Area', index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    municipality_id = fields.Many2one('res.country.municipality',
                                      string='Municipality')


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    municipality_ids = fields.Many2many('res.country.municipality',
                                        'delivery_carrier_municipality_rel',
                                        'carrier_id',
                                        'municipality_ids', 'Municipality',
                                        track_visibility='onchange'
                                        )

    products = fields.Many2many(comodel_name='product.template',
                                string='Product',
                                search='delivery_carrier_products',
                                track_visibility='onchange')

    delivery_carrier_cost = fields.One2many('delivery.carrier.cost',
                                            'delivery_carrier_id',
                                            string='Lines Delivery Carrier '
                                                   'Cost', copy=True)

    @api.onchange('state_ids')
    def onchange_states(self):
        self.country_ids = [(6, 0, self.country_ids.ids +
                             self.state_ids.mapped('country_id.id'))]
        self.municipality_ids = [(6, 0, self.municipality_ids.ids +
                                  self.municipality_ids.mapped('state_id.id'))
                                 ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    area_delivery_carrier = fields.Many2many(comodel_name='delivery.carrier',
                                             string='Area',
                                             search='delivery_carrier_rel',
                                             track_visibility='onchange')


class DeliveryCarrierCost(models.Model):
    _name = 'delivery.carrier.cost'

    vehicle = fields.Many2one(comodel_name='vehicle', string='Vehicle',
                              ndelete='cascade', index=True, copy=False,
                              track_visibility='onchange')

    cost = fields.Float(string='Cost', track_visibility='onchange')

    delivery_carrier_id = fields.Many2one('delivery.carrier',
                                          string='Delivery Carrier',
                                          ondelete='cascade', index=True,
                                          copy=False,
                                          track_visibility='onchange')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_type = fields.Selection(related='sale_id.carrier_type',
                                    readonly=True)

    vehicle_id = fields.Many2many(comodel_name='vehicle',  string='Vehicle',
                                  search='_search_vehicle_id',
                                  track_visibility='onchange')

    driver_id = fields.Many2many(comodel_name='hr.employee', string='Driver',
                                 search='_search_driver_id',
                                 track_visibility='onchange')

    assistant_id = fields.Many2many(comodel_name='hr.employee',
                                    string='Assistant',
                                    search='_search_assistant_id',
                                    track_visibility='onchange')

    vehicle_client = fields.Char(string='Vehicle',
                                 track_visibility='onchange')

    driver_client = fields.Char(string='Driver',
                                track_visibility='onchange')
