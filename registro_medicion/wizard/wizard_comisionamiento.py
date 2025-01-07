from odoo import models, fields, api
import time


class ReporteComisionamientoWizard(models.TransientModel):
    _name = 'reporte.comisionamiento.wizard'
    _description = 'Wizard para generar reporte de comisionamiento'

    fecha_inicio = fields.Date(string="Fecha Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha Fin", required=True)
    area = fields.Char(string="Área")
    mision = fields.Char(string="Misión")
    estado_movil = fields.Char(string="Estado del Móvil")
    descripcion_inconvenientes = fields.Char(string="Descripción de Inconvenientes")

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id.id

    @api.model
    def _get_default_journals(self):
        journals = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id)])
        return journals.mapped('id')

    def check_report(self):
        data = {}
        data['form'] = self.read(['fecha_inicio', 'fecha_fin'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['fecha_inicio', 'fecha_fin'])[0])
        return self.env.ref('registro_medicion.reporte_comisionamiento_action').report_action(self, data=data)

    def agregar_punto_de_miles(self, numero):
        numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[::-1]
        num_return = numero_con_punto
        return num_return


class ReportDailyBook(models.AbstractModel):
    _name = 'report.registro_medicion.reporte_comisionamiento_template'
    _description = "Reporte de Registro de Medición"

    def _get_report_values(self, docids, data=None):
        Model = self.env.context.get('active_model')
        docs = self.env[Model].browse(self.env.context.get('active_id'))

        docargs = {
            'doc_ids': self.ids,
            'doc_model': Model,
            'docs': docs,
            'time': time,
        }

        return docargs