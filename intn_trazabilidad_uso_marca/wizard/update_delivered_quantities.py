# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class UpdateDeliveredQuantities(models.TransientModel):
    _name = 'update.delivered.quantities'
    _description = 'Actualizar cantidades entregadas'

    line_ids = fields.One2many('update.delivered.quantities.line', 'wizard_id', string='Líneas de Instrumentos')

    @api.model
    def default_get(self, fields):
        res = super(UpdateDeliveredQuantities, self).default_get(fields)

        active_ids = self._context.get('active_ids', [])
        if active_ids:
            control_ingresos = self.env['control.ingreso.instrumentos'].browse(active_ids)

            res['line_ids'] = [
                (0, 0, {
                    'control_id': line.id,
                    'control_state': line.control_state,
                    'state': line.state,
                    'item': line.item,
                    'instrumento': line.instrumento.id,
                    'cantidad': line.cantidad,
                    'cantidad_salida': line.cantidad_salida,
                    'cantidad_faltante': line.cantidad_faltante,
                    'identificacion': line.identificacion,
                    'document': line.document,
                })
                for line in control_ingresos.mapped('line_ids')
            ]

        return res

    @api.multi
    def update_delivered_quantities(self):
        for wizard in self:
            control_ingresos = self.env['control.ingreso.instrumentos'].browse(self._context.get('active_ids', []))

            for line in wizard.line_ids:
                control_line = line.control_line_id
                if control_line:
                    new_cantidad_salida = control_line.cantidad_salida + line.cantidad_salida
                    control_line.sudo().write({
                        'cantidad_salida': new_cantidad_salida,
                    })

                    self.env['control.ingreso.instrumentos.line.history'].sudo().create({
                        'control_line': control_line.id,
                        'cantidad_salida': line.cantidad_salida,
                        'cantidad': line.cantidad,
                        'cantidad_faltante': line.cantidad_faltante,
                        'instrumento': line.instrumento.id,
                        'identificacion': line.identificacion,
                        'control_history_id': control_line.control_id.id,
                    })
                else:
                    new_cantidad_salida = line.cantidad_salida
                    line.control_id.sudo().write({
                        'cantidad_salida': new_cantidad_salida,
                    })

                    self.env['control.ingreso.instrumentos.line.history'].sudo().create({
                        'control_line': line.control_id.id,
                        'cantidad_salida': line.cantidad_salida,
                        'cantidad': line.cantidad,
                        'cantidad_faltante': line.cantidad_faltante,
                        'instrumento': line.instrumento.id,
                        'identificacion': line.identificacion,
                        'control_history_id': line.control_id.control_id.id,
                    })


            for control in control_ingresos:
                all_lines_completed = all(
                    line.cantidad_salida >= line.cantidad for line in control.line_ids
                )
                any_line_partial = any(
                    0 < line.cantidad_salida < line.cantidad for line in control.line_ids
                )

                if all_lines_completed:
                    control.sudo().write({'state': 'pickup'})
                elif any_line_partial:
                    control.sudo().write({'state': 'partial_pickup'})


class UpdateDeliveredQuantitiesLine(models.TransientModel):
    _name = 'update.delivered.quantities.line'
    _description = 'Líneas del Wizard de Actualización de Cantidades'

    wizard_id = fields.Many2one('update.delivered.quantities', string='Wizard')
    control_line_id = fields.Many2one('control.ingreso.instrumentos.line', string='Línea de Instrumento')
    control_id = fields.Many2one('control.ingreso.instrumentos.line', string='Control ID')
    control_state = fields.Selection(related='control_id.control_state', string='Estado del Control', readonly=True)
    state = fields.Selection(related='control_id.state', string='Estado', readonly=True)
    item = fields.Integer(related='control_id.item', string='Ítem')
    instrumento = fields.Many2one('instrument.inventory.metci', related='control_id.instrumento',
                                     string='Instrumento')
    cantidad = fields.Integer(string='Cantidad')
    cantidad_salida = fields.Integer(string='Cantidad de Salida')
    cantidad_faltante = fields.Integer(string='Cantidad Faltante')
    identificacion = fields.Char(related='control_id.identificacion', string='Identificación')
    document = fields.Binary(string='Documento')
