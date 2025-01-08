from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo import fields, http, _
from odoo.http import request
import hashlib
from datetime import datetime
import pytz


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

    @http.route(['/my/bascule_verification', '/my/bascule_verification/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_control_bascula(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        VerificationRequest = request.env['verification.request']

        # Inicializamos 'domain' con un filtro base
        domain = [
            ('state', '=', 'pending'),  # Filtro para estado "pending"
        ]

        searchbar_sortings = {
            'date': {'label': _('Request Date'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        # Default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        # Archivado y filtrado por fechas
        archive_groups = self._get_archive_groups('verification.request', domain)

        # Modificamos el dominio si las fechas están presentes
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # Count for pager
        request_count = VerificationRequest.search_count(domain)
        # Pager
        pager = portal_pager(
            url="/my/bascule_verification",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=request_count,
            page=page,
            step=self._items_per_page
        )
        # Content according to pager and archive selected
        requests = VerificationRequest.search(domain, order=sort_order, limit=self._items_per_page,
                                              offset=pager['offset'])
        request.session['my_requests_history'] = requests.ids[:100]

        values.update({
            'date': date_begin,
            'requests': requests.sudo(),
            'page_name': 'verification_request',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/bascule_verification',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("verification_request.portal_my_bascule_verification", values)

    @http.route('/verification_request/new/solicitud', type='http', auth='user', website=True)
    def new_solicitud(self, **kw):
        """
        Renderiza el formulario para una nueva solicitud.
        """
        session_uid = request.session.uid
        partner = None
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id

        fecha_actual = datetime.now(pytz.timezone(partner.tz or 'GMT')).strftime("%d/%m/%Y %H:%M")
        departments = request.env['res.country.state'].search([('country_id', '=', 185)])  # ID de Paraguay

        return request.render('verification_request.nueva_solicitud', {
            'fecha_actual': fecha_actual,
            'partner': partner,
            'page_name': 'solicitud',
            'departments': departments
        })
