from odoo import models, fields, api, _
from odoo.exceptions import AccessError, MissingError, UserError


class ControlIngresoInstrumentos(models.Model):
    _name = 'control.ingreso.instrumentos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Control de Ingreso de Instrumentos'

    name = fields.Char(string='N° Documento',
                       default=lambda self: self.env['ir.sequence'].next_by_code('control.ingreso.instrumentos'))
    expediente = fields.Many2one('sale.order', string='N° de Expediente')
    product_id = fields.Many2one('product.product', string='Fabricar')
    centro_produccion = fields.Many2one('mrp.workcenter', string='Centro de Producción')
    razon_social = fields.Many2one('res.partner', string='Razón Social', tracking=True)
    ruc = fields.Char(related='razon_social.vat', string='R.U.C.')
    telefono_fax = fields.Char(related='razon_social.phone', string='Tel/Fax')
    contacto = fields.Char(string='Contacto')
    email = fields.Char(related='razon_social.email', string='Email')
    fecha = fields.Date(string='Fecha', default=fields.Date.today, tracking=True)
    compromiso_entrega_fecha = fields.Date(string='Compromiso de Entrega (Fecha)', tracking=True)
    compromiso_entrega_hora = fields.Float(string='Compromiso de Entrega (Hora)', help='Hora estimada en formato HH.MM')
    notas = fields.Text(string='Notas Generales', default=False, tracking=True)
    observaciones = fields.Text(string='Observaciones', default=False, tracking=True)
    line_ids = fields.One2many('control.ingreso.instrumentos.line', 'control_id', string='Líneas de Instrumentos')
    line_history_ids = fields.One2many('control.ingreso.instrumentos.line.history', 'control_history_id',
                                       string='Historial Salida', tracking=True)
    firma_recibi = fields.Binary(string='Firma Recibí Conforme (ONM - INTN)')
    firma_usuario = fields.Binary(string='Firma Usuario')
    aclaracion_recibi = fields.Char(string='Aclaración Recibí Conforme')
    aclaracion_usuario = fields.Char(string='Aclaración Usuario')
    cic_recibi = fields.Char(string='C.I.C. No Recibí Conforme')
    cic_usuario = fields.Char(string='C.I.C. No Usuario')
    production_id = fields.Many2one('mrp.production', string='Orden de Producción', readonly=True)
    retiro_parcial_fecha = fields.Date(string='Fecha (Parcial)')
    retiro_parcial_aclaracion_onm = fields.Char(string='Aclaración ONM')
    retiro_parcial_cic_onm = fields.Char(string='C.I.C. No ONM')
    retiro_parcial_aclaracion_usuario = fields.Char(string='Aclaración Usuario')
    retiro_parcial_cic_usuario = fields.Char(string='C.I.C. No Usuario')
    retiro_total_fecha = fields.Date(string='Fecha (Total)')
    retiro_total_aclaracion_onm = fields.Char(string='Aclaración ONM')
    retiro_total_cic_onm = fields.Char(string='C.I.C. No ONM')
    retiro_total_aclaracion_usuario = fields.Char(string='Aclaración Usuario')
    retiro_total_cic_usuario = fields.Char(string='C.I.C. No Usuario')
    calibration_request = fields.Many2one('calibration.request', string='Solicitud de Calibración')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('confirmed', 'Confirmado'),
                                        ('partial_pickup', 'Retiro Parcial'), ('pickup', 'Retiro')],
                             string="Estado", readonly=True, default='draft', tracking=True)

    @api.model
    def create(self, vals):
        record = super(ControlIngresoInstrumentos, self).create(vals)
        record._notify_budget_approved()
        return record

    def write(self, vals):
        res = super(ControlIngresoInstrumentos, self).write(vals)
        for record in self:
            if 'state' in vals:
                record._handle_state_change(vals['state'])
        return res

    def _handle_state_change(self, new_state):
        if new_state == 'confirmed':
            self._notify_calibration_scheduled()
        elif new_state == 'pickup':
            self._notify_calibration_completed()

    def _notify_customer(self, subject, body):
        if not self.calibration_request.verificacion_insitu:
            email_to = self.email
            if not email_to:
                raise UserError("El cliente no tiene un correo electrónico configurado.")

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': email_to,
                'author_id': self.env.user.partner_id.id,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()

    def _notify_budget_approved(self):
        """
        Notificar al cliente sobre la aprobación del presupuesto.
        """
        subject = "Presupuesto Finalizado"
        body = f"""
            <p>Estimado cliente,</p>
            <p>Su solicitud de presupuesto Nro. {self.name} ha sido aprobada. Le recordamos que la vigencia es de 15 días corridos.</p>
            <p>Para programar el servicio solicitado, el presupuesto debe ser abonado dentro del plazo de vigencia del presupuesto y remitido el comprobante de pago realizado al correo: facturacion@intn.gov.py.</p>
            <p>Le saludamos cordialmente,<br>Instituto Nacional de Tecnología, Normalización y Metrología</p>
            """
        self._notify_customer(subject, body)

    def _notify_calibration_scheduled(self):
        """
        Notificar al cliente sobre la programación de calibración.
        """
        subject = "Fecha de Programación de Calibración"
        body = f"""
            <p>Estimado cliente,</p>
            <p>Informamos que la solicitud de servicio Nro. {self.name} ha sido programada.</p>
            <p>Para los servicios de calibración que se realizan en los laboratorios del INTN, debe acercar sus instrumentos a las instalaciones del Organismo Nacional de Metrología.</p>
            <p>Le saludamos cordialmente,<br>Instituto Nacional de Tecnología, Normalización y Metrología</p>
            """
        self._notify_customer(subject, body)

    def _notify_calibration_completed(self):
        """
        Notificar al cliente sobre la finalización de la calibración.
        """
        subject = "Calibración Finalizada"
        body = f"""
            <p>Estimado cliente,</p>
            <p>Informamos que el servicio correspondiente a la solicitud Nro. {self.name} ha sido finalizado.</p>
            <p>Le solicitamos retirar sus instrumentos dentro de los próximos 5 días hábiles.</p>
            <p>Le saludamos cordialmente,<br>Instituto Nacional de Tecnología, Normalización y Metrología</p>
            """
        self._notify_customer(subject, body)

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            rec.notify_work_date_assigned(rec.expediente)

    def notify_work_date_assigned(self, so_id):
        for rec in self:

            subject = "Ingreso de Instrumento"

            body = f"""<p>Le notificamos que su instrumento ha ingresado su expediente es:  {so_id.name}</p>"""
            for user in rec.calibration_request.users_to_notify:
                if not user.partner_id.email:
                    raise UserError(f"El usuario {user.name} no tiene un correo electrónico configurado.")
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.partner_id.email,
                }
                mail = rec.env['mail.mail'].sudo().create(mail_values)
                mail.send()

    @api.multi
    def create_out_move(self):
        for rec in self:
            for line in rec.line_ids:
                line.cantidad_salida = line.cantidad
            rec.state = 'out'

    @api.multi
    def create_production_order(self):
        '''
        Método para crear una orden de producción basada en los datos del control de ingreso.
        '''
        self.ensure_one()

        if not self.product_id or not self.centro_produccion:
            raise models.ValidationError(_('Debe especificar un Producto y un Centro de Producción.'))

        product_uom = self.product_id.uom_id
        if not product_uom:
            raise models.ValidationError(_('El producto seleccionado no tiene una unidad de medida definida.'))

        if self.product_id.uom_id.category_id != product_uom.category_id:
            raise models.ValidationError(
                _('La unidad de medida definida en el producto no pertenece a la misma categoría que la unidad seleccionada.')
            )

        production_vals = {
            'product_id': self.product_id.id,
            'product_qty': 1.0,
            'product_uom_id': product_uom.id,
            'bom_id': self.product_id.bom_ids[:1].id if self.product_id.bom_ids else False,
            'date_planned_start': self.compromiso_entrega_fecha or fields.Datetime.now(),
            'workcenter_id': self.centro_produccion.id,
            'origin': self.name,
        }
        production = self.env['mrp.production'].create(production_vals)

        self.production_id = production.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
            'target': 'current',
        }


class ControlIngresoInstrumentosLine(models.Model):
    _name = 'control.ingreso.instrumentos.line'
    _description = 'Detalle de Instrumentos'

    item = fields.Integer(string='Ítem')
    cantidad = fields.Integer(string='Cantidad Ingreso')
    cantidad_salida = fields.Integer(string='Cantidad Salida', tracking=True)
    cantidad_faltante = fields.Integer(string='Cantidad Faltante', compute='_compute_cantidad_faltante', store=True,
                                       tracking=True)
    instrumento = fields.Many2one('instrument.inventory.metci', string='Instrumento')
    identificacion = fields.Char(related='instrumento.unique_identifier', string='Identificación')
    control_id = fields.Many2one('control.ingreso.instrumentos', string='Control de Ingreso')
    control_state = fields.Selection(related='control_id.state', string='Estado Control de Ingreso')
    document = fields.Binary(string="Documento", attachment=True)
    state = fields.Selection(selection=[('done', 'Calibrado'), ('not_done', 'Trabajo no realizado')],
                             string="Estado", readonly=True, default='not_done')

    @api.depends('cantidad', 'cantidad_salida')
    def _compute_cantidad_faltante(self):
        for record in self:
            record.cantidad_faltante = record.cantidad - record.cantidad_salida

    @api.multi
    def done_work(self):
        for rec in self:
            rec.state = 'done'

            email_to = rec.control_id.razon_social.email if rec.control_id.razon_social else None
            if not email_to:
                raise UserError("El cliente no tiene un correo electrónico configurado.")

            subject = "Instrumento Calibrado"
            body = f"""<p>Le notificamos que su instrumento ha sido calibrado, su expediente es:  {rec.control_id.expediente.name}</p>"""

            mail_values = {
                'subject': subject,
                'body_html': body,
                'message_type': 'email',
                'email_to': email_to,
                'author_id': self.env.user.partner_id.id,
            }

            mail = rec.env['mail.mail'].sudo().create(mail_values)
            mail.send(auto_commit=True)

    @api.onchange('document')
    def _onchange_document(self):
        for rec in self:
            if self.document:
                email_to = rec.control_id.razon_social.email if rec.control_id.razon_social else None
                subject = "Documento de Calibración Disponible!"
                body = f"""<p>Informamos que se encuentra disponible el certificado de calibración correspondiente a su solicitud Nro. XXXXX. El mismo puede ser descargado del Portal del Cliente (colocar url aquí).

Solicitamos su amable colaboración a fin de responder la encuesta de satisfacción accediendo al siguiente link: Colocar url aquí.

Le saludamos cordialmente,

Instituto Nacional de Tecnología, Normalización y Metrología:  {self.control_id.expediente.name}</p>"""
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'message_type': 'email',
                    'email_to': email_to,
                    'author_id': self.env.user.partner_id.id,
                }

                mail = rec.env['mail.mail'].sudo().create(mail_values)
                mail.send(auto_commit=True)

    @api.depends('cantidad', 'cantidad_salida')
    def _compute_cantidad_faltante(self):
        for record in self:
            record.cantidad_faltante = record.cantidad - record.cantidad_salida


class ControlIngresoInstrumentosLineHistory(models.Model):
    _name = 'control.ingreso.instrumentos.line.history'
    _description = 'Historial de Salida'

    control_line = fields.Many2one('control.ingreso.instrumentos.line', string='Control Línea')
    item = fields.Integer(string='Ítem', related='control_line.item', readonly=True)
    cantidad = fields.Integer(string='Cantidad Ingreso', related='control_line.cantidad', readonly=True)
    cantidad_faltante = fields.Integer(string='Cantidad Faltante')
    cantidad_salida = fields.Integer(string='Cantidad Salida')
    instrumento = fields.Many2one('instrument.inventory.metci', string='Instrumento',
                                  related='control_line.instrumento', readonly=True)
    identificacion = fields.Char(related='instrumento.unique_identifier', string='Identificación')
    control_history_id = fields.Many2one('control.ingreso.instrumentos', string='Control de Ingreso',
                                         related='control_line.control_id', readonly=True)
    date = fields.Datetime(string="Fecha de Actualización", default=fields.Datetime.now, readonly=True)


class InstrumentInventory(models.Model):
    _name = 'instrument.inventory.metci'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Inventario de Instrumentos'

    name = fields.Char(string='Nombre del Instrumento')
    marca_id = fields.Many2one('instrument.brand', string='Marca')
    modelo_id = fields.Many2one('instrument.model', string='Modelo', domain="[('brand_id', '=', marca_id)]")
    serie = fields.Char(string='Número de Serie')
    rango = fields.Char(string='Rango ó Capacidad máxima')
    division = fields.Float(string='División ó Resolución')
    client_identifier = fields.Char(string='Identificador Cliente', copy=False)
    unique_identifier = fields.Char(string='Identificador Único', readonly=True, copy=False,
                                    default=lambda self: self.env['ir.sequence'].next_by_code('instrument.inventory'))


class InstrumentBrand(models.Model):
    _name = 'instrument.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Marca de Instrumento'

    name = fields.Char(string="Nombre de la Marca", required=True)
    description = fields.Text(string="Descripción")


class InstrumentModel(models.Model):
    _name = 'instrument.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Modelo de Instrumento'

    name = fields.Char(string="Nombre del Modelo", required=True)
    brand_id = fields.Many2one('instrument.brand', string="Marca", required=True)  # Relación con la marca
    description = fields.Text(string="Descripción")
