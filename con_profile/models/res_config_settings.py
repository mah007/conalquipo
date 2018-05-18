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
import logging
_logger = logging.getLogger(__name__)
from odoo import models,api


class ResBaseConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.one 
    def set_pricelist_parameters(self):
        _logger.info("> Settings pricelist parameters")
        settings = self.env['res.config.settings'].create({
            'multi_sales_price': True,
            'multi_sales_price_method': 'formula'
        })
        settings.execute()
        _logger.info("> ... done.")