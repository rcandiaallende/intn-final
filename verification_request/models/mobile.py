# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Mobile(models.Model):
    _name = "mobile"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string='Móvil', required=True, copy=False,
                       default=lambda self: 'New')
    active = fields.Boolean('Active', default=True, tracking=True)
    patent_plate = fields.Char(string='Chapa', required=True, copy=False, tracking=True)
    model = fields.Char(string='Modelo', tracking=True)
    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('sequence.mobile') or 'New'
    #     return super(Mobile, self).create(vals)
