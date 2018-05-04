from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrderAdvertisementWizard(models.TransientModel):
    _name = "sale.order.advertisement.wizard"

    @api.multi
    def _get_default_loc(self):
        location = self.env['stock.location'].search([
                ('set_default_location', '=', True)], limit=1) or False
        return location

    project_id = fields.Many2one('project.project', string="Project")
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    partner_id = fields.Many2one('res.partner', 'Partner')
    location_id = fields.Many2one('stock.location', "Source Location")
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        domain=[('usage', '=', 'internal')],
        default=_get_default_loc)
    carrier_type = fields.Selection(
        [('client', 'Client'),
         ('company', 'Company')], default="company", string="Responsable")
    sale_order_line_id = fields.Many2one(
        'sale.order.line', string='Fleet Line',
        domain="[('order_id', '=', sale_order_id), "
               "('delivery_direction', 'in', ['in']),"
               "('picking_ids', '=', False)]")
    reason = fields.Selection([
        ('0', 'End project-work'),
        ('2', 'Change Because of Malfunction'),
        ('1', 'It seems very expensive'),
        ('3', 'Bad attention'),
        ('2', 'The equipment did not serve you'),
        ('0', 'No longer need it'),
    ], string="Reason")
    notes = fields.Text(string="Notes",)

    @api.onchange('carrier_type')
    def _onchange_carrier_type(self):
        for rec in self:
            if rec.carrier_type == 'client':
                self.sale_order_line_id = False

    @api.multi
    def _create_stock_picking(self, partner_id, project_id, picking_type,
                              src_location, des_location, origin, sale_id,
                              group_id, return_reason, user_notes,
                              carrier_type, child_move=False):
        """
        This function create a picking and the stock moves necessaries
        for do a movement between the locations for the return of the
        products assigned to a project.

        :param partner_id: The Partner's ID (Int).
        :param project_id: The Project's ID (Int).
        :param picking_type: The picking's XML ID (Int).
        :param src_location: The Source Location's ID (Int).
        :param des_location: The Destination Location's ID (Int).
        :param origin: The Document's Origin (Char)
        :param sale_id: The Sale's ID linked to the picking (Int)
        :param group_id: The procurement group linked to the picking (Int).
        :param return_reason: The reason for the product's return (Char).
        :param user_notes: Notes about the picking return (Char).
        :param carrier_type: Carrier type of the Picking (Char).
        :param child_move: Movement to copy (Recordset).
        :return: A record with the picking ID's
        """

        if not child_move:
            stock_move = self.env['stock.move'].search(
                [('location_dest_id', '=', src_location),
                 ('state', '=', 'done'),
                 ('picking_id.project_id', '=', project_id)])
        else:
            stock_move = [child_move]
            location_id = self.env['stock.location'].browse([des_location])


        picking_ids = []
        picking = self.env['stock.picking'].create({
            'partner_id': partner_id,
            'project_id': project_id,
            'picking_type_id': picking_type,
            'location_id': src_location,
            'location_dest_id': des_location,
            'origin': origin,
            'sale_id': sale_id,
            'group_id': group_id,
            'return_reason': return_reason,
            'user_notes': user_notes,
            'carrier_type': carrier_type,
        })


        for move in stock_move:
            product_origin = move.product_id.product_origin.id
            if product_origin != des_location:
                picking_ids.extend(self._create_stock_picking(
                    partner_id, project_id, picking_type, des_location,
                    product_origin, origin, sale_id, group_id, return_reason,
                    user_notes, carrier_type, move))
            self.env['stock.move'].create({
                'name': _('New Move:') + move.product_id.display_name,
                'partner_id': partner_id,
                'project_id': project_id,
                'product_id': move.product_id.id,
                'product_uom_qty': move.quantity_done,
                'product_uom': move.product_uom.id,
                'location_dest_id': des_location,
                'location_id': src_location,
                'returned': move.id,
                'picking_id': picking.id,
                'group_id': move.group_id.id,
                'state': 'draft',
                'sale_line_id': move.sale_line_id.id,
            })
            picking_ids.append(picking)
        return picking_ids

    @api.multi
    def action_create_advertisement(self):
        picking_ids = []

        # Create the picking for return products
        picking_ids.extend(self._create_stock_picking(
            self.partner_id.id, self.project_id.id,
            self.env.ref('stock.picking_type_in').id, self.location_id.id,
            self.location_dest_id.id, self.sale_order_id.name,
            self.sale_order_id.id,
            self.sale_order_id.procurement_group_id.id, self.reason,
            self.notes, self.carrier_type
        ))

        so_pickings = [x.id for x in self.sale_order_id.picking_ids]
        new_pickings = [x.id for x in picking_ids]
        so_pickings.extend(new_pickings)
        self.sale_order_id.update({'picking_ids': [(6, 0, so_pickings)]})

        # Set the delivery cost on sale order
        if self.carrier_type == 'company':
            self.sale_order_line_id.update(
                {'picking_ids': [(6, 0, [x.id for x in picking_ids if
                                         x.location_id.id ==
                                         self.location_id.id])
                                 ]})

        return {'type': 'ir.actions.act_window_close'}

