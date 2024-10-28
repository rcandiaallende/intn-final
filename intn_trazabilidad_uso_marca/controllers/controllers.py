# -*- coding: utf-8 -*-
from odoo import http
import hashlib

class IntnTrazabilidadUsoMarca(http.Controller):
    @http.route('/licencia_conformidad_check', auth='public', website=True)
    def licencia_conformidad(self,licencia_conformidad_id,token):
        if token==self.genera_token(str(licencia_conformidad_id)):
            licencia_conformidad=http.request.env['licencia.conformidad'].sudo().search([('id','=',int(licencia_conformidad_id)),('state','=','done')])
            if licencia_conformidad:
                return http.request.render('intn_trazabilidad_uso_marca.online_licencia_conformidad',{'licencia_conformidad':licencia_conformidad})
            else:
                return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
        else:
            return http.request.render('intn_trazabilidad_uso_marca.token_invalido')

    def genera_token(self,id_documento):
        palabra=id_documento+"amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra,'utf-8')).hexdigest()

    @http.route('/licencia_conformidad_dos_check', auth='public', website=True)
    def licencia_conformidad_dos(self, licencia_conformidad_dos_id, token):
        if token == self.genera_token(str(licencia_conformidad_dos_id)):
            licencia_conformidad_dos = http.request.env['licencia.conformidad.dos'].sudo().search(
                [('id', '=', int(licencia_conformidad_dos_id)), ('state', '=', 'done')])
            if licencia_conformidad_dos:
                return http.request.render('intn_trazabilidad_uso_marca.online_licencia_conformidad_dos',
                                       {'licencia_conformidad_dos': licencia_conformidad_dos})
            else:
                return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
        else:
            return http.request.render('intn_trazabilidad_uso_marca.token_invalido')

    @http.route('/licencia_servicios_check', auth='public', website=True)
    def licencia_servicios(self, licencia_servicios_id, token):
        if token == self.genera_token(str(licencia_servicios_id)):
            licencia_servicios = http.request.env['licencia.servicios'].sudo().search(
                [('id', '=', int(licencia_servicios_id)), ('state', '=', 'done')])
            if licencia_servicios:
                return http.request.render('intn_trazabilidad_uso_marca.online_licencia_servicios',
                                       {'licencia_servicios': licencia_servicios})
            else:
                return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
        else:
            return http.request.render('intn_trazabilidad_uso_marca.token_invalido')

    @http.route('/SERVICIOSPC/<int:id>/<string:token>', auth='public', website=True)
    def licencia_servicios_public(self, id=None, token=None):
        if token == self.genera_token(str(id)).upper()[0:10]:
            licencia_servicios = http.request.env['licencia.servicios'].sudo().search(
                [('id', '=', int(id)), ('state', '=', 'done')])
            if licencia_servicios:
                return http.request.render('intn_trazabilidad_uso_marca.public_licencia_servicios',
                                           {'licencia_servicios': licencia_servicios})
            else:
                return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
        else:
            return http.request.render('intn_trazabilidad_uso_marca.token_invalido')

    @http.route('/certificado_conformidad_check', auth='public', website=True)
    def certificado_conformidad(self, certificado_conformidad_id, token):
        if token == self.genera_token(str(certificado_conformidad_id)):
            certificado_conformidad = http.request.env['certificado.conformidad'].sudo().search(
                [('id', '=', int(certificado_conformidad_id)), ('state', '=', 'done')])
            if certificado_conformidad:
                return http.request.render('intn_trazabilidad_uso_marca.online_certificado_conformidad',
                                           {'certificado_conformidad': certificado_conformidad})
            else:
                return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
        else:
            return http.request.render('intn_trazabilidad_uso_marca.token_invalido')
