# import os
import base64
from odoo import api, models, _
import logging
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.constrains('residual', 'payment_ids')
    def _check_residual(self):
        for invoice in self:
            if invoice.residual <= 0 and invoice.origin:
                sale_order_id = self.env['sale.order'].sudo().search([('name', '=', invoice.origin)], limit=1)
                if sale_order_id and sale_order_id.service_type == 'onn_normas':
                    normas_documents = sale_order_id.order_line.mapped('product_id').mapped('product_tmpl_id').mapped(
                        'norma_document')

                    attachments = []
                    for norma, order_line in zip(normas_documents, sale_order_id.order_line):
                        if norma:  # Asegurarse de que el archivo PDF exista
                            # Decodificar los datos binarios del PDF
                            pdf_data = base64.b64decode(norma)
                            modified_pdf = self._add_footer_to_pdf(
                                pdf_data=pdf_data,
                                footer_text=f"Norma adquirida por {sale_order_id.partner_id.name}"
                            )
                            # Codificar de nuevo para almacenarlo como adjunto en Odoo
                            encoded_pdf = base64.b64encode(modified_pdf)

                            # Obtener un nombre adecuado para el archivo
                            pdf_name = order_line.product_id.name or "documento_norma"

                            # Crear un archivo adjunto en Odoo
                            attachment = self.env['ir.attachment'].create({
                                'name': f"{pdf_name}_modified.pdf",
                                'type': 'binary',
                                'datas': encoded_pdf,
                                'datas_fname': f"{pdf_name}_modified.pdf",
                                'res_model': 'sale.order',
                                'res_id': sale_order_id.id,
                            })
                            attachments.append(attachment)
                            # Agregar al chatter
                            invoice.message_post(
                                body=f"Se ha adjuntado el archivo de la norma: {pdf_name}_modified.pdf",
                                attachment_ids=[attachment.id]
                            )

                    # Crear y enviar el correo
                    self._send_email_with_attachments(
                        sale_order_id.partner_id.email,
                        f"Documentos Normativos para {sale_order_id.partner_id.name}",
                        f"Estimado {sale_order_id.partner_id.name},\n\nAdjunto encontrará los documentos normativos adquiridos.\n\nSaludos cordiales,\nSu Empresa",
                        attachments
                    )

    def _send_email_with_attachments(self, email_to, subject, body, attachments):
        """Enviar un correo con los archivos adjuntos."""
        if not email_to:
            _logger.warning("El cliente no tiene un correo electrónico configurado.")
            return

        # Crear el correo
        email_values = {
            'subject': subject,
            'body_html': "<p>{}</p>".format(body.replace('\n', '<br>')),
            'email_to': email_to,
            'attachment_ids': [(6, 0, [att.id for att in attachments])],
        }

        # Enviar el correo
        mail = self.env['mail.mail'].create(email_values)
        mail.send()

    def _add_footer_to_pdf(self, pdf_data, footer_text):
        """Agregar pie de página a un PDF usando PyPDF2 y reportlab."""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter

        # Agregar el texto en la parte inferior
        can.drawString(30, 15, footer_text)
        can.save()

        # Mover el contenido al inicio
        packet.seek(0)
        footer_pdf = PdfFileReader(packet)

        # Leer el PDF original
        original_pdf = PdfFileReader(io.BytesIO(pdf_data))
        writer = PdfFileWriter()

        # Combinar cada página del original con el pie de página
        for page_num in range(original_pdf.getNumPages()):
            page = original_pdf.getPage(page_num)
            page.mergePage(footer_pdf.getPage(0))
            writer.addPage(page)

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

