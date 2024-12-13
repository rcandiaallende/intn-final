from odoo import models, fields, api
from odoo.exceptions import UserError


class SolicitudImpresionesReportWizard(models.TransientModel):
    _name = 'solicitud.impresiones.report.wizard'
    _description = 'Wizard de Reporte de Solicitudes de Impresiones'

    fecha_desde = fields.Date(string="Fecha Desde", required=True)
    fecha_hasta = fields.Date(string="Fecha Hasta", required=True)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    certificado_ids = fields.Many2many('certificado.conformidad', string="Certificados")
    factura_ids = fields.Many2many('factura_comprobante', string="Facturas")
    def generar_reporte(self):
        # Filtrar las solicitudes de impresiones con el rango de fechas y cliente seleccionado
        domain = [('fecha_solicitud', '>=', self.fecha_desde),
                  ('fecha_solicitud', '<=', self.fecha_hasta)]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
            # Agregar filtro de certificados si se seleccionaron

        if self.certificado_ids:
            domain.append(('certificado_ids', 'in', self.certificado_ids.ids))

        # Agregar filtro de facturas si se seleccionaron
        if self.factura_ids:
            domain.append(('factura_ids', 'in', self.factura_ids.ids))

        # Obtener los registros que cumplen con los filtros
        solicitudes = self.env['solicitud.impresiones'].search(domain)

        # Generar el informe en PDF usando el template
        data = {'solicitudes': solicitudes.ids}  # Pasamos solo los IDs}
        raise UserError(solicitudes.ids)
        return self.env.ref('intn_trazabilidad_uso_marca.solicitud_impresiones_report_action').report_action(None, data=data)
