# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import base64


class CertificadoBasculaNoAprobado(models.Model):
    _name = "certificado.bascula.no.aprobado"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string='Móvil', required=True, copy=False,
                       default=lambda self: 'New')
    active = fields.Boolean('Active', default=True, tracking=True)
    verification_service_id = fields.Many2one('verification.request', string="SV vinculado", tracking=True)
    date = fields.Datetime(string="Fecha del acta", tracking=True)
    reason_selection = fields.Selection([
        ('climatic_conditions', 'Condiciones climáticas'),
        ('instrument_fault', 'Desperfecto del Instrumento'),
        ('repair', 'Por reparación'),
        ('closure', 'Por cierre del establecimiento'),
        ('owner_impediment', 'Impedimento del propietario o encargado'),
        ('mobile_fault', 'Desperfecto del móvil metrológico'),
        ('other', 'Otros..............')
    ], string='Motivo')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.certificado.bascula.no.aprobado') or 'New'
        return super(CertificadoBasculaNoAprobado, self).create(vals)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Certificado Bascula No Aprobado', self.name)

    def send_impossibility_act(self):
        self.ensure_one()

        report = self.env.ref('verification_request.action_report_certificado_no_aprobado')
        pdf, _ = report._render_qweb_pdf(self.id)
        pdf_name = 'action_report_certificado_no_aprobado.pdf'

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
            'subject': 'Certificado de Bascula No Aprobado',
            'body_html': '<p>Por el presente, se adjunta el certificado NO aprobado de ejecución de la verificación de Bascula.</p>',
            'email_to': self.verification_service_id.email,
            'attachment_ids': [(6, 0, [attachment_id.id])],
        }
        email = self.env['mail.mail'].create(email_vals)
        email.send()

        self.message_post(
            body="Se ha enviado un Certificado No Aprobado.",
            subject="Certificado de No Aprobacion de Bascula",
            message_type='notification',
            subtype_id=self.env.ref('mail.mt_note').id,
            attachments=[(attachment_id.name, attachment_id.datas)],
        )
