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
        DATE_FORMAT = '%Y-%m-%d'
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']

        # Convertimos las fechas de entrada al formato ISO
        date_start_obj = datetime.strptime(date_start, '%d/%m/%Y')  # Entrada original
        date_end_obj = datetime.strptime(date_end, '%d/%m/%Y')  # Entrada original

        date_start_iso = date_start_obj.strftime(DATE_FORMAT)  # Formato ISO
        date_end_iso = date_end_obj.strftime(DATE_FORMAT)  # Formato ISO

        partner_id = data['form']['partner_id']

        domain = [
            ('fecha_solicitud', '>=', date_start_iso),
            ('fecha_solicitud', '<=', date_end_iso)
        ]

        if partner_id:
            domain.append(('partner_id', '=', partner_id))
            # Agregar filtro de certificados si se seleccionaron
            # if data['form'].get('certificado_ids'):
            #     domain.append(('certificado_ids', 'in', data['form']['certificado_ids']))
            # Agregar filtro de facturas si se seleccionaron
            # if data['form'].get('factura_ids'):
            #     domain.append(('factura_ids', 'in', data['form']['factura_ids']))

        # Obtener los registros que cumplen con los filtros
        solicitudes = self.env['solicitud.impresiones'].search(domain)

        # Generar el informe en PDF usando el template
        return {
            'doc_ids': solicitudes.ids,
            'doc_model': self.env['solicitud.impresiones']._name,
            'date_start': date_start,
            'date_end': date_end,
            'docs': solicitudes,
        }