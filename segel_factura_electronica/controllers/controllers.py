from urllib import request

from odoo import http
#from odoo.intn_addons.muk_utils.tools import json


# class InterfacesFacturas(http.Controller):
#     @http.route('/interfaces_facturas/interfaces_facturas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_facturas/interfaces_facturas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_facturas.listing', {
#             'root': '/interfaces_facturas/interfaces_facturas',
#             'objects': http.request.env['interfaces_facturas.interfaces_facturas'].search([]),
#         })

#     @http.route('/interfaces_facturas/interfaces_facturas/objects/<model("interfaces_facturas.interfaces_facturas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_facturas.object', {
#             'object': obj
#         })
