from odoo import fields, api, models, exceptions


class DeterminacionEnsayos(models.Model):
    _name = 'determinacion.ensayos'
    _description = "Determinacion de Ensayos"
    _order = 'create_date desc'

    name = fields.Char('Nombre', copy=False, required=True, track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')



class DeterminacionProductos(models.Model):
    _name = 'intn_trazabilidad_uso_marca.determinacion_productos'
    _description = "Determinacion de Productos"
    _order = 'name desc'

    name = fields.Char('', copy=False, required=False, track_visibility='onchange')
    product_id = fields.Many2one('product.template', string="Producto")
    determinacion_id = fields.Many2one('determinacion.ensayos', string="Determinación")
    solicitud_ensayo_line_id = fields.Many2one('solicitud.ensayos.lines', string="Soliciyud de Ensayo")
    display_type = fields.Selection([
        ('line_section', "Sección"),
        ('line_note', "Nota"),
        ('False', "Note")], default='False')
    sequence = fields.Integer('see', default=10)