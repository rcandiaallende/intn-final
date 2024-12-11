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
    production_ids = fields.Many2many('mrp.production', string='Órdenes de producción', readonly=True)
    production_count = fields.Integer(string='Cantidad de Órdenes de Producción',
                                            compute='_compute_production_ids_count', readonly=True)
    document = fields.Binary(string="Documento", attachment=True)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    control_ingresos = fields.One2many('control.ingreso.instrumentos', 'calibration_request',
                                       string='Control de Ingresos')
    control_ingresos_count = fields.Integer(string='Cantidad de Controles de Ingresos',
                                            compute='_compute_control_ingresos_count', readonly=True)

    @api.depends('production_ids')
    def _compute_production_ids_count(self):
        for record in self:
            record.production_ids_count = len(record.production_ids)

    @api.depends('control_ingresos')
    def _compute_control_ingresos_count(self):
        for record in self:
            record.control_ingresos_count = len(record.control_ingresos)

    @api.model
    def get_state_string(self, state):
        return dict(self._fields['state'].selection).get(state)

    @api.multi
    def crear_control_ingreso(self):
        self.ensure_one()
        nuevo_control = self.env['control.ingreso.instrumentos'].create({'compromiso_entrega_fecha': self.work_date,
                                                                         'razon_social': self.partner_id.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'control.ingreso.instrumentos',
            'view_mode': 'form',
            'res_id': nuevo_control.id,
            'target': 'current',
        }

    @api.multi
    def action_open_control_ingresos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Control de Ingresos',
            'res_model': 'control.ingreso.instrumentos',
            'view_mode': 'tree,form',
            'domain': [('calibration_request', '=', self.id)],
            'context': {'default_calibration_request': self.id},
        }

    @api.multi
    def action_open_control_ingresos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Control de Ingresos',
            'res_model': 'control.ingreso.instrumentos',
            'view_mode': 'tree,form',
            'domain': [('calibration_request', '=', self.id)],
            'context': {'default_calibration_request': self.id},
        }

    @api.multi
    def action_open_production_ids(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de producción',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.production_ids.ids)],
            'context': {'default_calibration_request': self.id},
        }
