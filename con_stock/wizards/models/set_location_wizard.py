# -*- coding: utf-8 -*-

from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class set_data_locations(models.TransientModel):
    _name = 'set.inv.locations'

    @api.onchange('get_locations')
    def _compute_locations(self):
        line_ids = []
        locations = self.env[
            'stock.location'].search([('usage', '=', self.get_locations)])
        if locations:
            for data in locations:
                val = {
                    'name': data.name,
                }
                line_ids.append((0, 0, val))
        self.locations_lines = [
            i for n, i in enumerate(line_ids) if i not in line_ids[n + 1:]]

    get_locations = fields.Selection(
        [('supplier', 'Supplier'),
         ('view', 'View'),
         ('internal', 'Internal'),
         ('customer', 'Customer')], 'Get locations')
    locations_lines = fields.One2many(
        'set.inv.locations.lines', 'set_data_id', 'Lines')

    @api.one
    def import_data_inv(self):
        for data in self.locations_lines:
            locations = self.env[
                'stock.location'].search([('name', '=', data.name)])
            for l in locations:
                if not l.set_default_location:
                    values = {
                        'product_state': data.states_id.id,
                        'color': data.color,
                        'set_default_location': False,
                        'set_product_state': True
                    }
                    l.update(values)
                else:
                    values = {
                        'product_state': data.states_id.id,
                        'color': data.color,
                        'set_default_location': True,
                        'set_product_state': True
                    }
                    l.update(values)


class set_data_locations_lines(models.TransientModel):
    _name = 'set.inv.locations.lines'

    set_data_id = fields.Many2one(
        'set.inv.locations', string="Set data wizard")
    name = fields.Char("Name")
    states_id = fields.Many2one(
        'product.states', string="State")
    color = fields.Char(string="Color", default="#FFFFFF",
                        help="Select the color of the state")

    @api.onchange('states_id')
    def _get_color(self):
        if self.states_id:
            self.color = self.states_id.color
