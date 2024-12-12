# -*- coding: utf-8 -*-
from odoo import http

# class DetalleCobrosReport(http.Controller):
#     @http.route('/detalle_cobros_report/detalle_cobros_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/detalle_cobros_report/detalle_cobros_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('detalle_cobros_report.listing', {
#             'root': '/detalle_cobros_report/detalle_cobros_report',
#             'objects': http.request.env['detalle_cobros_report.detalle_cobros_report'].search([]),
#         })

#     @http.route('/detalle_cobros_report/detalle_cobros_report/objects/<model("detalle_cobros_report.detalle_cobros_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('detalle_cobros_report.object', {
#             'object': obj
#         })