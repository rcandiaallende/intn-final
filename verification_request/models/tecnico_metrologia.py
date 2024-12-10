from odoo import models, fields, api

import qrcode
import base64
from io import BytesIO


class TecnicoMetrologia(models.Model):
    _name = 'tecnico.metrologia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Configurar Técnicos Metrología'

    usuario = fields.Many2one('res.users', string='Usuario Técnico', required=True)
    activo = fields.Boolean(string='Activo', default=True)
    date_inicio = fields.Date(string='Fecha de Inicio', required=True)
    date_final = fields.Date(string='Fecha de Finalización', required=False)
    log_cambios = fields.Text(string="Registro de Cambios")
    _log_access = True
    token_firma = fields.Char(string="Token de Firma", copy=False)
    qr_firma = fields.Binary(string="Código QR de Firma", attachment=True, readonly=True)
    cedula = fields.Char(string='Cedula de Identidad')
    qr_url_firma_intn = fields.Char(string="Url firma INTN interno", copy=False)
    qr_firma_intn = fields.Binary(string="QR de Firma INTN", attachment=True, readonly=True)

    @api.model
    def create(self, vals):
        # Generar un token único al crear un registro
        vals['token_firma'] = self.env['ir.sequence'].next_by_code('tecnico.metrologia.token') or '/'
        record = super(TecnicoMetrologia, self).create(vals)
        record._generate_qr_firma()
        return record

    @api.onchange('token_firma')
    def _onchange_token_firma(self):
        # Generar el código QR cada vez que el token cambie
        if self.token_firma:
            self._generate_qr_firma()

    @api.onchange('qr_url_firma_intn')
    def _onchange_token_firma_intn(self):
        # Generar el código QR cada vez que el token cambie
        if self.qr_url_firma_intn:
            self._generate_qr_firma()

    def _generate_qr_firma(self):
        # Generar el código QR basado en el token
        for record in self:
            if record.token_firma:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                qr.add_data(record.token_firma)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_image = base64.b64encode(buffer.getvalue())
                record.qr_firma = qr_image
            elif record.qr_url_firma_intn:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                qr.add_data(record.qr_url_firma_intn)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_image = base64.b64encode(buffer.getvalue())
                record.qr_url_firma_intn = qr_image

    def write(self, vals):
        # Si el token_firma se modifica, actualizamos el QR
        if 'token_firma' in vals:
            self._generate_qr_firma()
        return super(TecnicoMetrologia, self).write(vals)





