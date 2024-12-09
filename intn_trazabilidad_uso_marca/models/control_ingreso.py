from odoo import models, fields, api, _


class ControlIngresoInstrumentos(models.Model):
    _name = 'control.ingreso.instrumentos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Control de Ingreso de Instrumentos'

    name = fields.Char(string='N° Documento',
                       default=lambda self: self.env['ir.sequence'].next_by_code('control.ingreso.instrumentos'))
    expediente = fields.Many2one('sale.order', string='N° de Expediente')
    product_id = fields.Many2one('product.product', string='Fabricar', required=True)
    centro_produccion = fields.Many2one('mrp.workcenter', string='Centro de Producción', required=True)
    razon_social = fields.Many2one('res.partner', string='Razón Social')
    ruc = fields.Char(related='razon_social.vat', string='R.U.C.')
    telefono_fax = fields.Char(related='razon_social.phone', string='Tel/Fax')
    contacto = fields.Char(string='Contacto')
    email = fields.Char(related='razon_social.email', string='Email')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    compromiso_entrega_fecha = fields.Date(string='Compromiso de Entrega (Fecha)')
    compromiso_entrega_hora = fields.Float(string='Compromiso de Entrega (Hora)', help="Hora estimada en formato HH.MM")
    notas = fields.Text(string='Notas Generales')
    observaciones = fields.Text(string='Observaciones')
    line_ids = fields.One2many('control.ingreso.instrumentos.line', 'control_id', string='Líneas de Instrumentos')
    firma_recibi = fields.Binary(string="Firma Recibí Conforme (ONM - INTN)")
    firma_usuario = fields.Binary(string="Firma Usuario")
    aclaracion_recibi = fields.Char(string="Aclaración Recibí Conforme")
    aclaracion_usuario = fields.Char(string="Aclaración Usuario")
    cic_recibi = fields.Char(string="C.I.C. No Recibí Conforme")
    cic_usuario = fields.Char(string="C.I.C. No Usuario")
    production_id = fields.Many2one('mrp.production', string='Orden de Producción', readonly=True)
    retiro_parcial_fecha = fields.Date(string='Fecha (Parcial)')
    retiro_parcial_aclaracion_onm = fields.Char(string='Aclaración ONM')
    retiro_parcial_cic_onm = fields.Char(string='C.I.C. No ONM')
    retiro_parcial_aclaracion_usuario = fields.Char(string='Aclaración Usuario')
    retiro_parcial_cic_usuario = fields.Char(string='C.I.C. No Usuario')
    retiro_total_fecha = fields.Date(string='Fecha (Total)')
    retiro_total_aclaracion_onm = fields.Char(string='Aclaración ONM')
    retiro_total_cic_onm = fields.Char(string='C.I.C. No ONM')
    retiro_total_aclaracion_usuario = fields.Char(string='Aclaración Usuario')
    retiro_total_cic_usuario = fields.Char(string='C.I.C. No Usuario')

    @api.multi
    def create_production_order(self):
        """
        Método para crear una orden de producción basada en los datos del control de ingreso.
        """
        self.ensure_one()

        if not self.product_id or not self.centro_produccin:
            raise models.ValidationError(_('Debe especificar un Producto y un Centro de Producción.'))

        product_uom = self.product_id.uom_id
        if not product_uom:
            raise models.ValidationError(_('El producto seleccionado no tiene una unidad de medida definida.'))

        if self.product_id.uom_id.category_id != product_uom.category_id:
            raise models.ValidationError(
                _('La unidad de medida definida en el producto no pertenece a la misma categoría que la unidad seleccionada.')
            )

        production_vals = {
            'product_id': self.product_id.id,
            'product_qty': 1.0,
            'product_uom_id': product_uom.id,
            'bom_id': self.product_id.bom_ids[:1].id if self.product_id.bom_ids else False,
            'date_planned_start': self.compromiso_entrega_fecha or fields.Datetime.now(),
            'workcenter_id': self.centro_produccin.id,
            'origin': self.name,
        }
        production = self.env['mrp.production'].create(production_vals)

        self.production_id = production.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
            'target': 'current',
        }


class ControlIngresoInstrumentosLine(models.Model):
    _name = 'control.ingreso.instrumentos.line'
    _description = 'Detalle de Instrumentos'

    item = fields.Integer(string='Ítem')
    cantidad = fields.Integer(string='Cantidad')
    instrumento = fields.Char(string='Instrumento')
    identificacion = fields.Char(string='Identificación')
    control_id = fields.Many2one('control.ingreso.instrumentos', string='Control de Ingreso')
