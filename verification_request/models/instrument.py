# -- coding: utf-8 --
from odoo import fields, models, api, _


class Instrument(models.Model):
    _name = "instrument"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Instrument code', required=True, copy=False, readonly=True,
                       default=lambda self: 'New')
    description = fields.Char(string='Nombre', tracking=True, default='Instrumento de Pesaje de Funcionamiento no automático (Báscula)')
    instrument_class = fields.Char(string='Clase', tracking=True)
    capacity = fields.Float(string='Capacidad', tracking=True)
    uom_id = fields.Many2one('uom.uom', string="Unidad de medida", ondelete='set null', tracking=True)
    type = fields.Selection([('dynamic', 'Dinámico'), ('mechanic', 'Mecánico'), ('hibrid', 'Hibrido'), ('electronic', 'Electrónico')], string="Sistema del Instrumento", tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    serial_number = fields.Char(string='Numero de Serie', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.instrument') or 'New'
        return super(Instrument, self).create(vals)