# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class ListadoNotasCreditoReportWizard(models.TransientModel):
    _name = 'listado_notas_credito.report.wizard'

    date_start = fields.Date(string="Fecha Inicio", required=True, default=fields.Date.today)
    date_end = fields.Date(string="Fecha Final", required=True, default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string="Cliente")

    def check_report(self):
        data = {}
        data['form'] = self.read(['date_start', 'date_end', 'partner_id'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['date_start', 'date_end', 'partner_id'])[0])
        return self.env.ref('listado_notas_credito_report.recap_report_sifen').report_action(self, data=data)


class ReportListadoNotasCredito(models.AbstractModel):

    _name = 'report.listado_notas_credito_report.recap_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        Model = self.env.context.get('active_model')
        docs = self.env[Model].browse(self.env.context.get('active_id'))
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        partner_id = data['form']['partner_id']

        start_report = date_start_obj.strftime('%d/%m/%Y')
        end_report = date_end_obj.strftime('%d/%m/%Y')

        if partner_id:
            facturas = self.env['account.invoice'].search(
                [('type', '=', 'out_refund'), ('state', 'in', ['open', 'paid', 'cancel']),
                 ('date_invoice', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
                 ('date_invoice', '<=', date_end_obj.strftime(DATETIME_FORMAT)),
                 ('tax_line_ids', '!=', False)]).filtered(lambda x: x.partner_id.id == partner_id or x.partner_id.parent_id.id == partner_id)
        else:
            facturas = self.env['account.invoice'].search(
                [('type', '=', 'out_refund'), ('state', 'in', ['open', 'paid', 'cancel']),
                 ('date_invoice', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
                 ('date_invoice', '<=', date_end_obj.strftime(DATETIME_FORMAT)), ('tax_line_ids', '!=', False)])

        facturas_report = sorted(facturas, key=lambda x: x.fake_number)
        facturas_report = sorted(facturas_report, key=lambda x: x.date_invoice)
        return {
            'doc_ids': self.ids,
            'doc_model': Model,
            'date_start': start_report,
            'date_end': end_report,
            'docs': docs,
            'facturas_report': facturas_report
        }
