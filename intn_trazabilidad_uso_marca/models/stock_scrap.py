from odoo import models, fields, api, exceptions,_
from re import findall as regex_findall, split as regex_split

from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    impresion_etiquetas_id = fields.Many2one('impresion.etiquetas', required=False, string="Impresion de Etiquetas")

    def action_validate(self):
        res = super(StockScrap, self).action_validate()
        if self.impresion_etiquetas_id:
            if self.lot_id in self.impresion_etiquetas_id.lot_ids:
                self.impresion_etiquetas_id.write({'lot_ids':[(3, self.lot_id.id)]})

        return res
