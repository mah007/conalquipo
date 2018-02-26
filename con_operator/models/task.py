# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2018 IAS Ingenieria, Aplicaciones y Software, S.A.S.
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

from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Function to create  event in the calendar for execution of the task
    # and that the programmer of the task can observe the availability
    # of the person assigned to the task.first create a meeting-type
    # activity which will be observed in the historical part of the task
    #  and will load the calendar, where the event can be scheduled
    # on the desired day.

    @api.multi
    def action_create_calendar_event(self):
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
            'default_activity_type_id': self.env.ref('mail.mail_activity_data_meeting').id,
            'default_res_id': self.user_id.id,
            'default_res_model': self.env.context.get('default_res_model'),
            'default_name': self.name,
            'default_description': (self.description.replace(
                '<p>', '').replace('</p>', '').replace('<br>', '')),
            'default_activity_ids': [(4, activity_id.id)],
        }
        return action
