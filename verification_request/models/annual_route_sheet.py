from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AnnualRouteSheet(models.Model):
    _name = 'annual.route.sheet'
    _description = 'Hoja de Ruta Anual'
    _order = 'id desc'

    state_id = fields.Many2many('res.country.state', string="Departamento", domain="[('country_id', '=', 185)]")
    month = fields.Selection(
        [
            ('january', 'Enero'),
            ('february', 'Febrero'),
            ('march', 'Marzo'),
            ('april', 'Abril'),
            ('may', 'Mayo'),
            ('june', 'Junio'),
            ('july', 'Julio'),
            ('august', 'Agosto'),
            ('september', 'Septiembre'),
            ('october', 'Octubre'),
            ('november', 'Noviembre'),
            ('december', 'Diciembre'),
        ],
        string="Mes",
        required=True
    )
