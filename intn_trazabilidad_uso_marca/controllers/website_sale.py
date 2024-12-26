import os
import base64
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleInherit(WebsiteSale):

    @http.route(['/shop/payment/transaction/',
                 '/shop/payment/transaction/<int:so_id>',
                 '/shop/payment/transaction/<int:so_id>/<string:access_token>'],
                type='http', auth="public", website=True, methods=['POST'])
    def payment_transaction(self, acquirer_id, save_token=False, so_id=None, access_token=None, token=None,
                            **kwargs):
        order = None

        # Recuperar la orden de venta
        if so_id:
            domain = [('id', '=', so_id)]
            if access_token:
                domain.append(('access_token', '=', access_token))
            order = request.env['sale.order'].sudo().search(domain, limit=1)
        else:
            order = request.website.sale_get_order()

        if order:
            # Ruta al archivo estático
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),  # Ruta base del archivo Python
                '..', '..', 'static', 'src', 'img', 'comprobante.png'
            )
            order.service_type = 'onn_normas'

            try:
                # Leer el archivo estático
                with open(file_path, 'rb') as f:
                    file_data = f.read()

                # Guardar el archivo como adjunto relacionado con la orden de venta
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': 'Comprobante de Pago',
                    'datas': base64.b64encode(file_data).decode('utf-8'),
                    'res_model': 'sale.order',
                    'res_id': order.id,
                    'type': 'binary',
                })

                # Crear la factura desde la orden de venta
                if order.invoice_status == 'to invoice':
                    # Crear la factura
                    invoice = self._create_invoice_v12(order)
                    if invoice:
                        invoice.action_invoice_open()  # Publicar la factura
                        _logger.info(f"Factura creada y publicada para la orden {order.name}: {invoice.number}")

                # Crear y enviar el correo
                subject = f"Comprobante de Pago Recibido - Orden {order.name}"
                body = f"""
                        <p>Estimado {order.partner_id.name},</p>
                        <p>Hemos recibido el comprobante de pago para su orden <strong>{order.name}</strong>.</p>
                        <p>Adjuntamos el archivo recibido como comprobante. El proceso de verificación puede durar hasta 5 días. Una vez verificado le enviaremos un correo con la norma adquirida.</p>
                        <p>Gracias por su confianza.</p>
                        <p>Atentamente,<br/>{order.company_id.name}</p>
                    """
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': order.partner_id.email,
                    'attachment_ids': [(4, attachment.id)],
                }
                mail = request.env['mail.mail'].sudo().create(mail_values)
                mail.send()

            except FileNotFoundError:
                _logger.error(f"Archivo no encontrado: {file_path}")
            except Exception as e:
                _logger.error(f"Error al procesar el archivo estático: {e}")

        # Continuar con la lógica existente de transacción de pago
        return super(WebsiteSaleInherit, self).payment_transaction(
            acquirer_id, save_token, so_id, access_token, token, **kwargs
        )

    def _create_invoice_v12(self, sale_order):
        """
        Método para crear una factura en Odoo 12 desde un sale.order
        """
        try:
            invoice_id = sale_order.action_invoice_create()
            invoice = request.env['account.invoice'].browse(invoice_id)
            return invoice
        except Exception as e:
            _logger.error(f"Error al crear la factura para la orden {sale_order.name}: {e}")
            return None
