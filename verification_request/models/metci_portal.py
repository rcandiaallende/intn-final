from odoo import models, fields

class RegistryEntry(models.Model):
    _name = 'registry.entry'
    _description = 'Metci Portal'

    type_name = fields.Selection([
        ('persona_fisica', 'Persona Fisica'),
        ('person_juridica', 'Persona Juridica')
    ])
    type_document = fields.Selection([
        ('cedula', 'Cedula de Identidad Nacional'),
        ('ruc', 'Registro Unico del Contribuyente'),
        ('pasaporte', 'Pasaporte'),
        ('extranjero', 'Carnet de Extranjeria'),
        ('diplomatico', 'Ced. Diplomatica de identidad'),
    ])
    document_number = fields.Char(string="Número de Documento")
    name = fields.Char(string="Nombre")
    contry_id = fields.Many2one('res.country', string="Pais")
    cargo = fields.Char(string="Cargo")
    telefono_fijo = fields.Char(string="Telefono Fijo")
    telefono_celular = fields.Char(string="Telefono Celular")
    email = fields.Char(string="e-mail")
    password = fields.Char(string="Contraseña")
    password2 = fields.Char(string="Confirme Contraseña")
