from odoo import models, fields

class Excentricidad(models.Model):
    _name = 'excentricidad'
    _description = 'Excentricidad'

    request_id = fields.Many2one(
        'certificado.bascula.aprobado',
        string='Certificado vinculado',
        ondelete='cascade'
    )
    mep = fields.Float(string='MEP')
    emep = fields.Char(string='eMEP')
    medio = fields.Char(string='Medio')
    punta1 = fields.Char(string='Punta 1')
    punta2 = fields.Char(string='Punta 2')
    direccion = fields.Char(string='Dirección')
    carga_aplicada = fields.Char(string='Carga Aplicada')
    error_instrumento = fields.Float(string='Error Instrumento')