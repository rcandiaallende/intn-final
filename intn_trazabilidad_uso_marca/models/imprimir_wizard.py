from odoo import fields, api, models, exceptions


class WizardImprimir(models.TransientModel):
    _name = 'impresion.etiquetas.imprimir.wizard'

    impresion_etiquetas_id = fields.Many2one(
        'impresion.etiquetas', string="Impresion de Etiquetas", required=True)
    nro_control = fields.Integer(string="Prox. Numero de Control", required=True, related="impresion_etiquetas_id.prox_control")
    lote_etiqueta = fields.Char(string="Lote de Etiqueta")
    cantidad=fields.Integer('Cantidad')
    cantidad_maxima=fields.Integer('Cantidad máxima')
    lot_id = fields.Many2one('stock.production.lot',string="Lote")


    def button_imprimir(self):
        for i in self:
            if i.cantidad_maxima and i.cantidad > i.cantidad_maxima:
                raise exceptions.ValidationError(
                    "No puede imprimir la cantidad seleccionada.")
            x = 0
            create_vals = []
            while x < i.cantidad:
                print(x)
                if x == 0:
                    state = 'listo'
                    lote = i.lot_id
                else:
                    state = 'pendiente'
                    lote = i.impresion_etiquetas_id.quant_ids.mapped('lot_id').sorted('name')[0]
                vals = {
                    'nro_secuencia': x+1,
                    'partner_id': i.impresion_etiquetas_id.partner_id.id,
                    'licencia_id': i.impresion_etiquetas_id.licencia_id.id,
                    'nro_control': i.impresion_etiquetas_id.prox_control,
                    'state': state,
                    'impresion_etiquetas_id': i.impresion_etiquetas_id.id,
                    'lot_id':lote.id
                }
                create_vals.append(vals)
                i.impresion_etiquetas_id.write({'lot_ids': [(4, lote.id)]})
                i.impresion_etiquetas_id.stockActual()
                prox_control = i.impresion_etiquetas_id.prox_control +1
                i.impresion_etiquetas_id.write({'prox_control': prox_control,
                                                'cant_impresos':i.impresion_etiquetas_id.cant_impresos+1})
                x = x+1
            self.env['impresion.etiquetas.lines'].create(create_vals)
            i.impresion_etiquetas_id.necesita_verificacion = True
            #i.impresion_etiquetas_id.product_id.write({'sgte_numero_control':prox_control})