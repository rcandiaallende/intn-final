from odoo import fields, api, models, exceptions
import uuid


class ControlComprobantes(models.Model):
    _name = 'control.comprobantes'
    _description = "Control de Etiquetas Vendidas"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'