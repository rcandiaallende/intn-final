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

    has_valid_qty = fields.Boolean(
        string="Tiene Cantidad Válida",
        compute="_compute_has_valid_qty",
        store=True
    )

    @api.depends('line_ids.aprox_qty_usada')
    def _compute_has_valid_qty(self):
        for record in self:
            record.has_valid_qty = any(
                line.aprox_qty_usada > 0 for line in record.line_ids
            )

    _sql_constraints = [
        ('unique_name_timbrado', 'UNIQUE(name, timbrado)', 'El nombre y el timbrado deben ser únicos.'),
    ]

    @api.constrains('name')
    def _check_factura_name_length(self):
        for record in self:
            if record.name and len(record.name) != 15:
                raise exceptions.ValidationError(
                    "El número de factura debe tener exactamente 17 caracteres, incluyendo los guiones (ejemplo: 001-003-0001832)."
                )

    @api.model
    def create(self, vals):
        # Comprobar si ya existe una factura con el mismo nombre y timbrado
        existing = self.search([('name', '=', vals.get('name')), ('timbrado', '=', vals.get('timbrado'))])
        if existing:
            raise exceptions.ValidationError(
                "Ya existe una factura con el mismo número y timbrado. Por favor, verifica los datos.")
        return super(FacturaComprobante, self).create(vals)

    def write(self, vals):
        if 'name' in vals or 'timbrado' in vals:
            for record in self:
                name = vals.get('name', record.name)
                timbrado = vals.get('timbrado', record.timbrado)
                # Verificar duplicados en la escritura
                existing = self.search([('name', '=', name), ('timbrado', '=', timbrado), ('id', '!=', record.id)])
                if existing:
                    raise exceptions.ValidationError(
                        "Ya existe una factura con el mismo número y timbrado. Por favor, verifica los datos.")
        return super(FacturaComprobante, self).write(vals)

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
    aprox_qty_usada = fields.Float(string='Cantidad Aprox. Utilizada', compute='_compute_saldo',
                                   store=True, required=True, default=0)
    qty_usada = fields.Float(string='Cantidad Utilizada', readonly=True)

    @api.depends('qty','qty_usada' )
    def _compute_saldo(self):
        for rec in self:
            rec.aprox_qty_usada = rec.qty - rec.qty_usada
            return rec.aprox_qty_usada
