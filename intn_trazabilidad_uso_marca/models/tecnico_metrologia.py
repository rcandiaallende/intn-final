from odoo import models, fields, api
from odoo.tools import datetime


class TecnicoMetrologia(models.Model):
    _name = 'tecnico.metrologia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Configurar Técnicos Metrología'

    usuario = fields.Many2one('res.users', string='Usuario Técnico', required=True)
    activo = fields.Boolean(string='Activo', default=True)
    date_inicio = fields.Date(string='Fecha de Inicio', required=True)
    date_final = fields.Date(string='Fecha de Finalización', required=False)
    log_cambios = fields.Text(string="Registro de Cambios")
    _log_access = True




