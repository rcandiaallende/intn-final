from odoo import fields, api, models, exceptions


class NormasLicencia(models.Model):
    _name = 'normas.licencia'
    _description = "Normas"
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Nombre', copy=False,required=True, track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')