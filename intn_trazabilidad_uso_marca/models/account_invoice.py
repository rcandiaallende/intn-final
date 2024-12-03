# -*- coding: utf-8 -*-

import hashlib
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import AccessError, MissingError, UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.constrains('residual', 'payment_ids')
    def _check_residual(self):
        if self.residual <= 0:
            sale_order_id = self.env['sale.order'].sudo().search([('name', '=', self.origin)], limit=1)
            if sale_order_id and sale_order_id.calibration_request_id:
                calibration_request_id = sale_order_id.calibration_request_id
                # workorder_id = self.env['mrp.workorder'].sudo().create({
                #     "name": str(calibration_request_id.id),
                #     "workcenter_id": 1,
                #     "production_id": 1,
                #     "date_planned_start": calibration_request_id.work_date
                # })
                # calibration_request_id.workorder_id = workorder_id.id
                calibration_request_id.state = 'scheduled'
