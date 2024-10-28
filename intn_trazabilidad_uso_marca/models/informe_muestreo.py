from odoo import fields, api, models, exceptions

class InformeMuestreo(models.Model):
    _name = 'informe.muestreo'
    _description = "Informe de Muestreo"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'


    fecha_recepcion = fields.Date('Fecha de Recepción',  default=fields.Date.today,track_visibility='onchange')
    fecha_ejecucion = fields.Date('Fecha de Ejecución',  default=fields.Date.today,track_visibility='onchange')

    dpto_ejecutor_id = fields.Many2one('intn.departamentos',string="Departamento Ejecutor", track_visibility='onchange', required=True)

    city_id = fields.Many2one('res.country.state.city', string="Lugar",track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    solicitante_id = fields.Many2one('res.partner', 'Solicitante', required="True", track_visibility='onchange')
    street = fields.Char('Calle', related="solicitante_id.street", track_visibility='onchange')
    city_id = fields.Many2one('res.country.state.city', string="Ciudad", related="solicitante_id.city_id",
                              track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Expediente N°', required=False, track_visibility='onchange')


    acta_id = fields.Many2one('acta.extraccion',string='Acta INTN N°', track_visibility='onchange')

    descripcion_items = fields.Char('Descripción de los Items', required=True, track_visibility='onchange')
    product_id = fields.Many2one('product.template',string='Producto', required=True, track_visibility='onchange', related="acta_id.product_id")
    lugar_muestreo = fields.Char('Lugar de Muestreo', required=True, track_visibility='onchange', related="acta_id.lugar_muestreo")
    cantidad_lote = fields.Char('Cantidad de Lote', required=True, track_visibility='onchange')
    lote = fields.Char("Lote N°", required=True, track_visibility='onchange')
    presentacion = fields.Char('Presentación', required=True, track_visibility='onchange')
    volumen_lote = fields.Char('Volumen del Lote', required=True, track_visibility='onchange')

    descripcion1 = fields.Html('Descripcion 1')

    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado')], default='draft', track_visibility='onchange')


    def button_confirmar(self):
        for this in self:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_informe_muestreo')
            this.write({'name': seq})
            this.write({'state': 'done'})
            reg = {
                'res_id': self.id,
                'res_model': 'informe.muestreo',
                'partner_id': self.solicitante_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})
