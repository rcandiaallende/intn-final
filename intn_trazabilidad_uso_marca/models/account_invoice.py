# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'



    # @api.multi Todo: Se cambia el estado a agendado al modificar la fecha de programacion en la solicitud de calibracion
    # @api.constrains('residual', 'payment_ids')
    # def _check_residual(self):
    #     if self.residual <= 0:
    #         sale_order_id = self.env['sale.order'].sudo().search([('name', '=', self.origin)], limit=1)
    #         if sale_order_id and sale_order_id.calibration_request_id:
    #             calibration_request_id = sale_order_id.calibration_request_id
    #             calibration_request_id.state = 'scheduled'

