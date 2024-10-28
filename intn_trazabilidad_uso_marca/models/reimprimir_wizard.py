from odoo import api, fields, models, exceptions


class LineasReimprimir(models.Model):
    _name = 'lineas_reimprimir'

    lineas = fields.Many2many('impresion.etiquetas.lines', string='Nros de Control')
    reimprimir = fields.Boolean('Reimprimir', default=False)
    state = fields.Selection(string="Estado",
                             selection=[("pendiente", "Pendiente"), ("confirmado", "Confirmado")], default="pendiente",
                             copy=False,
                             track_visibility="onchange")


class WizardReimprimir(models.TransientModel):
    _name = 'reimprimir.wizard'

    impresion_etiquetas_id = fields.Many2one(
        'impresion.etiquetas', string="Impresion de Etiquetas", required=True)
    product_id = fields.Many2one('product.product', string="Etiqueta", required=True, related="impresion_etiquetas_id.product_id")
    nro_control_final = fields.Integer(string="Número de Control Final", required=False)
    nro_control_incial = fields.Integer(string="Número de Control Inicial", required=False)
    lineas = fields.Many2many('impresion.etiquetas.lines', string='Nros de Control')



    def button_solicitar_reimpresion(self):
        self.impresion_etiquetas_id.write({'reimpresion':'solicitada','state':'reimpresion','necesita_verificacion':False})
        for l in self.lineas:
            l.write({'state':'reimpresion'})