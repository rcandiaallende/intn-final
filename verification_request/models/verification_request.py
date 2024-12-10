# -- coding: utf-8 --
import uuid

from odoo import fields, models, api, _
from datetime import date, datetime
import calendar
from odoo.exceptions import UserError, _logger
import json


class VerificationRequest(models.Model):
    _name = "verification.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Verification Request code', required=True, copy=False, readonly=True,
                       default=lambda self: 'New')
    partner_id = fields.Many2one(comodel_name='res.partner', required=True, tracking=True,
                                 states={'pending': [('readonly', False)]},
                                 string='Cliente')
    state = fields.Selection(selection=[('pending', 'Pendiente'), ('programmed', 'Programado'),
                                        ('verified', 'Verificado'), ('duplicate', 'Duplicado'),
                                        ('cancel', 'Cancelado'), ('canceled_due_closure', 'Cancelado por cierre'),
                                        ('impossibility', 'Imposibilidad'), ],
                             string='Estado',
                             default='pending')

    designation = fields.Many2many('res.users', string='Designación', domain="[('id', 'in', active_tecnico_ids)]")
    email = fields.Char(related='partner_id.email', string='Correo', readonly=False)
    phone = fields.Char(related='partner_id.phone', string='Teléfono', readonly=False)
    country = fields.Many2one(related='partner_id.country_id', readonly=False)
    vat = fields.Char(related='partner_id.vat', string='RUC', readonly=False)
    country_state = fields.Many2one('res.country.state', string='Departamento', readonly=False,
                                    domain="[('country_id', '=', 185)]")
    city = fields.Char(related='partner_id.city_id.name', string='Ciudad', readonly=False)
    street = fields.Char(related='partner_id.street', string='Dirección', readonly=False)
    request_type = fields.Selection(
        [('email', 'Correo'), ('historic', 'Histórico'), ('personal', 'Personalmente')], string="Solicitud",
        default="email")
    verification_service = fields.Selection(
        [('periodic', 'VERIFICACIÓN PERIODICA'), ('complementary', 'VERIFICACIÓN COMPLEMENTARIA')], string="Servicio",
        default="periodic")
    instrument = fields.Many2one('instrument', string="Intrumento", states={'pending': [('readonly', False)]})
    instrument_type = fields.Selection(related='instrument.type', string="Tipo instrumento")
    mobile = fields.Many2one('mobile', string="Móvil", states={'pending': [('readonly', False)]})
    impossibility_act = fields.Many2one('impossibility.act', string="Acta imposibilidad")
    static_bascula = fields.Many2one('app.basculas', string="Báscula estática",
                                     states={'pending': [('readonly', False)]})
    dynamic_bascula = fields.Many2one('registro.medicion.basculas', string="Báscula dinámica",
                                      states={'pending': [('readonly', False)]})
    active_tecnico_ids = fields.Many2many(
        'res.users',
        compute='_compute_active_tecnico_ids',
        store=False  # No necesitamos almacenar este campo
    )
    week_number = fields.Integer(string='Número de la Semana', compute='_compute_week_number')
    state_id = fields.Many2many('res.country.state', string="Departamentos")
    month = fields.Selection(
        [
            ('january', 'Enero'),
            ('february', 'Febrero'),
            ('march', 'Marzo'),
            ('april', 'Abril'),
            ('may', 'Mayo'),
            ('june', 'Junio'),
            ('july', 'Julio'),
            ('august', 'Agosto'),
            ('september', 'Septiembre'),
            ('october', 'Octubre'),
            ('november', 'Noviembre'),
            ('december', 'Diciembre'),
        ],
        string="Mes",
    )
    observation = fields.Text(string="Observaciones")


    expediente = fields.Char(string='Expediente')

    def search_tecnico_ci(self, id_tecnico):
        tecnico = self.env['tecnico.metrologia'].search([('usuario', '=', id_tecnico)], limit=1)
        if tecnico:
            return tecnico.cedula
        return None

    def verificar_app(self):  # Método público
        for rec in self:
            if rec.state == 'programmed' and not rec.dynamic_bascula:
                # Buscar la bascula relacionada con el id_planificacion
                bascula = self.env['app.basculas'].search([('id_planificacion', '=', rec.name)], limit=1)
                if bascula:
                    # Actualizar el campo 'procesado' de 'app.basculas' a True
                    bascula.update({'procesado': True})
                    # Obtener el campo 'data_receive' que contiene el JSON
                    json_app = bascula.data_receive
                    self.procces_data_app(json_app)
                    if bascula.imposibility == True:
                        resultado = 'imposibilidad'
                        rec.state = 'impossibility'



    def procces_data_app(self, json_app):
        for rec in self:
            # Si el campo data_receive es un string JSON, lo convertimos a un diccionario
            if isinstance(json_app, str):
                json_app = json.loads(json_app)

            # Obtener 'fechaCreacion' del objeto anidado 'ensayos'
            fecha_creacion = json_app.get('ensayos', {}).get('fechaCreacion', False)
            estados = json_app.get('estados', {})
            marca_verificacion = json_app.get('clientApproves', {}).get('marcaVerificacion', False)

            instrumento = json_app.get('ensayos', {}).get('instrumento', {})
            tipo_instrumento = instrumento.get('instrumento', '')
            fabricante = instrumento.get('fabricante', '')
            modelo = instrumento.get('modelo', '')
            nro_serie = instrumento.get('nSerie', '')
            ubicacion = instrumento.get('ubicado', '')
            destinado = ", ".join(instrumento.get('destinado', []))
            id_ultima_verificacion = rec.id
            codigo_interno = instrumento.get('codigoInterno', '')
            carga_maxima = instrumento.get('cargaMaximaInput', '')
            tipo_bascula = instrumento.get('tipoBalanza', '')
            division1 = instrumento.get('divisionInput', '')
            rango_minimo = instrumento.get('cargaMinima', '')
            rango_maximo = instrumento.get('maxPrimerRango', '')
            visualizacion = instrumento.get('visualizacionInstrumento', '')
            influencia_posicion_carga = json_app.get('ensayos', {}).get('influenciaPosicionCarga', [])
            desempeno_carga = json_app.get('ensayos', {}).get('desempenoCarga', [])
            repetitibilidad = json_app.get('ensayos', {}).get('repetibilidad', [])
            max_balanza_peso_sensible = max(
                (item.get("balanzaPesoSensible", 0) for item in desempeno_carga), default=0
            )
            c_exactitud = json_app["ensayos"]["instrumento"]["cExactitud"]
            id_tecnico1 = json_app["ensayos"]["instrumento"]["idResponsable"]["value"]
            if id_tecnico1:
                cedula_tecnico1 = self.search_tecnico_ci(id_tecnico1)
                name_tenico1 = json_app["ensayos"]["instrumento"]["idResponsable"]["label"]
            id_tecnico2 = json_app["ensayos"]["instrumento"]["idConductor"]["value"]
            if id_tecnico2:
                cedula_tecnico2 = self.search_tecnico_ci(id_tecnico2)
                name_tenico2 = json_app["ensayos"]["instrumento"]["idConductor"]["label"]
            ci_client = json_app["clientApproves"]["ciClient"]
            clientName = json_app["clientApproves"]["clientName"]
            observations = json_app.get("clientApproves", {}).get("obervations", "")
            observation = json_app.get("clientApproves", {}).get("observation", "")
            pre_carga_final = json_app.get("estados", {}).get("preCarga", False)
            excentricidad_final = json_app.get("estados", {}).get("influenciaPosicionCarga", False)
            repetibilidad_final = json_app.get("estados", {}).get("repetibilidad", False)
            desempeno_carga_final = json_app.get("estados", {}).get("desempenoCarga", False)

            concatenated_value = f"{observations}  - {observation}"

            print('cliente: ' + str(rec.partner_id) +
                  ' cliente_direccion: ' + str(rec.partner_id.street) +
                  ' cliente_ruc: ' + str(rec.partner_id.vat) +
                  ' cliente_ciudad: ' + str(rec.city) +
                  ' observation: ' + str(concatenated_value))

            # discriminacion es balanzaPesoSensible
            if any(estados.values()):
                resultado = 'aprobado'
                self.create_so()
                certificado_aprobado = self.env['certificado.bascula.aprobado'].create({
                    'verification_service_id': self.id,
                    'tipo_instrumento': tipo_instrumento,
                    'fabricante': fabricante,
                    'modelo': modelo,
                    'nro_serie': nro_serie,
                    'identificacion': codigo_interno,
                    'ubicacion': ubicacion,
                    'nro_expediente': rec.sale_order.name,
                    'date': fecha_creacion,
                    'marca': fabricante,
                    'carga_maxima': carga_maxima,
                    'destinado': destinado,
                    'tipo_bascula': tipo_bascula,
                    'division1': division1,
                    'division2': division1,
                    'rango_minimo': str(rango_minimo),
                    'rango_maximo': rango_maximo,
                    'visualizacion': visualizacion,
                    # 'excentricidad': resultado,
                    # 'mep_excentricidad': resultado,
                    'discriminacion': 'Es sensible a una carga de ',
                    'mep_discriminacion': max_balanza_peso_sensible,
                    'desempenho_carga': 'Maximo error encontrado',
                    'mep_desempenho_carga': max_balanza_peso_sensible,
                    'clase': c_exactitud,
                    'tenico1': name_tenico1,
                    'tecnico2': name_tenico2,
                    'cedula_tecnico1': cedula_tecnico1,
                    'cedula_tecnico2': cedula_tecnico2,
                    'cliente_responsable': ci_client,
                    'ci_cliente_responsable': clientName,
                    'marca_verificacion': marca_verificacion,
                    'resultado': resultado,
                    'cliente': rec.partner_id.id,
                    'cliente_direccion': str(rec.partner_id.street),
                    'cliente_ruc': str(rec.partner_id.vat),
                    'cliente_ciudad': str(rec.city),
                    'observation': concatenated_value,
                    'result_desempenoCarga': desempeno_carga_final,
                    'result_excentricidad': excentricidad_final,
                    'result_repetitibilidad': repetibilidad_final,
                })
                for idx, item in enumerate(desempeno_carga, start=1):
                    self.env['desempeno.carga'].create({
                        'request_id': certificado_aprobado.id,
                        'mep': item.get('mep', 0.0),
                        'emep': item.get('eMep', ''),
                        'respuesta': item.get('respuesta', ''),
                        'indicacion': item.get('indicacion', ''),
                        'cargaAplicada': item.get('cargaAplicada', ''),
                        'errorInstrumento': item.get('errorInstrumento', ''),
                        'balanzaPesoSensible': item.get('balanzaPesoSensible', ''),
                    })
                for idx, item in enumerate(influencia_posicion_carga, start=1):
                    self.env['excentricidad'].create({
                        'request_id': certificado_aprobado.id,
                        'mep': item.get('mep', 0.0),
                        'emep': item.get('eMep', ''),
                        'medio': item.get('medio', ''),
                        'punta1': item.get('punta1', ''),
                        'punta2': item.get('punta2', ''),
                        'direccion': item.get('direccion', ''),
                        'carga_aplicada': item.get('cargaAplicada', ''),
                        'error_instrumento': item.get('errorInstrumento', 0.0),
                    })

                for idx, item in enumerate(repetitibilidad, start=1):
                    self.env['repetitibilidad'].create({
                        'request_id': certificado_aprobado.id,
                        'indicacion': item.get('indicacion', 0.0),
                        'errorInstrumento': item.get('errorInstrumento', ''),
                        'mep': item.get('mep', ''),
                        'validacion': item.get('validacion', ''),
                        'repetitibilidadAl': item.get('repetibilidadAl', ''),
                    })

                    # Log para verificar que los datos se guardaron correctamente
                certificado_aprobado.message_post(
                    body=f"Se crearon {len(influencia_posicion_carga)} registros de excentricidad.")
                rec.state = 'verified'
            else:
                self.create_so()
                resultado = 'reprobado'
                certificado_aprobado = self.env['certificado.bascula.aprobado'].create({
                    'verification_service_id': self.id,
                    'tipo_instrumento': tipo_instrumento,
                    'fabricante': fabricante,
                    'modelo': modelo,
                    'nro_serie': nro_serie,
                    'identificacion': codigo_interno,
                    'ubicacion': ubicacion,
                    'nro_expediente': rec.sale_order.name,
                    'date': fecha_creacion,
                    'marca': fabricante,
                    'carga_maxima': carga_maxima,
                    'destinado': destinado,
                    'tipo_bascula': tipo_bascula,
                    'division1': division1,
                    'division2': division1,
                    'rango_minimo': str(rango_minimo),
                    'rango_maximo': rango_maximo,
                    'visualizacion': visualizacion,
                    # 'excentricidad': resultado,
                    # 'mep_excentricidad': resultado,
                    'discriminacion': 'Es sensible a una carga de ',
                    'mep_discriminacion': max_balanza_peso_sensible,
                    'desempenho_carga': 'Maximo error encontrado',
                    'mep_desempenho_carga': max_balanza_peso_sensible,
                    'clase': c_exactitud,
                    'tenico1': name_tenico1,
                    'tecnico2': name_tenico2,
                    'cedula_tecnico1': cedula_tecnico1,
                    'cedula_tecnico2': cedula_tecnico2,
                    'cliente_responsable': clientName,
                    'ci_cliente_responsable': ci_client,
                    'marca_verificacion': marca_verificacion,
                    'resultado': resultado,
                    'cliente': rec.partner_id.id,
                    'cliente_direccion': rec.partner_id.street,
                    'cliente_ruc': rec.partner_id.vat,
                    'cliente_ciudad': rec.city,
                    'observation': concatenated_value,
                    'result_desempenoCarga': desempeno_carga_final,
                    'result_excentricidad': excentricidad_final,
                    'result_repetitibilidad': repetibilidad_final,
                })

                for idx, item in enumerate(influencia_posicion_carga, start=1):
                    self.env['excentricidad'].create({
                        'request_id': certificado_aprobado.id,
                        'mep': item.get('mep', 0.0),
                        'emep': item.get('eMep', ''),
                        'medio': item.get('medio', ''),
                        'punta1': item.get('punta1', ''),
                        'punta2': item.get('punta2', ''),
                        'direccion': item.get('direccion', ''),
                        'carga_aplicada': item.get('cargaAplicada', ''),
                        'error_instrumento': item.get('errorInstrumento', 0.0),
                    })

                for idx, item in enumerate(desempeno_carga, start=1):
                    self.env['desempeno.carga'].create({
                        'request_id': certificado_aprobado.id,
                        'mep': item.get('mep', 0.0),
                        'emep': item.get('eMep', ''),
                        'respuesta': item.get('respuesta', ''),
                        'indicacion': item.get('indicacion', ''),
                        'cargaAplicada': item.get('cargaAplicada', ''),
                        'errorInstrumento': item.get('errorInstrumento', ''),
                        'balanzaPesoSensible': item.get('balanzaPesoSensible', ''),
                    })

                for idx, item in enumerate(repetitibilidad, start=1):
                    self.env['repetitibilidad'].create({
                        'request_id': certificado_aprobado.id,
                        'indicacion': item.get('indicacion', 0.0),
                        'errorInstrumento': item.get('errorInstrumento', ''),
                        'mep': item.get('mep', ''),
                        'validacion': item.get('validacion', ''),
                        'repetitibilidadAl': item.get('repetibilidadAl', ''),
                    })

                    # Log para verificar que los datos se guardaron correctamente
                certificado_aprobado.message_post(
                    body=f"Se crearon {len(influencia_posicion_carga)} registros de excentricidad.")
                last_scale_check = self.env['last.scale.check'].create({
                    'cliente_id': rec.partner_id.id,
                    'ultima_fecha_verificacion': fecha_creacion,
                    'resultado_ultima_verificacion': resultado,
                    'marca_verificacion': marca_verificacion,
                    'tipo_instrumento': tipo_instrumento,
                    'fabricante': fabricante,
                    'modelo': modelo,
                    'nro_serie': nro_serie,
                    'ubicacion': ubicacion,
                    'destinado': destinado,
                    'id_ultima_verificacion': id_ultima_verificacion,
                })
                rec.state = 'verified'
                return last_scale_check

    def print_certificado_bascula(self):
        # Obtener la referencia del reporte
        report_ref = self.env.ref('verification_request.action_report_certificado_aprobado')

        for record in self:

            certificado = self.env['certificado.bascula.aprobado'].search([
                ('verification_service_id', '=', record.id)
            ], limit=1)

            if not certificado:
                raise UserError(
                    f"No se encontró un certificado asociado al verification_service_id {record.id}.")

            # Generar el reporte para el certificado encontrado
            return report_ref.report_action(certificado)

    @api.depends('request_date2')
    def _compute_week_number(self):
        for record in self:
            if record.request_date2:
                date_obj = fields.Date.from_string(record.request_date2)
                day_of_week = date_obj.isoweekday()
                if day_of_week < 6:  # Solo de lunes a viernes
                    week_number = date_obj.isocalendar()[1]
                else:
                    week_number = 0
                record.week_number = week_number
            else:
                record.week_number = 0

    @api.constrains('request_date2')
    def _check_weekday(self):
        for record in self:
            if record.request_date2:
                date_obj = fields.Date.from_string(record.request_date2)
                day_of_week = date_obj.isoweekday()
                if day_of_week in [6, 7]:
                    raise UserError(
                        "La fecha programada no puede ser un sábado ni un domingo. Por favor, selecciona otro día.")

    @api.depends('designation')
    def _compute_active_tecnico_ids(self):
        for record in self:
            # Obtener los usuarios técnicos activos
            active_tecnicos = self.env['tecnico.metrologia'].search([('activo', '=', True)])
            record.active_tecnico_ids = active_tecnicos.mapped('usuario.id')

    # @api.onchange('static_bascula')
    # def _onchange_static_bascula(self):
    #     if self.static_bascula and self.static_bascula.imposibility:
    #         self.state = "impossibility"
    #         self.create_so()

    @api.model
    def _get_active_tecnico_ids(self):
        # Obtenemos los IDs de los usuarios activos del modelo tecnico.metrologia
        active_tecnicos = self.env['tecnico.metrologia'].search([('activo', '=', True)])
        return active_tecnicos.mapped('usuario.id')

    def _get_year_selection(self):
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(current_year, current_year + 10)]

    year_selection = fields.Selection(
        selection=lambda self: self._get_year_selection(),
        string="Año",
        default=lambda self: str(datetime.now().year),
    )

    def _get_month_selection(self):
        return [(f'{month:02}', month_name) for month, month_name in enumerate(calendar.month_name) if month > 0]

    month_selection = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Mes",
        default=lambda self: datetime.now().strftime('%m'),
    )
    request_date = fields.Date(string='Fecha solicitud', required=True, states={'pending': [('readonly', False)]})
    request_date2 = fields.Date(string='Fecha programada', states={'pending': [('readonly', False)]})
    quantity = fields.Integer(string='Cantidad', default=1)
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    observation = fields.Text(string='Observación', states={'pending': [('readonly', False)]})
    sale_order = fields.Many2one('sale.order', string='Expediente')

    compute_paid_state = fields.Boolean(string='Pagado?', compute='_compute_compute_paid_state', default=False)

    def generate_certificate(self):
        if self.static_bascula:
            raise UserError(self.static_bascula)
        else:
            for rec in self:
                registro_medicion = rec.env['registro.medicion.basculas'].sudo().create({
                    "name": rec.name,
                    "fecha_emision": fields.Date.today(),
                    "razon_social": rec.partner_id.id
                })
                rec.registo_medicion_bascula_id = registro_medicion.id
                rec.registo_medicion_bascula_id = registro_medicion.id

    @api.model
    def _compute_compute_paid_state(self):
        for record in self:
            if record.sale_order:
                invoices = record.sale_order.mapped('invoice_ids')
                for move_id in invoices:
                    if move_id.state == 'paid':
                        record.compute_paid_state = True
            else:
                record.compute_paid_state = False

    # @api.multi
    # def action_view_invoice(self):
    #     invoices = self.mapped('invoice_ids')
    #     action = self.env.ref('account.action_invoice_tree1').read()[0]
    #     if len(invoices) > 1:
    #         action['domain'] = [('id', 'in', invoices.ids)]
    #     elif len(invoices) == 1:
    #         form_view = [(self.env.ref('account.invoice_form').id, 'form')]
    #         if 'views' in action:
    #             action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
    #         else:
    #             action['views'] = form_view
    #         action['res_id'] = invoices.ids[0]
    #     else:
    #         action = {'type': 'ir.actions.act_window_close'}
    #     return action

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.state_id:
            self.country_state = self.partner_id.state_id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.verification.request') or 'New'
        return super(VerificationRequest, self).create(vals)

    def action_programmed(self):
        for rec in self:
            rec.state = "programmed"

    def action_verified(self):
        for rec in self:
            rec.state = "verified"
            rec.create_so()

    def action_impossibility(self):
        for rec in self:
            rec.state = "impossibility"
            rec.create_impossibility_act()

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_pending(self):
        for rec in self:
            rec.state = "pending"

    def create_so(self):
        for rec in self:
            sale_order = rec.env['sale.order'].sudo().create({
                "partner_id": rec.partner_id.id
            })
            rec.sale_order = sale_order.id
            rec.expediente = sale_order.name

    def create_impossibility_act(self):
        for rec in self:
            act_id = rec.env['impossibility.act'].sudo().create({
                "date": fields.Datetime.now(),
                "verification_service_id": rec.id
            })
            rec.impossibility_act = act_id.id

    def create_certificado_aprobado(self):
        for rec in self:
            act_id = rec.env['certificado.bascula.aprobado'].sudo().create({
                "date": fields.Datetime.now(),
                "verification_service_id": rec.id
            })
            return act_id

    def open_impossibility_act(self):
        self.ensure_one()
        if self.impossibility_act:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Acta Imposibilidad',
                'view_mode': 'form',
                'res_model': 'impossibility.act',
                'res_id': self.impossibility_act.id,
                'target': 'current',
            }
        else:
            raise UserError("No hay registro relacionado para abrir.")

    def _default_access_token(self):
        return uuid.uuid4().hex

    # @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Solicitud de Verificacion', self.name)

    access_url = fields.Char('URL del portal de cliente', compute="_compute_access_url")
    access_token = fields.Char('Token de seguridad', default=_default_access_token)

    def _compute_access_url(self):
        for request in self:
            request.access_url = '/my/verification_request/%s' % request.id

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    # @api.multi
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        self.ensure_one()
        url = self.access_url + '%s?access_token=%s%s%s%s%s' % (
            suffix if suffix else '',
            self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            '#%s' % anchor if anchor else ''
        )
        return url

    @staticmethod
    def get_state_icon(state):
        states = {'pending': 'fa fa-clock-o', 'programmed': 'fa fa-calendar-check-o',
                  'verified': 'fa fa-check-square', 'cancel': 'fa fa-ban', 'impossibility': 'fa fa-exclamation-circle',
                  'duplicate': 'fa fa-files-o', 'canceled_due_closure': 'fa fa-ban'}
        return states[state]
