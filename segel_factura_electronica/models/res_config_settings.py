from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    interes_mora = fields.Float(string="Producto de Descuento", default_model='res.config.settings')

    producto_interes_mora = fields.Many2one('product.template', string='Producto de Mora',
                                            default_model='re.config.settings')

    @api.multi
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('interes_mora_parameter',
                                                  self.interes_mora)
        self.env['ir.config_parameter'].sudo().set_param('producto_interes_mora_parameter',
                                                  self.producto_interes_mora.id)
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            interes_mora=float(self.env['ir.config_parameter'].sudo().get_param('interes_mora_parameter')),
            producto_interes_mora=int(self.env['ir.config_parameter'].sudo().get_param('producto_interes_mora_parameter')) or False,

        )
        return res
