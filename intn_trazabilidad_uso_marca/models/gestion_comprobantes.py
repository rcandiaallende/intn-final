import datetime

from odoo import fields, api, models, exceptions


class GestionComprobantesLines(models.Model):
    _name = 'gestion_comprobantes_lines'
    _description = "Lineas de Gestion de Comprobantes"
    #_order = 'impresion_etiquetas_id desc'

    product_id = fields.Many2one('product.product', string='Etiqueta', required=True,domain=[('es_etiqueta', '=', True)],track_visibility="onchange")
    qty = fields.Integer(string='Cantidad', required=True, default=1)
    nro_inicial = fields.Integer(string='N. Inicial', required=True)
    nro_final = fields.Integer(string='N. Final', required=True)
    compra_anillos = fields.Boolean('Compra Anillos', required=False)
    factura_anillo_ids = fields.Many2many('factura_comprobante', string="Facturas", required=False)
    comprobante_id = fields.Many2one('gestion.comprobantes', string="Comprobante", required=True)
    impresion_etiqueta_id = fields.Many2one('impresion.etiquetas', required=False, string="Impresion de Etiquetas")

    #factura_compra_pdf = fields.Binary(string="Factura por compra de PQs")
    #factura_compra_name = fields.Char(string="Factura por compra de PQs Name")


class GestionComprobantes(models.Model):
    _name = 'gestion.comprobantes'
    _description = "Gestion de Comprobantes"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    solicitud_id = fields.Many2one(
        "solicitud.impresiones", string="Solicitud de Impresión", required=True, track_visibility="onchange")
    impresion_etiquetas_ids = fields.Many2many('impresion.etiquetas', required=True, string="Impresion de Etiquetas")
    fecha_hora = fields.Datetime(
        'Fecha/Hora', default=lambda self: fields.Datetime.now())
    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Cliente', required="True", track_visibility='onchange')

    lines = fields.One2many('gestion_comprobantes_lines', 'comprobante_id', string="Lineas de Comprobantes")

    state = fields.Selection(string="Estado",selection=[("draft", "Borrador"), ("done", "Confirmado"),("cancel", "Cancelado")], default="draft", copy=False,
                             track_visibility="onchange")

    order_id = fields.Many2one('sale.order', string="Expediente")

    def button_confirmar(self):
        for this in self:
            for line in this.lines:
                if not line.compra_anillos and line.product_id.aro_id:
                    if not line.factura_anillo_ids:
                        raise exceptions.ValidationError(
                            "En caso de que el cliente no compre anillos, debe cargar una factura por la compra de los"
                            "mismos.")
                    else:
                        lines_product = line.mapped('factura_anillo_ids').filtered(lambda x: x.state == 'done'). \
                            mapped('line_ids').filtered(lambda x: x.product_id == line.product_id.aro_id)
                        if not lines_product:
                            raise exceptions.ValidationError(
                                "La/s factura/s de compra de anillo no coinciden con el anillo solicitado.")
                        else:
                            if sum(lines_product.mapped('aprox_qty_usada')) < line.qty:
                                raise exceptions.ValidationError(
                                    "No tiene anillos suficientes para la cantidad de etiquetas impresas")
                            else:
                                cant_descontar = line.qty
                                for l in lines_product:
                                    if cant_descontar > 0:
                                        if cant_descontar > l.aprox_qty_usada:
                                            resto = cant_descontar - l.aprox_qty_usada
                                            l.aprox_qty_usada = l.aprox_qty_usada - resto
                                            cant_descontar = cant_descontar - resto
                                        else:
                                            l.aprox_qty_usada = l.aprox_qty_usada  - cant_descontar
                                            cant_descontar = 0
            # else:
            # if i.order_id:
            #    i.order_id.action_cancel()
            #this.crearExpediente()
            this.write({'state': 'done'})


    def generarTransferencias(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([('operacion_entrega_etiquetas','=',True)])
        if not picking_type:
            raise exceptions.ValidationError(
                "Debe definir una operación de entrega de Etiquetas.")
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': self.name,
            'partner_id': self.partner_id.id,
            'move_lines': []
        }
        picking = self.env['stock.picking'].create(picking_vals)
        for l in self.lines:
            move = {
                'name': '/',
                'product_id': l.product_id.id,
                'product_uom': l.product_id.uom_id.id,
                'product_uom_qty': l.qty,
                'picking_id':picking.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            }
            move = self.env['stock.move'].create(move)
            for lot in l.impresion_etiqueta_id.lot_ids:
                lines = {
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'lot_id': lot.id,
                    # 'product_uom_qty': 1,
                    'qty_done': 1,
                    'product_uom_id': l.product_id.uom_id.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                }
                move_lines = self.env['stock.move.line'].create(lines)
            if l.compra_anillos:
                move = {
                    'name': '/',
                    'product_id': l.product_id.aro_id.id,
                    'product_uom': l.product_id.aro_id.uom_id.id,
                    'product_uom_qty': l.qty,
                    'picking_id': picking.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                }
                move = self.env['stock.move'].create(move)
        return {
            'name': ('Entregas'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'), (False, 'kanban'), (False, 'form')],
            'view_mode': 'list,kanban,form',
            'context': {
                "search_default_id": picking.id,
                "default_id": picking.id,
                "searchpanel_default_id": picking.id
            },
        }

    def crearExpediente(self):
        for this in self:
            lines = []
            values = {
                'partner_id': this.partner_id.id,
                'partner_shipping_id': this.partner_id.id,
                'partner_invoice_id': this.partner_id.id,
                'date_order': datetime.datetime.now(),
                'fecha': datetime.datetime.now(),
                #'fecha_estimada': self.fecha_estimada or False,
                # 'tecnico_id': self.tecnico_id or False,
                'origin': this.name,
                #'solicitud_id': self.id
            }
            order = self.env['sale.order'].sudo().create(
                values)
            for line in this.lines:
                linea = {
                    'customer_lead': 0,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'order_id': order.id,
                    'price_unit': line.product_id.lst_price,
                    'product_uom_qty': line.qty,
                    'tax_id': [(6, 0, line.product_id.taxes_id.ids)],
                }
                lines.append((0, 0, linea))
                if line.compra_anillos:
                    linea = {
                        'customer_lead': 0,
                        'product_id': line.product_id.aro_id.id,
                        'name': line.product_id.aro_id.name,
                        'order_id': order.id,
                        'price_unit': line.product_id.aro_id.lst_price,
                        'product_uom_qty': line.qty,
                        'tax_id': [(6, 0, line.product_id.aro_id.taxes_id.ids)],
                    }
                    lines.append((0, 0, linea))
            order.write({'order_line': lines})
            this.write({'order_id': order.id})

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            seq = self.env['ir.sequence'].sudo().next_by_code(
                'seq_gestion_comprobantes2')
            vals['name'] = seq
        res = super(GestionComprobantes, self).create(vals)
        return res

    def button_cancelar(self):
        for i in self:
            # if i.order_id:
            #    i.order_id.action_cancel()
            i.write({'state': 'cancel'})
        return

    def unlink(self):
        raise exceptions.ValidationError(
            "No se pueden eliminar Gestiones de Comprobantes, sólo cancelarlas.")
