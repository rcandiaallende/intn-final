# -*- coding: utf-8 -*-
from odoo import models, fields, api
import statistics


class RegistroMedicionBasculas(models.Model):
    _name = 'registro.medicion.basculas'
    _description = 'Registro de Mediciones'

    name = fields.Char('Certificado No.', required=True)
    fecha_emision = fields.Date('Fecha de emisión', required=True)
    tecnico = fields.Many2one('res.users', string='Técnico')
    tecnico_conductor = fields.Many2one('res.users', string='Técnico Conductor')
    fecha_verificacion = fields.Date('Fecha de verificación')
    calcomania_no = fields.Char('Calcomanía No.')
    objeto = fields.Char('Objeto')
    marca = fields.Char('Marca')
    modelo = fields.Char('Modelo')
    no_serie = fields.Char('No. de Serie')
    razon_social = fields.Many2one('res.partner', string='Razón Social', required=True)
    ruc = fields.Char(related='razon_social.vat', string='RUC N°', store=True)
    direccion = fields.Char(related='razon_social.street', string='Dirección', store=True)
    ciudad = fields.Char(related='razon_social.city', string='Ciudad', store=True)
    departamento = fields.Char(related='razon_social.state_id.name', string='Departamento', store=True)
    capacidad = fields.Float('Capacidad (kg)')
    clase = fields.Char('Clase')
    identificacion_codigo = fields.Char('Identificación/Código')
    ubicacion = fields.Char('Ubicación')
    temperatura_inicial = fields.Float('Temperatura Inicial (ºC)')
    temperatura_final = fields.Float('Temperatura Final (ºC)')
    humedad_inicial = fields.Float('Humedad Relativa Inicial (%)')
    humedad_final = fields.Float('Humedad Relativa Final (%)')
    medicion_ids = fields.One2many('registro.medicion.basculas.linea', 'ensayo_id', string='Ensayos')
    patron = fields.Char('Patrón')
    certificado_numero = fields.Char('Certificado Nº')
    cant_ejes = fields.Integer('Cantidad de Ejes')
    cant_ejes_otros = fields.Integer('Cantidad de Ejes Otros')
    desviacion_estandar = fields.Float('Desv. Estandar (kg)')
    desviacion_estandar_2kg = fields.Float('Desv. Estandar x 2 (kg)')

    promedio_eje_1 = fields.Float('Promedio eje 1 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_eje_2 = fields.Float('Promedio eje 2 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_eje_3 = fields.Float('Promedio eje 3 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_eje_4 = fields.Float('Promedio eje 4 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_eje_5 = fields.Float('Promedio eje 5 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_eje_2_3 = fields.Float('Promedio eje 2+3 (kg)', compute='_compute_avg_ejes', store=True)
    promedio_total_bruto = fields.Float('Promedio total bruto (kg)', compute='_compute_avg_ejes', store=True)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Registro de Medición', self.name)

    @api.depends('medicion_ids')
    def _compute_avg_ejes(self):
        for rec in self:
            if rec.medicion_ids:
                mediciones_eje_1 = len(rec.medicion_ids.filtered(lambda x: x.eje_1))
                mediciones_eje_2 = len(rec.medicion_ids.filtered(lambda x: x.eje_2))
                mediciones_eje_3 = len(rec.medicion_ids.filtered(lambda x: x.eje_3))
                mediciones_eje_4 = len(rec.medicion_ids.filtered(lambda x: x.eje_4))
                mediciones_eje_5 = len(rec.medicion_ids.filtered(lambda x: x.eje_5))
                mediciones_eje_2_3 = len(rec.medicion_ids.filtered(lambda x: x.computed_field))
                mediciones_total_bruto = len(rec.medicion_ids.filtered(lambda x: x.peso_bruto_total))
                rec.promedio_eje_1 = (
                        sum(rec.medicion_ids.mapped("eje_1")) / mediciones_eje_1) if mediciones_eje_1 else 0
                rec.promedio_eje_2 = (
                        sum(rec.medicion_ids.mapped("eje_2")) / mediciones_eje_2) if mediciones_eje_2 else 0
                rec.promedio_eje_3 = (
                        sum(rec.medicion_ids.mapped("eje_3")) / mediciones_eje_3) if mediciones_eje_3 else 0
                rec.promedio_eje_4 = (
                        sum(rec.medicion_ids.mapped("eje_4")) / mediciones_eje_4) if mediciones_eje_4 else 0
                rec.promedio_eje_5 = (
                        sum(rec.medicion_ids.mapped("eje_5")) / mediciones_eje_5) if mediciones_eje_5 else 0
                rec.promedio_eje_2_3 = (
                        sum(rec.medicion_ids.mapped(
                            "computed_field")) / mediciones_eje_2_3) if mediciones_eje_2_3 else 0
                rec.promedio_total_bruto = (
                        sum(rec.medicion_ids.mapped(
                            "peso_bruto_total")) / mediciones_total_bruto) if mediciones_total_bruto else 0

            else:
                rec.promedio_eje_1 = 0
                rec.promedio_eje_2 = 0
                rec.promedio_eje_3 = 0
                rec.promedio_eje_4 = 0
                rec.promedio_eje_5 = 0
                rec.promedio_eje_2_3 = 0
                rec.promedio_total_bruto = 0


class RegistroMedicionBasculasLinea(models.Model):
    _name = 'registro.medicion.basculas.linea'

    ensayo_id = fields.Many2one('registro.medicion.basculas', string='Ensayo')
    cant_ejes = fields.Integer(related='ensayo_id.cant_ejes', string='Cantidad de Ejes')
    velocidad_kmh = fields.Float('Velocidad (km/h)')
    velocidad_dinamica_kmh = fields.Float('Velocidad Dinámica (km/h)')
    eje_1 = fields.Float('E1 (Eje1)')
    eje_2 = fields.Float('E2 (Eje2)')
    eje_3 = fields.Float('E3 (Eje3)')
    eje_4 = fields.Float('E4 (Eje4)')
    eje_5 = fields.Float('E5 (Eje5)')
    computed_field = fields.Float('Compute Field', compute='_compute_custom_value')
    peso_bruto_total = fields.Float('Peso Bruto Total (kg)', compute='_compute_peso_bruto_total')

    @api.depends('eje_2', 'eje_3', 'eje_4', 'cant_ejes')
    def _compute_custom_value(self):
        for record in self:
            if record.cant_ejes <= 3:
                record.computed_field = record.eje_2 + record.eje_3
            else:
                record.computed_field = record.eje_3 + record.eje_4 + record.eje_5

    @api.model
    @api.depends('eje_1', 'eje_2', 'eje_3', 'eje_4', 'eje_5')
    def _compute_peso_bruto_total(self):
        for record in self:
            record.peso_bruto_total = record.eje_1 + record.eje_2 + record.eje_3 + record.eje_4 + record.eje_5
