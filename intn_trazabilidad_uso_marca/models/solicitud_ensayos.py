from odoo import fields, api, models, exceptions


class SolicitudEnsayosLines(models.Model):
    _name = 'solicitud.ensayos.lines'
    _description = "Lineas de Solicitud de Ensayos"

    solicitud_ensayo_id = fields.Many2one('solicitud.ensayos', string="Solicitud de Ensayo", required=False)
    cantidad = fields.Char('Cantidad muestra/s', copy=False, required=True, track_visibility='onchange')
    identificacion_muestra = fields.Char('Identificación muestra/s', copy=False, required=True, track_visibility='onchange')
    descripcion_muestra = fields.Text('Descripción muestra/s', copy=False, required=True, track_visibility='onchange')
    determinacion_ids = fields.Many2many('intn_trazabilidad_uso_marca.determinacion_productos','solicitud_ensayo_line_id',
                                         string="Determinación")

    @api.onchange('solicitud_ensayo_id','solicitud_ensayo_id.product_id')
    @api.depends('solicitud_ensayo_id','solicitud_ensayo_id.product_id')
    def onchangeDeterminacion(self):
        for this in self:
            if this.solicitud_ensayo_id and this.solicitud_ensayo_id.product_id:
                if this.solicitud_ensayo_id.product_id.determinacion_ids:
                    this.determinacion_ids = this.solicitud_ensayo_id.product_id.determinacion_ids.sorted(key=lambda x: x.sequence)



class SolicitudEnsayos(models.Model):
    _name = 'solicitud.ensayos'
    _description = "Solicitud de Ensayos"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'


    organismo_id = fields.Many2one('intn.organismos', string="Sr/Sres", required=True)
    product_id = fields.Many2one('product.template','Producto', required=True, track_visibility='onchange')
    lote = fields.Char("Lote N°", required=True, track_visibility='onchange')


    fecha_solicitud = fields.Date('Fecha de Solicitud',  default=fields.Date.today,track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    observaciones = fields.Html('Observaciones')


    line_ids = fields.One2many('solicitud.ensayos.lines', 'solicitud_ensayo_id', string="Lineas", required=True)

    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado')], default='draft', track_visibility='onchange')


    def button_confirmar(self):
        for this in self:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_solicitud_ensayos')
            this.write({'name': seq})
            this.write({'state': 'done'})

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})
