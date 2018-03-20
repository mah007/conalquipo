from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectProductAvailable(models.TransientModel):
    _name = "project.product.available.wizard"

    date_from = fields.Date(
        string="From")
    date_to = fields.Date(
        string="To")
    project_ids = fields.Many2many('project.project',
                                  string="projects")