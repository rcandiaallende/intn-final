from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    fe_production = fields.Boolean(string='Facturación Electrónica Producción')
    fe_test = fields.Boolean(string='Test de Facturación Electrónica')
    fe_no_send_sifen = fields.Boolean(string='Sin Enviar a Sifen')
