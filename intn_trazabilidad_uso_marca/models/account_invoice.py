# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.constrains('residual', 'payment_ids')
    def _check_residual(self):
        for invoice in self:
            if invoice.residual <= 0:
                # Buscar la orden de venta relacionada
                sale_order_id = self.env['sale.order'].sudo().search([('name', '=', invoice.origin)], limit=1)
                if sale_order_id and sale_order_id.service_type == 'onn_normas':
                    # Ruta al archivo estático
                    file_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),  # Ruta base del archivo Python
                        '..', '..', 'static', 'src', 'pdf', 'norma.pdf'
                    )
                    try:
                        # Leer el archivo PDF
                        with open(file_path, 'rb') as f:
                            file_data = f.read()

                        # Crear el adjunto en Odoo
                        attachment = self.env['ir.attachment'].sudo().create({
                            'name': 'Norma.pdf',
                            'datas': base64.b64encode(file_data).decode('utf-8'),
                            'res_model': 'sale.order',
                            'res_id': sale_order_id.id,
                            'type': 'binary',
                        })

                        # Preparar y enviar el correo
                        subject = f"Norma Adquirida - Orden {sale_order_id.name}"
                        body = f"""
                            <p>Estimado {sale_order_id.partner_id.name},</p>
                            <p>Gracias por completar el pago de su orden <strong>{sale_order_id.name}</strong>.</p>
                            <p>Adjuntamos el documento de la norma adquirida.</p>
                            <p>Atentamente,<br/>{sale_order_id.company_id.name}</p>
                        """
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': sale_order_id.partner_id.email,
                            'attachment_ids': [(4, attachment.id)],
                        }
                        mail = self.env['mail.mail'].sudo().create(mail_values)
                        mail.send()

                    except FileNotFoundError:
                        _logger.error(f"Archivo no encontrado: {file_path}")
                    except Exception as e:
                        _logger.error(f"Error al procesar el archivo PDF: {e}")
