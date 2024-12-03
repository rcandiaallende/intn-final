from odoo import models, fields, api


class CalibrationRequest(models.Model):
    _name = 'calibration.request'
    _description = 'Solicitud de calibración'

    state = fields.Selection(string="Estado",
                             selection=[('revision', 'En revisión'),
                                        ('approved', 'Presupuesto aprobado'),
                                        ('scheduled', 'Orden de trabajo programada')])
