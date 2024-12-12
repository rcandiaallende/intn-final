# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class ListadoNotasCreditoReportWizard(models.TransientModel):
    _name = 'listado_notas_credito.report.wizard'

    date_start = fields.Date(string="Fecha Inicio", required=True, default=fields.Date.today)
    date_end = fields.Date(string="Fecha Final", required=True, default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    show_invoices = fields.Boolean('Mostrar facturas de origen anuladas o modificadas (conciliadas)', default=True)

    @api.multi
    def get_report(self):
        if self.date_start > self.date_end:
            raise ValueError("La fecha de inicio no puede ser mayor a la fecha final.")

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'partner_id': self.partner_id.id,
                'show_invoices': self.show_invoices,
            },
        }

        # Generar ambas opciones de informe
        report_refs = []
        if self.show_invoices:
            report_refs.append(self.env.ref('listado_notas_credito_report_sifen.recap_report_sifen').report_action(self, data=data))
        report_refs.append(self.env.ref('listado_notas_credito_report.recap_report').report_action(self, data=data))

        return report_refs


class ReportListadoNotasCredito(models.AbstractModel):

    _name = 'listado_notas_credito_report_sifen.recap_report_sifen_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        partner_id = data['form'].get('partner_id')
        show_invoices = data['form'].get('show_invoices', True)

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        start_report = date_start_obj.strftime('%d/%m/%Y')
        end_report = date_end_obj.strftime('%d/%m/%Y')

        domain = [
            ('type', '=', 'out_refund'),
            ('state', 'in', ['open', 'paid', 'cancel']),
            ('date_invoice', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
            ('date_invoice', '<=', date_end_obj.strftime(DATETIME_FORMAT)),
            ('tax_line_ids', '!=', False),
        ]

        if partner_id:
            domain.append(('partner_id', 'child_of', partner_id))

        facturas = self.env['account.invoice'].search(domain)

        if show_invoices:
            facturas = facturas.filtered(lambda x: x.matched_invoice_ids)

        docs = sorted(facturas, key=lambda x: (x.date_invoice, x.fake_number))

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_report,
            'date_end': end_report,
            'docs': docs,
        }
