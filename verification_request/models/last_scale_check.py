# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LastScaleCheck(models.Model):
    _name = 'last.scale.check'
    _description = 'Ultima Fecha Verifiacion Bascula'

    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    ultima_fecha_verificacion = fields.Date(string='Última Fecha de Verificación', required=True)
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', compute='_compute_fecha_vencimiento', store=True)
    resultado_ultima_verificacion = fields.Selection(
        [('aprobado', 'Aprobado'), ('imposibilidad', 'Imposibilidad'),('reprobado', 'No Aprobado')],
        string='Resultado Última Verificación',
        required=True
    )
    marca_verificacion = fields.Char(string='Marca Verificacion')
    tipo_instrumento = fields.Char(string='Tipo de Instrumento')
    fabricante = fields.Char(string='Fabricante')
    modelo = fields.Char(string='Modelo')
    nro_serie = fields.Char(string='Nro. de Serie')
    ubicacion = fields.Char(string='Ubicacion del instrumento')
    destinado = fields.Char(string='Destinado a')
    id_ultima_verificacion = fields.Many2one('verification.request', string='Id ultima verificacion')

    @api.depends('ultima_fecha_verificacion')
    def _compute_fecha_vencimiento(self):
        for record in self:
            if record.ultima_fecha_verificacion:
                record.fecha_vencimiento = fields.Date.add(record.ultima_fecha_verificacion, years=1)
