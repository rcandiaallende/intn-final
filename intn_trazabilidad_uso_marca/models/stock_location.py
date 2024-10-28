# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ , exceptions


class StockLocation(models.Model):
    _inherit = "stock.location"


    location_to_print = fields.Boolean('Ubicación "Etiquetas a imprimir"', default=False)
    location_printed = fields.Boolean('Ubicación "Etiquetas impresas"', default=False)