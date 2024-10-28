from odoo import fields, api, models, exceptions
import qrcode
import base64
import hashlib
from io import BytesIO
from odoo.exceptions import ValidationError
import datetime

import dateutil
from dateutil.relativedelta import relativedelta
import uuid


class NotaRechazo(models.Model):
    _name = 'intn_trazabilidad_uso_marca.nota_rechazo'
    _description = "Notas de Rechazo"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    fecha= fields.Date(string="Fecha", required=True, default=fields.Date.today,
                                   track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Expediente N°', required=False, track_visibility='onchange')

    partner_id = fields.Many2one('res.partner', 'Cliente', required="True", track_visibility='onchange')

    nota = fields.Html(string="Nota", default='Tengo el agrado de dirigirme a Ustedes en referencia a la solicitud de certificación'
                                              'por lote productos según expediente ..., y para su producto ... ')

    user_id = fields.Many2one(
        'res.users', string="Técnico Responsable", required=True, default=lambda self: self.env.user)
    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado')], default='draft', track_visibility='onchange')

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company'])
    qr_code = fields.Binary(string="QR Code", compute="generate_qr_code")

    fecha_letras = fields.Char(compute='_fechaLetras')


    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Nota de Rechazo', self.name)

    def _compute_access_url(self):
        # super(SolicitudesServicio, self)._compute_access_url()
        for nota in self:
            nota.access_url = '/my/nota-rechazo/%s' % (nota.id)

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    @api.multi
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

    def genera_token(self, id_factura):
        palabra = id_factura + "amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra, 'utf-8')).hexdigest()

    def generate_qr_code(self):
        for i in self:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            route = "/nota_rechazo_check?nota_rechazo_id=" + \
                    str(i.id) + "&token=" + i.genera_token(str(i.id))
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data("%s%s" % (base_url, route))
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            i.qr_code = qr_image


    def button_confirmar(self):
        for this in self:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_nota_rechazo')
            this.write({'name':seq})
            this.write({'state': 'done'})
            reg = {
                'res_id': self.id,
                'res_model': 'intn_trazabilidad_uso_marca.nota_rechazo',
                'partner_id': self.partner_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})
            #this.solicitante_id.write({'state_uso_marca': 'cancelado'})

    def unlink(self):
        raise exceptions.ValidationError(
            "No se pueden eliminar notas de rechazo, sólo cancelarlas.")

    def _fechaLetras(self):
        meses = [
            'Enero',
            'Febrero',
            'Marzo',
            'Abril',
            'Mayo',
            'Junio',
            'Julio',
            'Agosto',
            'Setiembre',
            'Octubre',
            'Noviembre',
            'Diciembre',
        ]
        for this in self:
            if this.fecha:
                fecha_letras = this.fecha.strftime("%d de __mes__ de %Y")
                fecha_letras = fecha_letras.replace('__mes__', meses[this.fecha.month - 1])
                this.fecha_letras = fecha_letras
            else:
                this.fecha_letras = this.fecha

