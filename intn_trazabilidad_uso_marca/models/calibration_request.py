from odoo import models, fields, api
from odoo.exceptions import AccessError, MissingError, UserError


class CalibrationRequest(models.Model):
    _name = 'calibration.request'
    _description = 'Solicitud de calibración'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "work_date desc, name, id"

    name = fields.Char(string='Referencia', required=True, copy=False, default='Nuevo')
    state = fields.Selection(selection=[('revision', 'En revisión'),
                                        ('approved', 'Presupuesto aprobado'),
                                        ('scheduled', 'Orden de trabajo programada')], string="Estado",
                             readonly=True, default='revision')
    work_date = fields.Date(string="Fecha de programación de trabajo")
    production_ids = fields.Many2many('mrp.production', string='Órdenes de producción', readonly=True)
    production_count = fields.Integer(string='Cantidad de Órdenes de Producción',
                                      compute='_compute_production_ids_count')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    control_ingresos = fields.One2many('control.ingreso.instrumentos', 'calibration_request',
                                       string='Control de Ingresos')
    control_ingresos_count = fields.Integer(string='Cantidad de Controles de Ingresos',
                                            compute='_compute_control_ingresos_count', readonly=True)
    users_to_notify = fields.Many2many('res.users', string='Usuarios a notificar')
    retiro = fields.Selection([
        ('retiro_1', 'El Solicitante'),
        ('retiro_2', 'Un Tercero')
    ], string="Método de Retiro", required=True, default='retiro_1')
    retiro_tercero_nombre = fields.Char('Nombre del Tercero')
    retiro_tercero_documento = fields.Char('Documento del Tercero')
    order_id = fields.Many2one('sale.order', string='Expediente')
    verificacion_insitu = fields.Boolean(string='Se verifica In Situ', default=False)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('calibration.request') or 'Nuevo'
        return super(CalibrationRequest, self).create(vals)

    @api.onchange('work_date')
    def _onchange_work_date(self):
        if self.work_date:
            self.state = 'scheduled'

    @api.multi
    @api.constrains('state', 'work_date')
    def _check_state(self):
        so_id = self.env['sale.order'].search([('calibration_request_id', '=', self.id)], limit=1)
        if self.work_date and not so_id.is_paid():
            raise UserError(f"No puede programar una fecha si la Factura de {so_id.name} está pendiente de pago.")
        if self.state == 'scheduled':
            if not self.users_to_notify:
                raise UserError("No hay usuarios seleccionados para notificar.")
            if not self.work_date:
                raise UserError(
                    f"No tiene asignada una Fecha de programación de trabajo en la solicitud de calibración {self.id}")
            self.notify_work_date_assigned(so_id)

    def notify_work_date_assigned(self, so_id):
        for rec in self:
            if not so_id or not so_id.name:
                raise UserError("El expediente no tiene un nombre válido.")

            if not rec.verificacion_insitu:
                subject = "Calibración Agendada"

                body = f"""
                <p>Estimado cliente,</p>
                <p>Le notificamos que su solicitud de calibración <strong>{rec.name}</strong> ha sido programada para la fecha: <strong>{rec.work_date}</strong>.</p>
                <p>Le solicitamos acceder a su usuario donde podrá encontrar la fecha programada para la recepción de su/s instrumento/s.</p>
                <p>Para los servicios de calibración que se realizan en los laboratorios del INTN, debe acercar sus instrumentos a las instalaciones del Organismo Nacional de Metrología, ubicado en:</p>
                <p><strong>Avenida Gral. Artigas N° 3973 casi Gral. Roa, Asunción - Paraguay.</strong></p>
                <p>El horario de recepción de instrumentos es de <strong>07:30 a 14:30 horas.</strong></p>
                <p>En caso de no entregar su/s instrumento/s en la fecha programada, se realizará una reprogramación del servicio sujeto a la carga de trabajo del laboratorio correspondiente.</p>
                <p>Le saludamos cordialmente,</p>
                <p><strong>Instituto Nacional de Tecnología, Normalización y Metrología</strong></p>
                """

                for user in rec.users_to_notify:
                    if not user.partner_id.email:
                        raise UserError(f"El usuario {user.name} no tiene un correo electrónico configurado.")

                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.partner_id.email,
                        'author_id': self.env.user.partner_id.id,
                    }
                    mail = rec.env['mail.mail'].sudo().create(mail_values)
                    mail.send(auto_commit=True)

    @api.depends('production_ids')
    def _compute_production_ids_count(self):
        for record in self:
            record.production_count = len(record.production_ids)

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
                                                                         'razon_social': self.partner_id.id,
                                                                         'calibration_request': self.id})
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

        current_user_id = self.env.user.id

        filtered_productions = self.production_ids.filtered(
            lambda production: any(
                responsible.id == current_user_id
                for responsible in production.product_id.laboratorio_id.responsables_ids
            )
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Producción',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', filtered_productions.ids)],
            'context': {'default_calibration_request': self.id},
        }
