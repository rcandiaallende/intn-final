# -*- coding: utf-8 -*-

from odoo import models, fields, api


# JERARQUIA DE SERVICIOS #
class Organismos(models.Model):
    _name = 'intn.organismos'
    _description = "Formulario para gestión de organismos"

    name = fields.Char(string="Nombre", required=True)
    observacion = fields.Text(string="Observación")
    terms = fields.Text(string="Términos y Condiciones")
    active = fields.Boolean(string="Activo", default=True)
    necesita_contrato = fields.Boolean(
        string="Se necesita contrato", default=False)
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        ondelete='cascade', string="Centro de Producción")
    responsable_id = fields.Many2one('res.users', string="Responsable")


class Unidades(models.Model):
    _name = 'intn.unidades'
    _description = "Formulario para gestión de unidades"

    name = fields.Char(string="Nombre", required=True)
    observacion = fields.Text(string="Observación")
    terms = fields.Text(string="Términos y Condiciones")
    active = fields.Boolean(string="Activo", default=True)
    necesita_contrato = fields.Boolean(
        string="Se necesita contrato", default=False)
    organismo_id = fields.Many2one('intn.organismos',
                                   ondelete='cascade', string="Organismo", required=True)
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        ondelete='cascade', string="Centro de Producción")
    responsable_id = fields.Many2one('res.users', string="Responsable")
    complete_name = fields.Char(string='Nombre', compute="completeNameUnidad")
    sequence_id = fields.Many2one(
        'ir.sequence', string="Secuencia para Nro. de informe por Unidad")
    genera_ordenes_cantidad = fields.Boolean(
        string='Genera OTs por cantidad unitaria', default=False)

    def completeNameUnidad(self):
        for this in self:
            if this.organismo_id:
                this.complete_name = this.organismo_id.name + ' / ' + this.name
            else:
                this.complete_name = this.name


class Departamentos(models.Model):
    _name = 'intn.departamentos'
    _description = "Formulario para gestión de departamentos"

    name = fields.Char(string="Nombre", required=True)
    observacion = fields.Text(string="Observación")
    terms = fields.Text(string="Términos y Condiciones")
    active = fields.Boolean(string="Activo", default=True)
    necesita_contrato = fields.Boolean(
        string="Se necesita contrato", default=False)
    unidad_id = fields.Many2one('intn.unidades',
                                ondelete='cascade', string="Unidad", required=True)
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        ondelete='cascade', string="Centro de Producción")
    responsable_id = fields.Many2one('res.users', string="Responsable")
    complete_name = fields.Char(
        string='Nombre', compute="completeNameDepartamento")
    sequence_id = fields.Many2one(
        'ir.sequence', string="Secuencia para Nro. de informe por Departamento")

    def completeNameDepartamento(self):
        for this in self:
            if this.unidad_id:
                this.complete_name = this.unidad_id.complete_name + ' / ' + this.name
            else:
                this.complete_name = this.name


class Coordinaciones(models.Model):
    _name = 'intn.coordinaciones'
    _description = "Formulario para gestión de coordinaciones"

    name = fields.Char(string="Nombre", required=True)
    observacion = fields.Text(string="Observación")
    terms = fields.Text(string="Términos y Condiciones")
    active = fields.Boolean(string="Activo", default=True)
    necesita_contrato = fields.Boolean(
        string="Se necesita contrato", default=False)
    departamento_id = fields.Many2one('intn.departamentos',
                                      ondelete='cascade', string="Departamento", required=True)
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        ondelete='cascade', string="Centro de Producción")
    responsable_id = fields.Many2one('res.users', string="Responsable")
    complete_name = fields.Char(
        string='Nombre', compute="completeNameCoordinacion")

    def completeNameCoordinacion(self):
        for this in self:
            if this.departamento_id:
                this.complete_name = this.departamento_id.complete_name + ' / ' + this.name
            else:
                this.complete_name = this.name


class Laboratorios(models.Model):
    _name = 'intn.laboratorios'
    _description = "Formulario para gestión de laboratorios"

    name = fields.Char(string="Nombre", required=True)
    observacion = fields.Text(string="Observación")
    terms = fields.Text(string="Términos y Condiciones")
    active = fields.Boolean(string="Activo", default=True)
    necesita_contrato = fields.Boolean(
        string="Se necesita contrato", default=False)
    coordinacion_id = fields.Many2one('intn.coordinaciones',
                                      ondelete='cascade', string="Coordinación", required=True)
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        ondelete='cascade', string="Centro de Producción")
    responsable_id = fields.Many2one('res.users', string="Responsable")
    complete_name = fields.Char(
        string='Nombre', compute="completeNameLaboratorio")
    responsables_ids = fields.Many2many('res.users', string="Responsables")

    def completeNameLaboratorio(self):
        for this in self:
            if this.coordinacion_id:
                this.complete_name = this.coordinacion_id.complete_name + ' / ' + this.name
            else:
                this.complete_name = this.name
