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
                'date_start': self.date_start,
                'date_end': self.date_end,
                'partner_id': self.partner_id.id,
            },
        }

        return self.env.ref('intn_trazabilidad_uso_marca.solicitud_impresiones_report_action').report_action(self,
                                                                                                             data=data)


class ReportListadoNotasCredito(models.AbstractModel):
    _name = 'intn_trazabilidad_uso_marca.solicitud_impresiones_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['fecha_desde']
        date_end = data['form']['fecha_hasta']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        partner_id = data['form']['partner_id']

        start_report = date_start_obj.strftime('%d/%m/%Y')
        end_report = date_end_obj.strftime('%d/%m/%Y')

        domain = [('fecha_solicitud', '>=', start_report),
                  ('fecha_solicitud', '<=', end_report)]

        if partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
            # Agregar filtro de certificados si se seleccionaron

        # if self.certificado_ids:
        #     domain.append(('certificado_ids', 'in', self.certificado_ids.ids))
        #
        # # Agregar filtro de facturas si se seleccionaron
        # if self.factura_ids:
        #     domain.append(('factura_ids', 'in', self.factura_ids.ids))

        # Obtener los registros que cumplen con los filtros
        solicitudes = self.env['solicitud.impresiones'].search(domain)

        # Generar el informe en PDF usando el template
        data = {'solicitudes': solicitudes.ids}  # Pasamos solo los IDs}

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_report,
            'date_end': end_report,
            'docs': solicitudes,
        }

    # def generar_reporte(self):
    #     # Filtrar las solicitudes de impresiones con el rango de fechas y cliente seleccionado
    #     domain = [('fecha_solicitud', '>=', self.fecha_desde),
    #               ('fecha_solicitud', '<=', self.fecha_hasta)]
    #
    #     if self.partner_id:
    #         domain.append(('partner_id', '=', self.partner_id.id))
    #         # Agregar filtro de certificados si se seleccionaron
    #
    #     if self.certificado_ids:
    #         domain.append(('certificado_ids', 'in', self.certificado_ids.ids))
    #
    #     # Agregar filtro de facturas si se seleccionaron
    #     if self.factura_ids:
    #         domain.append(('factura_ids', 'in', self.factura_ids.ids))
    #
    #     # Obtener los registros que cumplen con los filtros
    #     solicitudes = self.env['solicitud.impresiones'].search(domain)
    #
    #     # Generar el informe en PDF usando el template
    #     data = {'solicitudes': solicitudes.ids}  # Pasamos solo los IDs}
    #     # raise UserError(solicitudes.ids)
    #     return self.env.ref('intn_trazabilidad_uso_marca.solicitud_impresiones_report_action').report_action(None,
    #                                                                                                          data=data)
