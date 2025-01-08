import hashlib
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
import json
import datetime
import pytz
from datetime import datetime, timedelta

class IntnCamionesTanque(CustomerPortal):
    @http.route('/certificado_inspeccion_check', auth='public', website=True)
    def index(self, certificado_inspeccion_id, token):
        if token == self.genera_token(str(certificado_inspeccion_id)):
            certificado_inspeccion = request.env['certificado.inspeccion'].sudo().search(
                [('id', '=', int(certificado_inspeccion_id)), ('state', '=', 'done')]
            )
            if certificado_inspeccion:
                return request.render(
                    'intn_camiones_tanque.online_certificado_inspeccion',
                    {'certificado_inspeccion': certificado_inspeccion}
                )
            else:
                return request.render('intn_camiones_tanque.token_invalido')
        else:
            return request.render('intn_camiones_tanque.token_invalido')

    def genera_token(self, id_documento):
        palabra = id_documento + "amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra, 'utf-8')).hexdigest()

