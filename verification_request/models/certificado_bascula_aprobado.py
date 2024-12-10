# -*- coding: utf-8 -*-
import datetime

from odoo import fields, models, api, _
import base64


class CertificadoBasculaAprobado(models.Model):
    _name = "certificado.bascula.aprobado"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    verification_service_id = fields.Many2one('verification.request', string="SV vinculado")
    verification_service_name = fields.Char(
        string="Nombre de la solicitud vinculada",
        related='verification_service_id.name',
        store=True,
        readonly=True
    )
    # Relación con Excentricidad
    excentricidad_ids = fields.One2many(
        'excentricidad',
        'request_id',
        string="Excentricidad",
    )

    desempeno_carga_ids = fields.One2many(
        'desempeno.carga',
        'request_id',
        string="Desempeño de Carga"
    )

    repetitibilidad_id = fields.One2many(
        'repetitibilidad',
        'request_id',
        string="Repetitibilidad"
    )
    tipo_instrumento = fields.Char(string="Tipo  de instrumento")
    fabricante = fields.Char(string='Fabricante')
    modelo = fields.Char(string='Modelo')
    nro_serie = fields.Char(string='Nro de Serie')
    identificacion = fields.Char(string='Identificacion')
    ubicacion = fields.Char(string='Ubicacion')
    nro_expediente = fields.Char(string='Expediente')
    date = fields.Datetime(string="Fecha de verificacion", tracking=True)
    marca = fields.Char(string='Marca')
    carga_maxima = fields.Char(string='Carga Maxima')
    destinado = fields.Char(string='Destrinado a')
    tipo_bascula = fields.Char(string='Tipo Bascula')
    division1 = fields.Char(string='Division e1')
    division2 = fields.Char(string='Division e2')
    rango_minimo = fields.Char(string='Rango Minimo')
    rango_maximo = fields.Char(string='Rango Maximo')
    visualizacion = fields.Char(string='Visualizacoin del Instrumento')
    excentricidad = fields.Char(string='Excentricidad')
    mep_excentricidad = fields.Char(string='MEP Excentricidad')
    discriminacion = fields.Char(string='Discriminacion')
    mep_discriminacion = fields.Char(string='MEP Discriminacion')
    desempenho_carga = fields.Char(string='Desempeño de Carga')
    mep_desempenho_carga = fields.Char(string='MEP Carga')
    clase = fields.Char('Clase')
    tecnico1 = fields.Char(string='Tecnico Responsable')
    tecnico2 = fields.Char(string='Tecnico Conductor')
    cedula_tecnico1 = fields.Char(string='Cédula Técnico Responsable')
    cedula_tecnico2 = fields.Char(string='Cédula Técnico Responsable')

    cliente_responsable = fields.Char(string='Operador de bascula cliente')
    ci_cliente_responsable = fields.Char(string='Cedula Operado Cliente')
    marca_verificacion = fields.Char(string='Marca Verificacion')
    resultado = fields.Char(string='Estado recibido desde la app')
    cliente = fields.Many2one('res.partner', string='Cliente')
    cliente_direccion = fields.Char(string='Direccion cliente Certificado')
    cliente_ruc = fields.Char(string='Ruc Cliente Certificado')
    cliente_ciudad = fields.Char(string='Ciudad Cliente Certificado')
    observation = fields.Char(string='Observacion')
    year = fields.Char(string='Year Certificado', compute='_get_year_system')
    result_desempenoCarga = fields.Boolean(string='Resultado de Desempenho de carga')
    result_excentricidad = fields.Boolean(string='Resultado de Excentricidad')
    result_repetitibilidad = fields.Boolean(string='Resultado de Repetitibilidad')

    def _get_year_system(self):
        current_year = datetime.datetime.now().year
        for record in self:
            record.year = str(current_year)

    def imprimir_certificado(self):
        record = self.env['certificado.bascula.aprobado'].browse(9)
        print(record.name)  # Asumiendo que existe el campo 'name'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.certificado.bascula.aprobado') or 'New'
        return super(CertificadoBasculaAprobado, self).create(vals)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Certificado Bascula Aprobado', self.name)

    def send_impossibility_act(self):
        self.ensure_one()

        report = self.env.ref('verification_request.action_report_certificado_aprobado')
        pdf, _ = report._render_qweb_pdf(self.id)
        pdf_name = 'action_report_certificado_aprobado.pdf'

        # Codificar en base64 el PDF
        pdf_encoded = base64.b64encode(pdf).decode('utf-8')

        attachment_file = {
            'name': pdf_name,
            'datas': pdf_encoded,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        }
        attachment_id = self.env['ir.attachment'].create(attachment_file)

        email_vals = {
            'subject': 'Certificado de Bascula Aprobado',
            'body_html': '<p>Por el presente, se adjunta el certificado aprobado de ejecución de la verificación de Bascula.</p>',
            'email_to': self.verification_service_id.email,
            'attachment_ids': [(6, 0, [attachment_id.id])],
        }
        email = self.env['mail.mail'].create(email_vals)
        email.send()

        self.message_post(
            body="Se ha enviado un Certificado Aprobado.",
            subject="Certificado de Aprobacion de Bascula",
            message_type='notification',
            subtype_id=self.env.ref('mail.mt_note').id,
            attachments=[(attachment_id.name, attachment_id.datas)],
        )
