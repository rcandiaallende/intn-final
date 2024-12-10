from odoo import models, fields

class Repetitibilidad(models.Model):
    _name = 'repetitibilidad'
    _description = 'Repetitibilidad'

    request_id = fields.Many2one(
        'certificado.bascula.aprobado',
        string='Certificado vinculado',
        ondelete='cascade'
    )
    indicacion = fields.Char(string='Indicacion')
    errorInstrumento = fields.Char(string='Error del Instrumento')
    mep = fields.Float(string='MEP')
    validacion = fields.Char(string='eMEP')
    repetitibilidadAl = fields.Float(string='Carga Aplicada')
