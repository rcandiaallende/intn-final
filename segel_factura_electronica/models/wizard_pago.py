from odoo import fields, api, models, exceptions


class WizardPago(models.TransientModel):
    _name = 'intn_intereses_mora.wizard_pago'

    factura_origen = fields.Many2one(
        'account.invoice', string="Factura origen")

    facturas_origen = fields.Many2many(
        'account.invoice', string="Facturas origen")

    fecha_pago = fields.Date(string="Fecha de pago",
                             default=lambda self:fields.Date.today(), required=True)
    dias_atraso = fields.Integer(
        string="Días de atraso", compute="get_intereses_acumulados")
    currency_id = fields.Many2one(
        'res.currency', related="factura_origen.currency_id")
    monto_interes = fields.Monetary(
        string="Interés por mora", compute="get_intereses_acumulados", currency_field="currency_id")

    def get_invoice_currency(self):
        return self.factura_origen.currency_id

    @api.depends('factura_origen', 'fecha_pago','facturas_origen')
    @api.onchange('fecha_pago')
    def get_intereses_acumulados(self):
        if self.factura_origen:
            invoice = self.factura_origen
            if invoice.state == 'open':
                data = invoice.calcular_intereses(invoice,self.fecha_pago)
                self.monto_interes = data.get('interes')
                self.dias_atraso = data.get('dias_atraso')
            else:
                self.monto_interes = 0
                self.dias_atraso = 0
        elif self.facturas_origen:
            monto_interes = 0
            dias_atraso = 0
            for factura in self.facturas_origen:
                if factura.state == 'open':
                    dias_atraso = (self.fecha_pago - factura.date_due).days
                    if dias_atraso > 0 and not factura.get_factura_mora_pagada():
                        porcentaje_mensual = float(
                            self.sudo().env['ir.config_parameter'].get_param('interes_mora_parameter'))
                        interes_mensual_base = factura.amount_total_company_signed * porcentaje_mensual / 100
                        interes_diario_base = float(interes_mensual_base / 30)
                        interes = dias_atraso * interes_diario_base
                        monto_interes = monto_interes + interes
            self.monto_interes = monto_interes
            self.dias_atraso = dias_atraso


    def button_confirmar(self):
        if self.monto_interes > 0:
            producto_interes_mora = self.env['product.template'].browse(
                int(self.sudo().env['ir.config_parameter'].get_param('producto_interes_mora_parameter')) or False)
            if not producto_interes_mora:
                raise exceptions.ValidationError(
                    'Se debe establecer un producto para los intereses por moras. Favor contacte con su administrador.')

            if self.factura_origen:
                for this in self.factura_origen:
                    lines = [(0, 0, {
                        'product_id': producto_interes_mora.product_variant_id.id,
                        'name': producto_interes_mora.name,
                        'quantity': 1,
                        'price_unit': self.monto_interes,
                        'account_id': producto_interes_mora.property_account_income_id.id,
                        'invoice_line_tax_ids': [[6, 0, producto_interes_mora.taxes_id.ids]]
                    })]

                    data = {
                        'partner_id': this.partner_id.id,
                        'date_invoice': fields.Date.today(),
                        'factura_origen_mora': this.id,
                        'invoice_line_ids': lines,
                        'origin': this.fake_number
                    }
                    factura_mora = self.env['account.invoice'].create(data)
                    this.write({'factura_mora': factura_mora.id})
                    view = self.env.ref('account.invoice_form')
                    return {
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'account.invoice',
                        'res_id': factura_mora.id,
                        'view_id': view.id,
                    }
            elif self.facturas_origen:
                origin = ''
                for factura in self.facturas_origen:
                    origin = origin + factura.fake_number + ','
                lines = [(0, 0, {
                    'product_id': producto_interes_mora.product_variant_id.id,
                    # 'name': producto_interes_mora.name,
                    'name':producto_interes_mora.name + ' correspondiente a las facturas ' + origin,
                    'quantity': 1,
                    'price_unit': self.monto_interes,
                    'account_id': producto_interes_mora.property_account_income_id.id,
                    'invoice_line_tax_ids': [[6, 0, producto_interes_mora.taxes_id.ids]]
                })]

                data = {
                    'partner_id': self.facturas_origen[0].partner_id.id,
                    'date_invoice': fields.Date.today(),
                    'facturas_origen_mora': [(6, 0, self.facturas_origen.ids)],
                    'invoice_line_ids': lines,
                    'origin': origin
                }
                factura_mora = self.env['account.invoice'].create(data)
                for factura in self.facturas_origen:
                    factura.write({'factura_mora': factura_mora.id})
                view = self.env.ref('account.invoice_form')
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'res_id': factura_mora.id,
                    'view_id': view.id,
                }
        else:
            if self.factura_origen:
                self.factura_origen.write({'desactivar_mora': True})
            elif self.facturas_origen:
                for factura in self.facturas_origen:
                    factura.write({'desactivar_mora':True})
