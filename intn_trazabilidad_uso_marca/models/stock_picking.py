# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions,_
from re import findall as regex_findall, split as regex_split

from psycopg2 import OperationalError, Error

from odoo.osv import expression


from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    order_id = fields.Many2one('sale.order', string="Expediente", track_visibility="onchange")
    gestion_comprobante_id = fields.Many2one('gestion.comprobantes', string="Gestión de Comprobantes",
                                            track_visibility="onchange")


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    operacion_entrega_etiquetas = fields.Boolean('Entrega de etiquetas', track_visibility="onchange")