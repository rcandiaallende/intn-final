from odoo import fields, api, models, exceptions


class FacturaComprobante(models.Model):
    _name = 'factura_comprobante'
    _description = "Factura Comprobantes"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_factura desc'

    fecha_hora = fields.Datetime(
        'Fecha/Hora', default=lambda self: fields.Datetime.now())
    fecha_factura = fields.Date(string="Fecha de Factura", required=True, track_visibility='onchange')
    proveedor_id = fields.Many2one('res.partner', string="Proveedor", track_visibility='onchange')
    name = fields.Char(string="Nro de Factura", required=True, track_visibility='onchange')
    cliente_id = fields.Many2one('res.partner', string="Proveedor", track_visibility='onchange')
    factura_compra_pdf = fields.Binary(string="Factura por compra")
    factura_compra_name = fields.Char(string="Factura por compra Name")
    timbrado = fields.Char(string="Timbrado Factura", required=True)

    line_ids = fields.One2many('factura_comprobante_lines', 'factura_comprobante_id',string="Lineas de Factura", required=True)

    state = fields.Selection(string="Estado",
                             selection=[("draft", "Borrador"), ("done", "Confirmado"), ("cancel", "Cancelado")],
                             default="draft", copy=False,
                             track_visibility="onchange")

    _sql_constraints = [
        ('unique_name_timbrado', 'UNIQUE(name, timbrado)', 'El nombre y el timbrado deben ser únicos.'),
    ]

    def button_cancelar(self):
        for this in self:
            this.write({'state':'cancel'})

    def button_confirmar(self):
        for this in self:
            this.write({'state':'done'})


class FacturaComprobanteLines(models.Model):
    _name = 'factura_comprobante_lines'
    _description = "Lieas de Factura Comprobantes"
    _order = 'factura_comprobante_id desc'

    factura_comprobante_id = fields.Many2one('factura_comprobante', string="Factura de Compra", required=True)
    product_id = fields.Many2one('product.product',string='Descripción', required=True,track_visibility='onchange')
    qty = fields.Float(string='Cantidad', required=True, default=1)
    aprox_qty_usada = fields.Float(string='Cantidad Aprox. Utilizada', required=True, default=0)
    qty_usada = fields.Float(string='Cantidad Utilizada', readonly=True, compute='_compute_used_qty')

    def _compute_used_qty(self):
        self.qty_usada = self.qty - self.aprox_qty_usada
        return self.qty_usada
