from odoo import fields, api, models, exceptions


class ColorAnillos(models.Model):
    _name = 'intn_trazabilidad_uso_marca.color_anillos'
    _description= 'Color de Anillos de Seguridad'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Color', required=True)
    active = fields.Boolean(string="Activo", default=True)


    @api.model
    def year_selection(self):
        year = 2020  # replace 2000 with your a start year
        year_list = []
        while year != 2030:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    year = fields.Selection(year_selection, string='Año',store=True, required=True, track_visibility='onchange')
