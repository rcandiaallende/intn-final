# -- coding: utf-8 --

import hashlib
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import AccessError, MissingError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('pending', 'Pendiente Aprobación')])
    service_type = fields.Selection(string="Tipo servicio de Expediente",
                                    selection=[('onn_normas', 'ONN Normas'),
                                               ('metci', 'METCI'),
                                               ('reprint_onn_normas', 'Reimpresión ONN Normas')])
    calibration_request_id = fields.Many2one('calibration.request', string='Solicitud de Calibración')
    calibration_count = fields.Integer(string='Cantidad de Solicitud de Calibración',
                                       compute='_compute_calibration_ids_count')
    document_printing_count = fields.Integer(string='Cantidad Impresa', default=0)
    re_printing_so_ids = fields.Many2many(
        'sale.order',
        'sale_order_reprinting_rel',  # Nombre explícito de la tabla relacional
        'order_id',  # Campo de referencia al modelo actual
        'reprinting_id',  # Campo de referencia a las reimpresiones
        string='Re-impresiones asociadas'
    )
    retiro = fields.Selection([
        ('retiro_1', 'El Solicitante'),
        ('retiro_2', 'Un Tercero')
    ], string="Método de Retiro", required=True, default='retiro_1')
    retiro_tercero_nombre = fields.Char('Nombre del Tercero')
    retiro_tercero_documento = fields.Char('Documento del Tercero')
    ecommerce_payment_receipt = fields.Binary(string="Comprobante Pago E-commerce")

    @api.depends('calibration_request_id')
    def _compute_calibration_ids_count(self):
        for record in self:
            record.calibration_count = len(record.calibration_request_id)

    @api.multi
    def action_open_calibration_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'calibration.request',
            'view_mode': 'form',
            'res_id': self.calibration_request_id.id,
            'target': 'current',
        }

    def generate_unique_hash(self):
        order_id = str(self.id)  # Convertir el ID a cadena
        hash_object = hashlib.sha256(order_id.encode())  # Crear un hash SHA-256
        unique_hash = hash_object.hexdigest()  # Obtener el valor en formato hexadecimal
        return unique_hash

    def is_paid(self):
        for rec in self:
            if not rec.invoice_ids:
                return False
            if sum(rec.invoice_ids.mapped('residual')) <= 0:
                return True

    def approve_so(self):
        for rec in self:
            rec.action_confirm()
            if rec.calibration_request_id:
                # if not rec.calibration_request_id.work_date:
                #     raise UserError(_('Debe agendar una fecha para la realización del trabajo')) Todo: Se debe hacer la validacion al momento de pasar a agendado la Solicitud de calibracion
                rec.calibration_request_id.state = 'approved'
                production_ids = rec.env['mrp.production'].search([('origin', '=', rec.name)])
                if rec.calibration_request_id.ensure_one():  # Asegúrate de que sea un único registro
                    rec.calibration_request_id.production_ids = production_ids.ids if production_ids else None
            else:
                calibration_request = rec.env['calibration.request'].sudo().create({
                    'state': 'revision',
                    'partner_id': rec.partner_id.id,
                    'retiro': rec.retiro,
                    'retiro_tercero_nombre': rec.retiro_tercero_nombre,
                    'retiro_tercero_documento': rec.retiro_tercero_documento,
                    'order_id': rec.id
                })
                rec.calibration_request_id = calibration_request.id
                production_ids = rec.env['mrp.production'].search([('origin', '=', rec.name)])
                if calibration_request.ensure_one():
                    calibration_request.production_ids = production_ids.ids if production_ids else None
                if not rec or not rec.name:
                    raise UserError("El expediente no tiene un nombre válido.")

                email_to = rec.partner_id.email if rec.partner_id else None
                if not email_to:
                    raise UserError("El cliente no tiene un correo electrónico configurado.")

                subject = "Expediente Aprobado"
                body = f"""<p>Estimado cliente,

                    Su solicitud de presupuesto Nro. {rec.name} ha sido aprobada. Le recordamos que la vigencia es de 15 días corridos.
                    Para programar el servicio solicitado, el presupuesto debe ser abonado dentro del plazo de vigencia del presupuesto y remitido el 
                    comprobante de pago realizado al correo: facturacion@intn.gov.py.
                    </p>
                    </p>
                    Una vez confirmado el pago del presupuesto, dentro de los tres días siguientes recibirá una notificación de las fechas
                    programadas para la recepción de su/s instrumento/s. Le solicitamos tener en cuenta que, si sus instrumentos abarcan a 
                    más de un laboratorio, recibirá una notificación de agendamiento por cada laboratorio correspondiente.
                    En caso de no recibir la notificación de las fechas de recepción de su/s instrumento/s, favor contactar al Dpto.
                    de Tesorería, al teléfono: 021 2886000 int 1317 o 1318, o al correo electrónico: facturacion@intn.gov.py.
                    </p>
                    </p>
                    Le saludamos cordialmente,
                    </p>
                    </p>
                    Instituto Nacional de Tecnología, Normalización y Metrología</p>"""

            mail_values = {
                'subject': subject,
                'body_html': body,
                'message_type': 'email',
                'email_to': email_to,
                'author_id': self.env.user.partner_id.id,
            }

            # Crear y enviar el correo
            mail = rec.env['mail.mail'].sudo().create(mail_values)
            mail.send(auto_commit=True)
