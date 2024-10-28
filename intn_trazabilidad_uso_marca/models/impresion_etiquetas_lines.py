import uuid
from odoo import api, fields, models, exceptions
import datetime
from datetime import date

import dateutil
from dateutil.relativedelta import relativedelta

class ImpresoraEtiquetas(models.Model):
    _name = 'impresora.etiquetas'
    _description = 'Impresoras de etiquetas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name desc"

    name= fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo', default=True)


class ImpresionEtiquetasLines(models.Model):
    _name = 'impresion.etiquetas.lines'
    _description = 'Lineas de Impresión de Etiquetas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "nro_control asc"
    _rec_name = "nro_control"

    nro_secuencia = fields.Char("Nro de Secuencia")
    impresion_etiquetas_id = fields.Many2one('impresion.etiquetas', required=True, string="Impresion de Etiquetas")
    partner_id = fields.Many2one("res.partner", string="Empresa", required=True, track_visibility="onchange", related="impresion_etiquetas_id.partner_id")
    qr_code = fields.Char(string="QR Code", related="licencia_id.qr_code_public")
    licencia_id = fields.Many2one('licencia.servicios', string="Licencia", copy=False, related="impresion_etiquetas_id.licencia_id")
    nro_control = fields.Integer('Nro de Control', copy=False)
    state = fields.Selection(string="Estado",selection=[("reimpresion","Reimpresion"),("pendiente", "Pendiente"), ("listo", "Listo"),("hecho", "Hecho"),("verificado","Verificado")], default="pendiente", copy=False,
                             track_visibility="onchange")

    printer_etiqueta_id = fields.Many2one('impresora.etiquetas', string="Impresora de Etiquetas")
    lot_id = fields.Many2one('stock.production.lot', string="Lote")


    @api.model
    @api.constrains('state','printer_etiqueta_id')
    def obtener_linea_solicitud(self):
        impresora = self.env['impresora.etiquetas'].search([('active','=',True)])
        if not impresora or len(impresora) >1:
            raise exceptions.ValidationError(
                "Verifique la impresora activa.")
        proximo = self.env['impresion.etiquetas.lines'].search([('state', '=', 'listo')])

        if proximo:
            proximo=proximo[0]
            linea = {
                'id':proximo.id,
                'nombre':proximo.partner_id.nombre_impresion,
                'numero':str(proximo.nro_control).zfill(7),
                'licencia':proximo.licencia_id.name,
                'qr':proximo.qr_code,
                'impresora': impresora.name
            }
            return linea
        else:
            return None

    def hecho(self):
        for this in self:
            this.write({'state':'hecho'})
            seq = int(this.nro_secuencia) + 1
            proximo = this.env['impresion.etiquetas.lines'].search([('nro_secuencia','=',seq),('state','=','pendiente'),('impresion_etiquetas_id','=',this.impresion_etiquetas_id.id)])
            if proximo:
                proximo.write({'state':'listo'})
            return

