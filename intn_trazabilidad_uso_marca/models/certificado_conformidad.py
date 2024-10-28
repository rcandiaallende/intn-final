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


class FabricanteProducto(models.Model):
    _name = 'fabricante.producto'
    _description = "Fabricantes de Productos"
    _order = 'name desc'

    name = fields.Char('Nombre', copy=False,required=True, track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')


class MarcaProducto(models.Model):
    _name = 'marca.producto'
    _description = "Marcas de Productos"
    _order = 'name desc'

    name = fields.Char('Nombre', copy=False,required=True, track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')


class CertificadoConformidad(models.Model):
    _name = 'certificado.conformidad'
    _description = "Certificado de Conformidad de Lotes de Productos"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'


    fecha= fields.Date(string="Fecha", required=True, default=fields.Date.today,
                                   track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')



    descripcion1 = fields.Html('Descripcion 1',
    default='El Organismo Nacional de Certificación del INTN, <b>CERTIFICA</b> que el producto que se detalla a '
            'continuación, cumple con los requisitos establecidos en:')


    ########### PRODUCTO
    product_id = fields.Many2one('product.product',string='Descripción', required=True,track_visibility='onchange')
    identificacion_lote = fields.Char('Identificación del Lote', required=True,track_visibility='onchange')
    tam_lote = fields.Char('Tamaño del Lote', required=True, track_visibility='onchange')
    tamaño_lote_kg = fields.Integer('Tamaño del lote en Kg', required=True)
    tamaño_lote_restante_real = fields.Integer('Tamaño del lote restante real', required=True)
    tamaño_lote_restante_aproximado = fields.Integer('Tamaño del lote restante aproximado', required=True)
    modelo =fields.Char('Modelo', required=False, track_visibility='onchange')
    fabricante_id = fields.Many2one('fabricante.producto', string="Fabricante", track_visibility='onchange')
    marca_id = fields.Many2one('marca.producto', string="Marca", track_visibility='onchange')
    origen = fields.Many2one('res.country', string="Origen", track_visibility='onchange')
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=False,
                                   track_visibility='onchange')


    ########### INFORMES RELACIONADOS
    acta_id = fields.Many2one('acta.extraccion',string='Acta de Extracción de Muestras', track_visibility='onchange', required=False)
    informes_ensayo = fields.Char('Informes de Ensayo', track_visibility='onchange')

    ########### SOLICITANTE
    solicitante_id = fields.Many2one('res.partner', 'Solicitante', required="True", track_visibility='onchange')
    ruc = fields.Char('RUC', related="solicitante_id.vat", track_visibility='onchange')
    street= fields.Char('Calle', related="solicitante_id.street",track_visibility='onchange')
    city_id = fields.Many2one('res.country.state.city', string="Ciudad", related="solicitante_id.city_id",track_visibility='onchange')
    state_id = fields.Many2one('res.country.state', string="Departamento", related="solicitante_id.state_id",track_visibility='onchange')
    country_id = fields.Many2one('res.country', string="País", related="solicitante_id.country_id",track_visibility='onchange')
    order_id = fields.Many2one('sale.order', string='Expediente N°', required=False, track_visibility='onchange')

    observaciones = fields.Html('Observaciones', track_visibility='onchange')

    user_id = fields.Many2one(
        'res.users', string="Técnico Responsable", required=True, default=lambda self: self.env.user)
    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado')], default='draft', track_visibility='onchange')

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company'])
    qr_code = fields.Binary(string="QR Code", compute="generate_qr_code")

    fecha_letras = fields.Char(compute='_fechaLetras')

    periodo_validez = fields.Char(string="Periodo de Validez", default="seis (6) meses", track_visibility='onchange')

    nro_hoja_seguridad = fields.Char(string="N° de hoja de seguridad", track_visibility='onchange')
    nro_sello = fields.Char(string="N° de sello", track_visibility='onchange')

    @api.depends('product_id')
    @api.onchange('product_id')
    def onchangeProduct(self):
        for this in self:
            if this.product_id:
                this.observaciones = this.product_id.observaciones_certificado

    def _default_access_token(self):
        return uuid.uuid4().hex

    access_url = fields.Char('URL del portal de cliente', compute="_compute_access_url")
    access_token = fields.Char('Token de seguridad', default=_default_access_token)

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Certificado de Conformidad', self.name)

    def _compute_access_url(self):
        # super(SolicitudesServicio, self)._compute_access_url()
        for verificacion in self:
            verificacion.access_url = '/my/certificado-conformidad/%s' % (verificacion.id)

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

    @api.multi
    def button_print(self):
        return self.env.ref('intn_trazabilidad_uso_marca.reporte_certificado_conformidad').report_action(self)


    def genera_token(self, id_factura):
        palabra = id_factura + "amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra, 'utf-8')).hexdigest()

    def generate_qr_code(self):
        for i in self:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            route = "/certificado_conformidad_check?certificado_conformidad_id=" + \
                    str(i.id) + "&token=" + i.genera_token(str(i.id))
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=2,
                border=1,
            )
            qr.add_data("%s%s" % (base_url, route))
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            i.qr_code = qr_image
            
    def unlink(self):
        raise exceptions.ValidationError(
            "No se pueden eliminar Certificados de Conformidad, sólo cancelarlos.")
    
    def button_confirmar(self):
        for this in self:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_certificado_conformidad')
            this.write({'name': seq})
            this.write({'state': 'done'})
            reg = {
                'res_id': self.id,
                'res_model': 'certificado.conformidad',
                'partner_id': self.solicitante_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})


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
