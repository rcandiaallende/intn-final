from odoo import models, fields

class CertificadoCalibracion(models.Model):
    _name = 'certificado.calibracion'
    _description = 'Certificados de calibración de pesas'

    certificado = fields.Char(string='Certificado', required=True)
    due_date = fields.Date(string='Fecha de Vencimiento', required=True)
    active = fields.Boolean(string='Activo', default=True)