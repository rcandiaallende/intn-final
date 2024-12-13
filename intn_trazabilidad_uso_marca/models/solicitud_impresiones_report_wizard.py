from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime


class SolicitudImpresionesReportWizard(models.TransientModel):
    _name = 'solicitud.impresiones.report.wizard'
    _description = 'Wizard de Reporte de Solicitudes de Impresiones'

    fecha_desde = fields.Date(string="Fecha Desde", required=True)
    fecha_hasta = fields.Date(string="Fecha Hasta", required=True)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    certificado_ids = fields.Many2many('certificado.conformidad', string="Certificados")
    factura_ids = fields.Many2many('factura_comprobante', string="Facturas")

    @api.multi
    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.fecha_desde,
                'date_end': self.fecha_hasta,
                'partner_id': self.partner_id.id,
            },
        }

        return self.env.ref('intn_trazabilidad_uso_marca.solicitud_impresiones_report_action').report_action(self,
                                                                                                             data=data)


class ReportListadoNotasCredito(models.AbstractModel):
    _name = 'report.intn_trazabilidad_uso_marca.reporte_impresion'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']  # Se espera que esté en formato ISO
        date_end = data['form']['date_end']  # Se espera que esté en formato ISO

        # Validar si las fechas ya están en formato ISO
        try:
            datetime.strptime(date_start, '%Y-%m-%d')  # Validar formato ISO
            datetime.strptime(date_end, '%Y-%m-%d')    # Validar formato ISO
        except ValueError:
            raise ValueError("El formato de las fechas no es válido. Se esperaba '%Y-%m-%d'.")

        partner_id = data['form']['partner_id']

        domain = [
            ('fecha_solicitud', '>=', date_start),
            ('fecha_solicitud', '<=', date_end),
        ]

        if partner_id:
            domain.append(('partner_id', '=', partner_id))
            # Filtros adicionales (certificados o facturas)
            # if data['form'].get('certificado_ids'):
            #     domain.append(('certificado_ids', 'in', data['form']['certificado_ids']))
            # if data['form'].get('factura_ids'):
            #     domain.append(('factura_ids', 'in', data['form']['factura_ids']))

        # Buscar registros en base al dominio
        solicitudes = self.env['solicitud.impresiones'].search(domain)

        # Retornar los valores para generar el informe
        return {
            'doc_ids': solicitudes.ids,
            'doc_model': self.env['solicitud.impresiones']._name,
            'date_start': date_start,
            'date_end': date_end,
            'docs': solicitudes,
        }
