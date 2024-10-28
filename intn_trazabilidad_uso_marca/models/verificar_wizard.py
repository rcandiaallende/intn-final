from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class WizardVerificar(models.TransientModel):
    _name = 'intn_trazabilidad_uso_marca.verificar_impresion_wizard'

    impresion_etiquetas_id = fields.Many2one(
        'impresion.etiquetas', string="Impresion de Etiquetas", required=True)
    product_id = fields.Many2one('product.product', string="Etiqueta", required=True, related="impresion_etiquetas_id.product_id")
    nro_control = fields.Integer(string="Número de Control", required=False)
    nro_lote = fields.Char(string='Número de Serie', required=False)

    nro_control_requerido = fields.Integer(string="Número de Control Requerido", required=True)
    nro_lote_requerido = fields.Char(string='Número de Serie Requerido', required=True)
    linea_id = fields.Many2one('impresion.etiquetas.lines', string='Linea Actual')

    nro_control_dif = fields.Boolean('Nro de Control Diferente')
    nro_lote_dif = fields.Boolean('Nro de Lote Diferente')
    motivo = fields.Text('Motivo')

    @api.depends('nro_lote', 'nro_control')
    @api.onchange('nro_lote', 'nro_control')
    def onchangeControlLote(self):
        for this in self:
            if this.nro_lote != this.nro_lote_requerido:
                this.nro_lote_dif = True
            else:
                this.nro_lote_dif = False
            if this.nro_control != this.nro_control_requerido:
                this.nro_control_dif = True
            else:
                this.nro_control_dif = False


    @api.depends('impresion_etiquetas_id','product_id')
    @api.onchange('impresion_etiquetas_id','product_id')
    def onchangeProductId(self):
        for this in self:
            lineas = self.env['impresion.etiquetas.lines'].search([('state', '!=', 'verificado'),
                                                                   ('impresion_etiquetas_id', '=', this.impresion_etiquetas_id.id)])
            if len(lineas) > 1:
                mayor = lineas.mapped('lot_id').sorted('name', reverse=True)
                lineas = self.env['impresion.etiquetas.lines'].search([('lot_id', '=', mayor[0].id)])[0]
            this.nro_control = lineas.nro_control
            this.nro_control_requerido = lineas.nro_control
            this.nro_lote = lineas.lot_id.name
            this.nro_lote_requerido = lineas.lot_id.name

    def button_confirmar(self):
        for this in self:
            this.impresion_etiquetas_id.necesita_verificacion = False
            lineas = self.env['impresion.etiquetas.lines'].search([('state', '!=', 'verificado'),
                                                                   ('impresion_etiquetas_id', '=',
                                                                    this.impresion_etiquetas_id.id)])
            if len(lineas) == 1:
                lineas.write({'state': 'verificado'})
            else:
                for l in lineas:
                    l.write({'state': 'verificado'})

            if this.nro_control_dif:
                this.impresion_etiquetas_id.message_post(
                    body="El Nro de Control debería ser " + this.nro_control_requerido + ', en cambio es ' + this.nro_control)
                this.impresion_etiquetas_id.nro_control = this.nro_control + 1
                this.impresion_etiquetas_id.message_post(body=this.motivo)
            if this.nro_lote_dif:
                this.impresion_etiquetas_id.message_post(
                    body="El Nro de Lote debería ser " + this.nro_lote_requerido + ', en cambio es ' + this.nro_lote)
                this.impresion_etiquetas_id.message_post(body=this.motivo)

            create_vals = []
            if this.impresion_etiquetas_id.cant_impresos == this.impresion_etiquetas_id.qty:
                this.impresion_etiquetas_id.write({'state': 'verificado','active':False})
                this.impresion_etiquetas_id.solicitud_id.verificar()
                location_printed= self.env['stock.location'].search([('location_printed','=',True)])
                location_to_print= self.env['stock.location'].search([('location_to_print','=',True)])
                if not location_printed or len(location_printed) >1:
                    raise exceptions.ValidationError(
                        "No puede realizar impresiones sin definir la ubicación de impresión.")
                vals = {
                    'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                    'location_id': location_to_print.id,
                    'location_dest_id': location_printed.id,
                    'origin': this.impresion_etiquetas_id.name,
                    'partner_id': this.impresion_etiquetas_id.partner_id.id,
                    'move_lines': [(0, 0, {
                        'name': '/',
                        'product_id': this.product_id.id,
                        'product_uom': this.product_id.uom_id.id,
                        'product_uom_qty': len(this.impresion_etiquetas_id.lot_ids),
                        #'quantity_done': len(this.impresion_etiquetas_id.lot_ids),
                    })],
                }
                picking = self.env['stock.picking'].create(vals)
                move = picking.move_lines[0]
                for l in this.impresion_etiquetas_id.lot_ids:
                    lines = {
                        'picking_id': picking.id,
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'lot_id': l.id,
                        #'product_uom_qty': 1,
                        'qty_done': 1,
                        'product_uom_id': this.product_id.uom_id.id,
                        'location_id': location_to_print.id,
                        'location_dest_id': location_printed.id,
                    }
                    create_vals.append(lines)
                move_lines = self.env['stock.move.line'].create(create_vals)
                picking.action_confirm()
                picking.button_validate()
