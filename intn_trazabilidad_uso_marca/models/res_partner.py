# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ , exceptions


class ResPartner(models.Model):
    _inherit = "res.partner"

    licencia_servicios_ids = fields.One2many('licencia.servicios', 'solicitante_id',string="Licencias Marca INTN-Servicios", copy=False, track_visibility=True)

    state_uso_marca = fields.Selection(string="Estado", selection=[('habilitado', 'Habilitado'), (
        'suspendido', 'Suspendido'), ('cancelado', 'Cancelado'), ('vencido', 'Vencido')], default='', track_visibility='onchange')

    nombre_impresion = fields.Char('Nombre a mostrar en Etiqueta', track_visibility='onchange')

    cod_uso_marca = fields.Char(string="Código",track_visibility='onchange')

    marca_id = fields.Many2one('marca.producto', string="Marca",track_visibility='onchange')


    @api.onchange('state_uso_marca')
    def onchangeStateUsoMarca(self):
        for this in self:
            if this.state_uso_marca == 'habilitado' or this.state_uso_marca == 'vencido':
                raise exceptions.ValidationError(
                    "No puede cambiar a estado HABILITADO o VENCIDO. Éstos estados son manejados por la Licencia.")
