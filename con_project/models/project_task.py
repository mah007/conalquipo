# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    product_id = fields.Many2one('product.product', string="Product",
                                 help="The associated product to the service "
                                      "task")
    uom_id = fields.Many2one(
        'product.uom', string="UoM",
        help="The associated UoM to the service task")

    @api.multi
    def action_create_calendar_event(self):
        """Action function for create event from task over calendar.

        Function to create  event in the calendar for execution of the task
        and that the programmer of the task can observe the availability
        of the person assigned to the task.first create a meeting-type
        activity which will be observed in the historical part of the task
        and will load the calendar, where the event can be scheduled
        on the desired day.:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: return a dictionary with the view action.

        """
        self.ensure_one()
        meeting_act_type = self.env['mail.activity.type'].search(
            [('category', '=', 'meeting')], limit=1)
        activity_id = self.env['mail.activity'].create({
            'activity_type_id': meeting_act_type.id,
            'summary': 'Task Programming',
            'res_id': self.user_id.id,
            'user_id': self.user_id.id,
            'res_model_id': self.env.ref('project.model_project_task').id,
            'note': self.description,
        })

        self.write({'activity_ids': [(4, activity_id.id)]})

        action = self.env.ref('calendar.action_calendar_event').read()[0]
        action['context'] = {
            'search_default_partner_ids': self.user_id.name,
            'default_activity_type_id':
                self.env.ref('mail.mail_activity_data_meeting').id,
            'default_res_id': self.user_id.id,
            'default_res_model': self.env.context.get('default_res_model'),
            'default_name': self.name,
            'default_description': (self.description.replace(
                '<p>', '').replace('</p>', '').replace('<br>', '')),
            'default_activity_ids': [(4, activity_id.id)],
        }
        return action

    @api.onchange('sale_line_id')
    def onchange_sale_line_id(self):
        """On Changed function on sale_line_id.

            This function filters the users that are authorized to operate the
            equipment associated with this task:

          Args:
              self (record): Encapsulate instance object.

          Returns:
              Dict: return a dictionary with a dynamic domain.

        """
        domain = {}
        users = []

        if self.sale_line_id and self.sale_line_id.product_operate:
            product_tmpl_id = self.sale_line_id.product_operate.product_tmpl_id
            for employee in product_tmpl_id.employee_ids:
                users.append(employee.user_id.id)
                domain = {'user_id': [('id', 'in', users)]}

        return {'domain': domain}

    @api.model
    def create(self, values):
        """Overloaded create function on ProjectTask.

            This function write the operator selected in the task over the
            sale order line on field assigned_operator:

          Args:
              self (record): Encapsulate instance object.
              values (Dict): Dictionary with the fields values.

          Returns:
              Int: return the id's record created.

        """
        res = super(ProjectTask, self).create(values)

        if res.sale_line_id:
            res.sale_line_id.write({
                'assigned_operator': res.user_id.id})
        return res

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.onchange('unit_amount')
    def compute_qty_rem(self):
        self.task_id.sale_line_id.write({
            'qty_delivered': self.task_id.effective_hours})
