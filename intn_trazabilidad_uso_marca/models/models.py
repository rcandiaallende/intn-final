# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class intn_trazabilidad_uso_marca(models.Model):
#     _name = 'intn_trazabilidad_uso_marca.intn_trazabilidad_uso_marca'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100