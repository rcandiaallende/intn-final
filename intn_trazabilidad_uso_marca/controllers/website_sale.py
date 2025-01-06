import os
import base64
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
from odoo.exceptions import AccessError, MissingError, UserError

_logger = logging.getLogger(__name__)


class WebsiteSaleInherit(WebsiteSale):

    @http.route('/shop/payment/upload_attachment', type='http', auth='public', website=True, csrf=False)
    def upload_payment_attachment(self, **kwargs):
        # Obtener la orden activa
        order = request.website.sale_get_order()
        if not order or order.state != 'draft':
            return request.redirect('/shop')  # Redirigir si no hay orden activa

        # Validar que se subió un archivo
        uploaded_file = kwargs.get('order_attachment')
        if not uploaded_file:
            return request.redirect('/shop/payment?error=no_file')

        # Convertir archivo a base64
        file_content = uploaded_file.read()
        file_name = uploaded_file.filename
        encoded_file = base64.b64encode(file_content)
        # Vincular el adjunto al SO
        order.ecommerce_payment_receipt = encoded_file

        # Crear el adjunto
        attachment = request.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'datas': encoded_file,
            'res_model': 'sale.order',
            'res_id': order.id,
            'mimetype': uploaded_file.content_type,
        })

        # Mensaje de éxito (opcional)
        request.session['upload_success'] = True

        # Redirigir a la página de pago para continuar con el proceso normal
        return request.redirect('/shop/payment')

    @http.route(['/shop/payment/transaction/',
                 '/shop/payment/transaction/<int:so_id>',
                 '/shop/payment/transaction/<int:so_id>/<string:access_token>'],
                type='json', auth="public", website=True, methods=['POST'])
    def payment_transaction(self, acquirer_id, save_token=False, so_id=None, access_token=None, token=None,
                            **kwargs):
        order = None
        if so_id:
            domain = [('id', '=', so_id)]
            if access_token:
                domain.append(('access_token', '=', access_token))
            order = request.env['sale.order'].sudo().search(domain, limit=1)
        else:
            order = request.website.sale_get_order()

        if order:
            order.service_type = 'onn_normas'
            order.action_confirm()
            for line in order.order_line:
                line.qty_to_invoice = line.product_uom_qty
            order.invoice_status = 'to invoice'

            # Crear la factura
            invoice = self._create_invoice_v12(order)
            if invoice:
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
            }
            mail = request.env['mail.mail'].sudo().create(mail_values)
            mail.send()

        return super(WebsiteSaleInherit, self).payment_transaction(
            acquirer_id=acquirer_id, save_token=save_token, so_id=so_id, access_token=access_token,
            token=token, **kwargs
        )

    def _create_invoice_v12(self, sale_order):
        try:
            invoice_id = sale_order.sudo().action_invoice_create(grouped=True)
            invoice = request.env['account.invoice'].sudo().browse(invoice_id)
            attachment = request.env['ir.attachment'].sudo().create({
                'name': 'Comprobante_transferencia',
                'type': 'binary',
                'datas': sale_order.ecommerce_payment_receipt,
                'res_model': 'account.invoice',
                'res_id': invoice.id,
            })
            invoice.ecommerce_payment_receipt = sale_order.ecommerce_payment_receipt
            invoice.sudo().action_move_create()
            invoice.sudo().invoice_validate()
            return invoice
        except Exception as e:
            _logger.error(f"Error al crear la factura para la orden {sale_order.name}: {e}")
            return None
