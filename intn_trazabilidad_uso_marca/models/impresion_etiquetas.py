import uuid
from odoo import api, fields, models, exceptions
import datetime
from datetime import date

import dateutil
from dateutil.relativedelta import relativedelta


class ImpresionEtiquetas(models.Model):
    _name = 'impresion.etiquetas'
    _description = 'Impresión de Etiquetas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc"

    name = fields.Char(
        string='Número', track_visibility="onchange", copy=False)
    product_id = fields.Many2one('product.product', string='Etiqueta', domain=[('es_etiqueta', '=', True)],
                                 track_visibility="onchange")

    qty = fields.Integer(string='Cantidad', required=True, default=1)
    solicitud_id = fields.Many2one(
        "solicitud.impresiones", string="Solicitud de Impresión", required=True, track_visibility="onchange")
    licencia_id = fields.Many2one('licencia.servicios', string="Licencia por Uso de Marca", copy=False,
                                  track_visibility="onchange", related="solicitud_id.licencia_id")
    fecha_solicitud = fields.Datetime(
        string="Fecha de solicitud", track_visibility="onchange", related="solicitud_id.fecha_solicitud")
    user_id = fields.Many2one(
        "res.users", string="Usuario", copy=False, track_visibility="onchange")
    partner_id = fields.Many2one("res.partner", string="Empresa", required=True, track_visibility="onchange",
                                 related="solicitud_id.partner_id")
    control_inicial = fields.Integer(string='N. Control Inicial', required=True)
    prox_control = fields.Integer(string="Proximo Control")
    control_final = fields.Integer(string='N. Control Final', required=True)

    state = fields.Selection(string="Estado",
                             selection=[("asignado", "Asignado"), ("verificado", "Verificado"),("reimpresion","Reimpresión"),
                                        ("cancel", "Cancelado")], default="asignado", copy=False,
                             track_visibility="onchange")

    reimpresion = fields.Selection(string="Reimpresión",
                             selection=[("solicitada", "Solicitada"), ("hecha", "Hecha")], default="", copy=False,
                             track_visibility="onchange")

    lines = fields.One2many('impresion.etiquetas.lines', 'impresion_etiquetas_id', string="Registro de Impresion")

    primera_etiqueta = fields.Boolean('Primera Etiqueta', default=False, copy=False)
    necesita_verificacion = fields.Boolean('Necesita Verificación', default=False, copy=False)
    cant_impresos = fields.Integer('Cantidad de Impresos', default=0, copy=False)

    active= fields.Boolean('Activado', default=True)

    lot_ids = fields.Many2many('stock.production.lot',string='Lotes')

    quant_ids = fields.Many2many('stock.quant', string='Stock actual', compute="stockActual")


    muestra_verificar = fields.Boolean(string="Visible Verificar", compute="botonesVisibles")
    muestra_primera_etiqueta = fields.Boolean(string="Visible Primera Etiqueta", compute="botonesVisibles")
    muestra_imprimir = fields.Boolean(string="Visible Imprimir", compute="botonesVisibles")


    def botonesVisibles(self):
        for this in self:
            if this.state == 'asignado':
                if this.primera_etiqueta:
                    this.muestra_primera_etiqueta = False
                else:
                    this.muestra_primera_etiqueta = True
                if this.necesita_verificacion:
                    this.muestra_verificar = True
                else:
                    this.muestra_verificar = False
                if this.qty > this.cant_impresos and not this.necesita_verificacion:
                    this.muestra_imprimir = True
                else:
                    this.muestra_imprimir = False

    def button_autorizar_reimpresion(self):
        for this in self:
            this.state = 'asignado'

    @api.onchange('product_id')
    @api.depends('product_id')
    def stockActual(self):
        location_a_imprimir = self.env['stock.location'].search([('location_to_print', '=', True)])
        if not location_a_imprimir:
            raise exceptions.ValidationError(
                "No puede realizar impresiones sin definir el stock de salida.")
        #product = self.env['product.product'].search([('product_tmpl_id','=',self.product_id)])
        quants = self.env['stock.quant'].search([('location_id', '=', location_a_imprimir.id),
                                                 ('product_id', '=', self.product_id.id), ('quantity', '>', 0)])
        quants_anteriores = self.env['impresion.etiquetas'].search([('id','!=',self.id),('lot_ids','!=',False)])
        quants = quants.filtered(lambda r: r.lot_id not in self.lot_ids and r.lot_id not in quants_anteriores.mapped('lot_ids'))
        self.quant_ids = [(6, 0, quants.ids)]

    #@api.model
    def button_verificar(self):
        view = self.env.ref(
            'intn_trazabilidad_uso_marca.verificar_wizard_view')
        return {
            'name': 'Verificar',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'intn_trazabilidad_uso_marca.verificar_impresion_wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_impresion_etiquetas_id': self.id},
        }

        """for this in self:
            this.write({'state': 'verificado'})
            sol = self.env['impresion.etiquetas'].search(
                [('solicitud_id', '=', this.solicitud_id.id), ('state', '!=', 'verificado')])
            if not sol:
                this.solicitud_id.verificar()"""

    def open_scrap(self):
        location_a_imprimir = self.env['stock.location'].search([('location_to_print', '=', True)])
        return {
            'name': 'Desechar',
            'type': 'ir.actions.act_window',
            'view_type': 'form,tree',
            'view_mode': 'form,tree',
            'res_model': 'stock.scrap',
            'src_model': 'stock.scrap',
            'target': 'current',
            'context': {
                'default_impresion_etiquetas_id': self.id,
                'default_product_id': self.product_id.id,
                'search_default_impresion_etiquetas_id':self.id,
                'default_location_id':location_a_imprimir.id},
        }

    # @api.model
    # def button_confirmar(self):
    #    for i in self:
    #        # if i.order_id:
    #        #    i.order_id.action_cancel()
    #        i.write({'state': 'verificado'})
    #    return

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            seq = self.env['ir.sequence'].sudo().next_by_code(
                'seq_impresion_etiquetas')
            vals['name'] = seq
        res = super(ImpresionEtiquetas, self).create(vals)
        return res

    def button_cancelar(self):
        for i in self:
            # if i.order_id:
            #    i.order_id.action_cancel()
            i.write({'state': 'cancel'})
        return

    def unlink(self):
        raise exceptions.ValidationError(
            "No se pueden eliminar impresiones, sólo cancelarlas.")

    def button_imprimir_primera_etiqueta(self):
        lote = self.quant_ids.filtered(lambda x: not x.lot_id in self.lot_ids).mapped('lot_id').sorted('name')[0]
        vals = {
            'nro_secuencia': 1,
            'partner_id': self.partner_id.id,
            'licencia_id': self.licencia_id.id,
            'nro_control': self.prox_control,
            'state': 'listo',
            'impresion_etiquetas_id': self.id,
            'lot_id':lote.id
        }
        self.env['impresion.etiquetas.lines'].create(vals)
        #self.product_id.sgte_numero_control = self.product_id.sgte_numero_control + 1
        self.write({'prox_control':self.prox_control + 1,'primera_etiqueta':True,'cant_impresos':1,'necesita_verificacion':True})
        self.write({'lot_ids':[(4,lote.id)]})

    def button_reimprimir(self):
        if not self.quant_ids:
            raise exceptions.ValidationError(
                "No puede realizar impresiones, no tiene stock suficiente.")
        view = self.env.ref(
            'intn_trazabilidad_uso_marca.reimprimir_wizard_view')
        return {
            'name': 'Reimprimir',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reimprimir.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_impresion_etiquetas_id': self.id,
                'default_nro_control_final':int(self.prox_control - 1),
                'default_nro_control_inicial':self.control_inicial
            },
        }


    def button_imprimir(self):
        if self.lines:
            lineas_reimprimir = self.lines.filtered(lambda x: x.state == 'reimpresion')
            if lineas_reimprimir:
                for l in lineas_reimprimir:
                    if l == lineas_reimprimir[0]:
                        state = 'listo'
                    else:
                        state = 'pendiente'
                    lote = self.quant_ids.mapped('lot_id').sorted('name')[0]
                    l.write({'state':state,'lot_id':lote.id})
                    self.necesita_verificacion = True
                    self.write({'lot_ids': [(4, lote.id)]})
                    self.stockActual()
            else:
                if not self.quant_ids:
                    raise exceptions.ValidationError(
                        "No puede realizar impresiones, no tiene stock suficiente.")
                view = self.env.ref(
                    'intn_trazabilidad_uso_marca.imprimir_wizard_view')
                cantidad = self.qty - self.cant_impresos
                cantidad_maxima = self.qty - self.cant_impresos
                if len(self.quant_ids) > 200 or cantidad > 200:
                    cantidad = 200
                if 200 > self.qty - self.cant_impresos:
                        cantidad = self.qty - self.cant_impresos
                if len(self.quant_ids) < cantidad:
                    cantidad = len(self.quant_ids)
                    cantidad_maxima = self.qty - self.cant_impresos
                return {
                    'name': 'Imprimir',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'impresion.etiquetas.imprimir.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': {
                        'default_impresion_etiquetas_id': self.id,
                        'default_nro_control':self.prox_control,
                        'default_lot_id': self.quant_ids.mapped('lot_id').sorted('name')[0].id,
                        'default_lote_etiqueta': self.quant_ids.mapped('lot_id').sorted('name')[0].name,
                        'default_cantidad_maxima': cantidad_maxima,
                        'default_cantidad':cantidad
                    },
                }
