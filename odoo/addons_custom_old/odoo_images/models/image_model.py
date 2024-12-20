# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class Images(models.Model):
    _name = "odoo.image"
    _description = "Odoo Images"
    _rec_name = "x_name"
    _order = "x_sequence"

    x_sequence = fields.Integer(string="Sequence", required=False, )
    x_name = fields.Char(string="Name", )
    x_image = fields.Binary(string="Images",  )
