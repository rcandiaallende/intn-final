from odoo import models, fields, api


class CalibrationRequest(models.Model):
    _name = 'calibration.request'
    _description = 'Solicitud de calibración'

    state = fields.Selection(
        string="Estado",
        selection=[
            ('revision', 'En revisión'),
            ('approved', 'Presupuesto aprobado'),
            ('scheduled', 'Orden de trabajo programada')
        ],
        readonly=True,
        default='revision',
    )

    work_date = fields.Date(string="Fecha de programación de trabajo")
    workorder_id = fields.Many2one('mrp.workorder', string='Orden de trabajo')
    document = fields.Binary(string="Documento", attachment=True)

    @api.model
    def get_state_string(self, state):
        return dict(self._fields['state'].selection).get(state)
