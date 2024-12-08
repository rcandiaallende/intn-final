from odoo import models, fields

class DesempenoCarga(models.Model):
    _name = 'desempeno.carga'
    _description = 'Desempeño de Carga'

    request_id = fields.Many2one(
        'certificado.bascula.aprobado',
        string='Certificado vinculado',
        ondelete='cascade'
    )
    mep = fields.Float(string='MEP')
    emep = fields.Char(string='eMEP')
    respuesta = fields.Char(string='Respuesta')
    indicacion = fields.Char(string='Indicacion')
    cargaAplicada = fields.Char(string='Carga Aplicada')
    errorInstrumento = fields.Float(string='Error del Instrumento')
    balanzaPesoSensible = fields.Float(string='Balanza Peso Sensible')