# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WizardMotivoRechazo(models.TransientModel):
    _name = 'wizard.motivo.rechazo'

    reason_selection = fields.Selection([
        ('climatic_conditions', 'Condiciones climáticas'),
        ('instrument_fault', 'Desperfecto del Instrumento'),
        ('repair', 'Por reparación'),
        ('closure', 'Por cierre del establecimiento'),
        ('owner_impediment', 'Impedimento del propietario o encargado'),
        ('mobile_fault', 'Desperfecto del móvil metrológico'),
        ('other', 'Otros..............')
    ], string='Seleccionar')

    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        active_id = self._context.get('active_id')
        verification_request_id = self.env['verification.request'].browse(active_id.id)
        verification_request_id.impossibility_act.reason_selection = self.reason_selection
        return act_close
