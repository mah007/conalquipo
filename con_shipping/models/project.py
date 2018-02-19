# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stock_location_id = fields.Many2one('stock.location',
                                        string='Location the project')

    @api.model
    def create(self, values):

        res = super(ProjectProject, self).create(values)

        stock_location = self.env['stock.location']

        stock_location_partner = stock_location.search([(
            'partner_id', '=', self.partner_id.id),
            ('name', '=', self.partner_id.name)])

        name_stock_location = res.partner_id.name + '/' + res.name

        if stock_location_partner:
            location_id = stock_location.create({
                'usage': 'customer',
                'partner_id': self.partner_id.id,
                'name': name_stock_location,
                'location_id': stock_location_partner,
                'project_id': res,
                })
        else:

            location_partner = stock_location.create({
                'usage': 'customer',
                'partner_id': self.partner_id.id,
                'name': res.partner_id.name,
                'location_id': self.env.ref(
                    'stock.stock_location_customers').id})

            location_id = stock_location.create({
                'usage': 'customer',
                'partner_id': self.partner_id.id,
                'name': name_stock_location,
                'location_id': location_partner.id,
                'project_id': res,
                })

        res.update({'stock_location_id': location_id.id})

        return res


class StockLocation(models.Model):
    _inherit = "stock.location"

    project_id = fields.One2many('project.project', 'stock_location_id',
                                 string='project')
