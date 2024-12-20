# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class MailingListContact(models.TransientModel):
    _name = "mailing.list.contact"
    _description = "Mailing List Contact"

    x_mailing_list_id = fields.Many2one(comodel_name="mailing.list", string="Mailing List", required=True, )
    x_mailing_list_contact_ids = fields.Many2many(comodel_name="mailing.contact", relation="mailing_contact_mailing_list_contact_rel",
                                                  column1="mailing_contact_id", column2="mailing_list_contact_id", string="Mailing List Contacts", )

    @api.model
    def default_get(self, fields):
        res = super(MailingListContact, self).default_get(fields)
        mailing_list_contact_ids = self.env.context.get('active_ids')
        res.update({
            'x_mailing_list_contact_ids': mailing_list_contact_ids,
        })
        return res

    def action_add_contact_to_mailing_list(self):
        for rec in self:
            for contact in rec.x_mailing_list_contact_ids:
                if not rec.x_mailing_list_id in contact.subscription_list_ids.mapped('list_id').ids:
                    contact.subscription_list_ids = [(0, 0, {'list_id': rec.x_mailing_list_id.id,})]
                else:
                    subscription_list_id = contact.subscription_list_ids.search([('list_id', '=', rec.x_mailing_list_id.id)])
                    if subscription_list_id:
                        subscription_list_id.opt_out = False if subscription_list_id.opt_out else False

