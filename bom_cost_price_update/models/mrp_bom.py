# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def get_currency(self):
        return self.env.user.company_id.currency_id
        
    @api.multi
    @api.depends('bom_line_ids', 'bom_line_ids.product_id','bom_line_ids.product_id.standard_price')
    def _compute_bom_cost_total(self):
        for rec in self:
            rec.total_cost = 0.0
            for line in rec.bom_line_ids:
                rec.total_cost += line.product_id.standard_price * line.product_qty
    
    total_cost = fields.Float(
        string='Total Cost', 
        store=True,
        compute='_compute_bom_cost_total', 
        digits=dp.get_precision('Product Price'),
    )
    
    currency_id = fields.Many2one(
        'res.currency', string='Currency', 
        default=get_currency, required=True,
        readonly=True,
    )
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
