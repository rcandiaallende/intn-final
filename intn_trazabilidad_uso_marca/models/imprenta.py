from odoo import models, fields

class Imprenta(models.Model):
    _name = 'imprenta'
    _description = 'Imprenta'

    name = fields.Char(string='Nombre', required=True)
    direccion = fields.Char(string='Dirección')
    email = fields.Char(string='Correo Electrónico')
    telefono = fields.Char(string='Teléfono')
    sucursal = fields.Char(string='Sucursal')
