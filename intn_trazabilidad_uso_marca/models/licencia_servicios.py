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


class LicenciaServicios(models.Model):
    _name = 'licencia.servicios'
    _description = "Licencia de Servicios"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    fecha= fields.Date(string="Fecha", required=True, default=fields.Date.today,
                                   track_visibility='onchange')
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True, default=fields.Date.today,
                            track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Expediente N°', required=False, track_visibility='onchange')

    solicitante_id = fields.Many2one('res.partner', 'Solicitante', required="True", track_visibility='onchange')
    ruc = fields.Char('RUC', related="solicitante_id.vat", track_visibility='onchange')
    street= fields.Char('Calle', related="solicitante_id.street",track_visibility='onchange')
    city_id = fields.Many2one('res.country.state.city', string="Ciudad", related="solicitante_id.city_id",track_visibility='onchange')
    state_id = fields.Many2one('res.country.state', string="Departamento", related="solicitante_id.state_id",track_visibility='onchange')
    country_id = fields.Many2one('res.country', string="País", related="solicitante_id.country_id",track_visibility='onchange')

    des_servicio_1 = fields.Html(string="Texto 1", default='ENSAMBLADO DE EXTINTORES PORTATILES DE INCENDIO CON AGENTE')
    des_servicio_2 = fields.Html(string="Texto 1", default='VERIFICACIÓN, MANTENIMIENTO Y RECARGA DE EXTINTORES PORTATILES DE INCENDIO CON AGENTE')
    marca_1 = fields.Many2one('marca.producto', string="Marca",track_visibility='onchange', related="solicitante_id.marca_id")
    marca_2 = fields.Many2one('marca.producto', string="Marca",track_visibility='onchange', related="solicitante_id.marca_id")
    agentes_1 = fields.Many2many('product.product','relation_table_one', 'licencia_id','agente_id', string="Agentes",track_visibility='onchange')
    agentes_2 = fields.Many2many('product.product', 'relation_table_dos', 'licencia_id','agente_id',string="Agentes",track_visibility='onchange')
    norma_ids = fields.Many2many('normas.licencia', string="Normas",track_visibility='onchange')
    reglamento_general_id = fields.Many2one('reglamentos.licencia', string="Reglamento General",track_visibility='onchange')
    reglamentos_especificos_ids = fields.Many2many('reglamentos.licencia', string="Reglamentos Específicos",track_visibility='onchange')

    user_id = fields.Many2one(
        'res.users', string="Técnico Responsable", required=True, default=lambda self: self.env.user)
    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado'),('vencido','Vencido')], default='draft', track_visibility='onchange')

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company'])
    qr_code = fields.Binary(string="QR Code", compute="generate_qr_code")

    fecha_letras = fields.Char(compute='_fechaLetras')

    fecha_vencimiento_letras = fields.Char(compute='_fechaVenicimientoLetras')

    qr_code_public = fields.Char(string="QR Code Public", compute="generate_qr_code_public")

    nro_hoja_seguridad = fields.Char(string="N° de hoja de seguridad", track_visibility='onchange')
    nro_sello = fields.Char(string="N° de sello", track_visibility='onchange')

    #product_id = fields.Many2one('product.template', string="Producto", required=True)

    def _default_access_token(self):
        return uuid.uuid4().hex

    access_url = fields.Char('URL del portal de cliente', compute="_compute_access_url")
    access_token = fields.Char('Token de seguridad', default=_default_access_token)

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Licencia de Servicios', self.name)

    def _compute_access_url(self):
        # super(SolicitudesServicio, self)._compute_access_url()
        for verificacion in self:
            verificacion.access_url = '/my/licencia-servicios/%s' % (verificacion.id)

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


    @api.onchange('reglamento_general_id')
    @api.depends('reglamento_general_id')
    def onchangeReglamentoGeneral(self):
        for this in self:
            if this.reglamento_general_id:
                rg = this.reglamento_general_id.reglamentos_especificos_ids
                this.update({'reglamentos_especificos_ids':rg})
                normas = this.reglamento_general_id.mapped('reglamentos_especificos_ids.normas_ids')
                this.update({'norma_ids':normas})

    @api.multi
    def button_print(self):
        return self.env.ref('intn_trazabilidad_uso_marca.reporte_licencia_servicios').report_action(self)

    def genera_token(self, id_factura):
        palabra = id_factura + "amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra, 'utf-8')).hexdigest()

    def generate_qr_code(self):
        for i in self:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            route = "/licencia_servicios_check?licencia_servicios_id=" + \
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


    def generate_qr_code_public(self):
        for i in self:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            route = "/serviciospc/" + \
                    str(i.id) + "/" + i.genera_token(str(i.id))[0:10]
            url = base_url + route
            i.qr_code_public = url

    def button_confirmar(self):
        for this in self:
            #seq = self.env['ir.sequence'].sudo().next_by_code('seq_licencia_servicios')
            if not this.solicitante_id.cod_uso_marca:
                raise exceptions.ValidationError(
                    "Debe asignar un código al solicitante antes de confirmar la Licencia.")
            #if not this.product_id or not this.product_id.cod_licencia:
            #    raise exceptions.ValidationError(
            #        "Debe asignar un código al producto antes de confirmar la Licencia.")
            this.write({'name': '400S - '+str(this.solicitante_id.cod_uso_marca)})
            this.write({'state': 'done'})
            reg = {
                'res_id': self.id,
                'res_model': 'licencia.servicios',
                'partner_id': self.solicitante_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)
            this.solicitante_id.sudo().write({'state_uso_marca':'habilitado'})

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})
            this.solicitante_id.state_uso_marca = 'cancelado'
            #this.solicitante_id.write({'state_uso_marca': 'cancelado'})


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

    def _fechaVenicimientoLetras(self):
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
                fecha_vencimiento_letras = this.fecha_vencimiento.strftime("%d de __mes__ de %Y")
                fecha_vencimiento_letras = fecha_vencimiento_letras.replace('__mes__',
                                                                            meses[this.fecha_vencimiento.month - 1])
                this.fecha_vencimiento_letras = fecha_vencimiento_letras
            else:
                this.fecha_vencimiento = this.fecha_vencimiento

    def unlink(self):
        raise exceptions.ValidationError(
            "No se pueden eliminar licencias, sólo cancelarlas.")

    @api.model
    def getVencimientos(self):
        today = datetime.date.today()
        confirmados = self.env['licencia.servicios'].search([('state', '=', 'done')])
        if confirmados:
            vencidos = confirmados.filtered(lambda x: today >= x.fecha_vencimiento)
            if vencidos:
                for v in vencidos:
                    licencia_vigente = confirmados.filtered(lambda x: today >= x.fecha_vencimiento and x.partner_id == v.partner_id)
                    if not licencia_vigente:
                        v.solicitante_id.write({'state_uso_marca': 'vencido'})
                        v.write({'state': 'vencido'})
