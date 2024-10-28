from odoo import fields, api, models, exceptions


class ActaExtraccion(models.Model):
    _name = 'acta.extraccion'
    _description = "Acta de Extracción de Muestras"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    fecha_hora = fields.Datetime(
        'Fecha de Informe', default=lambda self: fields.Datetime.now())

    city_id = fields.Many2one('res.country.state.city', string="Lugar", track_visibility='onchange')

    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    solicitante_id = fields.Many2one('res.partner', 'Solicitante', required="True", track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Expediente N°', required=False, track_visibility='onchange')

    product_id = fields.Many2one('product.template','Producto', required=True, track_visibility='onchange')
    lugar_muestreo = fields.Char('Lugar de Muestreo', required=True, track_visibility='onchange')
    norma_ids = fields.Many2many('normas.licencia', string="Norma o método aplicado", track_visibility='onchange')

    detalle_lote = fields.Html('Detalle del Lote', required=True, track_visibility='onchange')

    muestra = fields.Html('Muestra', required=True, track_visibility='onchange',
                          default="Cantidad<br/><br/><br/>Identificación")

    observacion = fields.Html('Observación', required=False, track_visibility='onchange')

    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'done', 'Confirmado'), ('cancel', 'Cancelado')], default='draft', track_visibility='onchange')

    def button_confirmar(self):
        for this in self:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_acta_extraccion')
            this.write({'name': seq})
            this.write({'state': 'done'})
            reg = {
                'res_id': self.id,
                'res_model': 'acta.extraccion',
                'partner_id': self.solicitante_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)

    def button_cancelar(self):
        for this in self:
            this.write({'state': 'cancel'})
