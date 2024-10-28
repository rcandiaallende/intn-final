from odoo import fields, api, models, exceptions


class ReglamentosLicencia(models.Model):
    _name = 'reglamentos.licencia'
    _description = "Reglamentos"
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre', copy=False,required=True, track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')
    reglamento_general = fields.Boolean('Reglamento General', default=False, track_visibility='onchange')
    reglamentos_especificos_ids = fields.Many2many('reglamentos.licencia','reglamentos_especificos', 'id', 'reglamentos_especificos_ids',string='Reglamentos Especificos', track_visibility='onchange')
    normas_ids = fields.Many2many('normas.licencia',string='Normas', track_visibility='onchange')
