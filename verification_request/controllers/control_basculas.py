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



class CustomerPortal(CustomerPortal):

    @http.route('/my/imprimir-certificado/<int:certificado_id>', type='http', auth="user", website=True)
    def imprimir_norma(self, certificado_id, **kw):
        certificado = request.env['verification.request'].browse(certificado_id)

        certificado = certificado.sudo()

        if not certificado.exists():
            return "Registro no encontrada"

        if certificado.state == 'verified':
            report = request.env.ref('verification_request.action_report_certificado_aprobado')
        else:
            report = request.env.ref('verification_request.action_report_impossibility')

        pdf_content, content_type = report.sudo().render_qweb_pdf([certificado.id])

        if not pdf_content:
            return "Error al generar el PDF"

        return request.make_response(pdf_content, headers=[('Content-Type', content_type), (
            'Content-Disposition', 'attachment; filename="reporte.pdf"')])

    @http.route('/verification_request/new/solicitud1/', type='http', auth='user', website=True)
    def new_solicitud_verification_bascula(self, **kw):
        """
        Renderiza el formulario para una nueva solicitud.
        """
        session_uid = request.session.uid
        partner = None
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id

        fecha_actual = datetime.now(pytz.timezone(partner.tz or 'GMT')).strftime("%d/%m/%Y %H:%M")
        departments = request.env['res.country.state'].search([('country_id', '=', 185)])  # ID de Paraguay

        return request.render('verification_request.nueva_solicitud1', {
            'fecha_actual': fecha_actual,
            'partner': partner,
            'page_name': 'solicitud',
            'departments': departments
        })

    @http.route('/verification_request/save/solicitud', type='http', auth='user', website=True, csrf=True)
    def save_solicitud(self, **kw):
        """
        Guarda la nueva solicitud en el modelo correspondiente.
        """
        try:
            # Obtener la zona horaria del usuario y la fecha actual
            partner = request.env['res.users'].browse(request.session.uid).partner_id
            fecha_actual = datetime.now(pytz.timezone(partner.tz or 'GMT')).date()  # Fecha en formato YYYY-MM-DD

            values = {
                'partner_id': partner.id,
                'state_id': [(6, 0, [int(dep) for dep in kw.get('department', '').split(',')])],
                'month': kw.get('month'),
                'observation': kw.get('observation'),
                'request_date': fecha_actual,  # Fecha de solicitud automática
                'request_date2': fecha_actual
            }

            solicitud = request.env['verification.request'].sudo().create(values)

            return request.render('verification_request.solicitud_creada', {
                'solicitud': solicitud,
                'page_name': 'solicitud'
            })
        except Exception as e:
            request.env.cr.rollback()  # Asegúrate de finalizar la transacción fallida
            return request.render('verification_request.solicitud_error', {
                'error': str(e),
                'page_name': 'solicitud'
            })

    @http.route('/get_months_by_department', type='json', auth='user')
    def get_months_by_department(self, state_ids):
        """
        Devuelve los meses disponibles según los departamentos seleccionados.
        """
        if not state_ids:
            return {'error': 'No se seleccionaron departamentos.'}

        # Buscar registros que coincidan con los departamentos seleccionados
        records = request.env['annual.route.sheet'].search([('state_id', 'in', state_ids)])
        months = {rec.month for rec in records}

        # Obtener los nombres de los meses desde las selecciones del modelo
        month_labels = dict(request.env['annual.route.sheet']._fields['month'].selection)

        return {'months': [{'value': month, 'label': month_labels[month]} for month in months]}

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = None

        session_uid = request.session.uid
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id

        solicitudes = request.env['verification.request']
        solicitud_count = solicitudes.search_count([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ['duplicate', 'canceled_due_closure', 'cancel'])
        ])

        values.update({
            'solicitudes_camiones_count': solicitud_count,
        })

        return values

    @http.route(['/my/camiones/solicitudes/<int:solicitud_id>'], type='http', auth="public", website=True)
    def solicitud_camion_info(self, solicitud_id, report_type=None, access_token=None, message=False, download=False,
                              **kw):
        try:
            solicitud_sudo = self._document_check_access('intn_camiones_tanque.solicitudes', solicitud_id,
                                                         access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=solicitud_sudo, report_type=report_type,
                                     report_ref='intn_camiones_tanque.reporte_solicitud', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if solicitud_sudo and request.session.get(
                'view_quote_%s' % solicitud_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % solicitud_sudo.id] = now
            body = _('Solicitud vista por el cliente')
            _message_post_helper(res_model='intn_camiones_tanque.solicitudes', res_id=solicitud_sudo.id, message=body,
                                 token=solicitud_sudo.access_token, message_type='notification', subtype="mail.mt_note",
                                 partner_ids=solicitud_sudo.partner_id.user_id.sudo().partner_id.ids)

        values = {
            'solicitud': solicitud_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': solicitud_sudo.partner_id.id,
            'report_type': 'html',
            'page_name': 'solicitud',
        }
        if solicitud_sudo.company_id:
            values['res_company'] = solicitud_sudo.company_id

        if solicitud_sudo.state in ('draft', 'done', 'reagendado', 'cancel'):
            history = request.session.get('my_agendamientos_history', [])
        else:
            history = request.session.get('my_agendamientos_history', [])
        values.update(get_records_pager(history, solicitud_sudo))

        return request.render('intn_camiones_tanque.solicitud_agendamiento_portal_template', values)

    @http.route(['/my/bascule_verification1', '/my/bascule_verification/page/<int:page>'], type='http', auth="user",
                website=True)
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
            url="/my/bascule_verification1",
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
        return request.render("verification_request.portal_my_bascule_verification1", values)

    @http.route('/verification_request/save/solicitud', auth='user', website=True, )
    def save_solicitud_agendamiento(self, **kw):
        partner = request.env['res.users'].browse(request.session.uid).partner_id.id

        my_datetime = kw['request_date2']
        fecha_actual = kw['request_date']

        values = {
            'partner_id': partner,
            'request_date': fecha_actual,
            'request_date2': my_datetime,
            'instrument': kw['instrument'],
            'quantity': kw['quantity'],
            'observation': kw['observation'],
        }

        try:
            solicitud = request.env['verification.request'].sudo().create(values)

            # documentos = kw['documentos']
            #
            # doc = documentos.read()
            # doc = base64.b64encode(doc)
            # vals = {
            #     'datas': doc,
            #     'name': documentos.filename,
            #     'datas_fname': documentos.filename,
            #     'type': 'binary'
            # }
            # solicitud.write({'documentos': [(0, 0, vals)]})

            return http.request.render('verification_request.solicitud_creada',
                                       {'solicitud': solicitud, 'page_name': 'solicitud'})
        except ValueError:
            return False


@http.route('/camiones/save/camion', auth='user', website=True)
def save_camion(self, **kw):
    partner = kw['partner']

    if 'modelo' in kw:
        modelo = kw['modelo']
    else:
        modelo = False

    values = {
        'partner_id': partner,
        'marca_id': kw['marca'],
        'modelo_id': modelo,
        'year': kw['year'],
        'chasis': kw['chasis'],
        'fabricante_cisterna': kw['fabricante'],
        'year_fabricacion': kw['year_fabricacion'],
        'emblema_id': kw['emblema'],
        'codigo_emblema_char': kw['codigo_emblema'],
        'matricula_camion': kw['matricula_camion'],
        'matricula_cisterna': kw['matricula_cisterna'],
        'cantidad_compartimientos': kw['cantidad_compartimientos'],
        'capacidad': kw['capacidad']
    }

    camion = request.env['camiones.cisterna'].sudo().create(values)

    session_uid = request.session.uid
    if session_uid:
        partner = request.env['res.users'].browse(request.session.uid).partner_id
        sucursales = partner.child_ids

    fecha_actual = datetime.now(pytz.timezone(partner.tz or 'GMT')).strftime("%d/%m/%Y %H:%M")
    fecha_actual_diez = datetime.now(pytz.timezone(partner.tz or 'GMT')) + timedelta(days=1)
    fecha_actual_diez = fecha_actual_diez.strftime("%Y-%m-%d")

    camiones = []

    marcas = request.env['fleet.vehicle.model.brand'].search([('name', '!=', False)])
    modelos = request.env['fleet.vehicle.model'].search([])
    emblemas = request.env['emblemas'].search([('active', '=', True)])

    acoplados = request.env['acoplados'].search([('partner_id', '=', partner.id)])

    if partner.child_ids:
        acoplados = request.env['acoplados'].search(
            ['|', ('partner_id', '=', partner.child_ids.ids), ('partner_id', '=', partner.id)])

    if partner.camiones_ids:
        camiones = partner.camiones_ids

    if partner.child_ids:
        child_camiones = partner.mapped('child_ids').mapped('camiones_ids')
        if not partner.camiones_ids:
            camiones = child_camiones
        else:
            camiones = camiones + child_camiones

    return http.request.render('intn_camiones_tanque.nueva_solicitud1',
                               {'fecha_actual': fecha_actual, 'partner': partner, 'page_name': 'solicitud',
                                'sucursales': sucursales, 'camiones': camiones, 'marcas': marcas,
                                'modelos': modelos, 'emblemas': emblemas, 'camionC': camion, 'acopladoA': False,
                                'fecha_actual_diez': fecha_actual_diez, 'acoplados': acoplados})


@http.route('/camiones/save/acoplado', auth='user', website=True)
def save_acoplado(self, **kw):
    partner = kw['partner']

    values = {
        'partner_id': partner,
        'marca_acoplado_id': kw['marca_acople'],
        'chasis_acoplado': kw['chasis_acople'],
        'fabricante_acoplado': kw['fabricante_acople'],
        'year_fabricacion': kw['year_fabricacion_acople'],
        'matricula_acoplado': kw['matricula_acople'],
        'cantidad_compartimientos': kw['cantidad_compartimientos_acople'],
        'capacidad': kw['capacidad_acople']
    }

    acoplado = request.env['acoplados'].sudo().create(values)

    session_uid = request.session.uid
    if session_uid:
        partner = request.env['res.users'].browse(request.session.uid).partner_id
        sucursales = partner.child_ids

    fecha_actual = datetime.now(pytz.timezone(partner.tz or 'GMT')).strftime("%d/%m/%Y %H:%M")
    fecha_actual_diez = datetime.now(pytz.timezone(partner.tz or 'GMT')) + timedelta(days=1)
    fecha_actual_diez = fecha_actual_diez.strftime("%Y-%m-%d")

    camiones = []

    marcas = request.env['fleet.vehicle.model.brand'].search([('name', '!=', False)])
    modelos = request.env['fleet.vehicle.model'].search([])
    emblemas = request.env['emblemas'].search([('active', '=', True)])

    acoplados = request.env['acoplados'].search([('partner_id', '=', partner.id)])

    if partner.child_ids:
        acoplados = request.env['acoplados'].search(
            ['|', ('partner_id', '=', partner.child_ids.ids), ('partner_id', '=', partner.id)])

    if partner.camiones_ids:
        camiones = partner.camiones_ids

    if partner.child_ids:
        child_camiones = partner.mapped('child_ids').mapped('camiones_ids')
        if not partner.camiones_ids:
            camiones = child_camiones
        else:
            camiones = camiones + child_camiones

    return http.request.render('intn_camiones_tanque.nueva_solicitud',
                               {'fecha_actual': fecha_actual, 'partner': partner, 'page_name': 'solicitud',
                                'sucursales': sucursales, 'camiones': camiones, 'marcas': marcas,
                                'modelos': modelos, 'emblemas': emblemas, 'camionC': False, 'acopladoA': acoplado,
                                'fecha_actual_diez': fecha_actual_diez, 'acoplados': acoplados})


@http.route(['/get-camiones/<int:partner_id>'], type='http', auth="public", website=True)
def get_camiones(self, partner_id, **kw):
    if partner_id != 0:
        partner = request.env['res.partner'].browse(partner_id)
    else:
        partner = request.env['res.users'].browse(request.session.uid).partner_id

    camiones = request.env['camiones.cisterna'].sudo().search(
        ['|', ('partner_id', '=', partner.id), ('partner_id.parent_id', '=', partner_id)])
    camiones_a_enviar = []
    if camiones:
        for b in camiones:
            p = {'id': b.id, 'second_name': b.codigo_emblema_char + '-' + b.emblema_id.name}

            camiones_a_enviar.append(p)

    return json.dumps(camiones_a_enviar)


@http.route(['/get-fecha/<string:fecha>/<int:capacidad>/<string:tipo_solicitud>'], type='http', auth="public",
            website=True)
def get_fecha(self, fecha, capacidad, tipo_solicitud, **kw):
    if tipo_solicitud not in ['verificacion_anual', 'habilitacion']:
        return json.dumps({'code': 200})
    agendamientos = request.env['intn_camiones_tanque.solicitudes'].sudo().search(
        [('state', '!=', 'cancel'), ('fecha_agendamiento', '!=', False)])
    agendamientos_fecha = agendamientos.filtered(
        lambda x: x.fecha_agendamiento_compute.strftime('%Y-%m-%d') == fecha)
    capacidad_agendada = 0
    capacidad_maxima = int(
        request.env['ir.config_parameter'].sudo().get_param('capacidad_maxima_agendamiento_parameter'))
    for af in agendamientos_fecha:
        capacidad_agendada = capacidad_agendada + af.capacidad

    feriados = request.env['resource.calendar.leaves'].sudo().search([('name', '!=', False)])
    dia_feriado = feriados.filtered(
        lambda x: x.date_from.strftime('%Y-%m-%d') <= fecha <= x.date_to.strftime('%Y-%m-%d'))
    fecha = datetime.strptime(fecha, '%Y-%m-%d')
    if fecha.weekday() > 4 or dia_feriado:
        return json.dumps({'code': 400, 'mensaje': 'No puede agendarse en días festivos.'})
    if capacidad_agendada + capacidad > capacidad_maxima:
        return json.dumps({'code': 400, 'mensaje': 'Se ha alcanzado la capacidad límite para la fecha.'})
    else:
        return json.dumps({'code': 200})


@http.route(['/my/certificado-inspeccion', '/my/certificado-inspeccion/page/<int:page>'], type='http', auth="user",
            website=True)
def portal_my_certificado_inspeccion(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
    values = self._prepare_portal_layout_values()
    partner = request.env.user.partner_id
    certificado_inspeccion = request.env['certificado.inspeccion']

    domain = [
        ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        ('state', 'in', ['done', 'cancel'])
    ]

    searchbar_sortings = {
        'date': {'label': _('Fecha de Creación'), 'order': 'create_date desc'},
        'name': {'label': _('Referencia'), 'order': 'name'},
        'stage': {'label': _('Estado'), 'order': 'state'},
    }

    # default sortby order
    if not sortby:
        sortby = 'date'
    sort_order = searchbar_sortings[sortby]['order']

    archive_groups = self._get_archive_groups('certificado.inspeccion', domain)
    if date_begin and date_end:
        domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    # count for pager
    quotation_count = certificado_inspeccion.search_count(domain)
    # make pager
    pager = portal_pager(
        url="/my/certificado-inspeccion",
        url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        total=quotation_count,
        page=page,
        step=self._items_per_page
    )
    # search the count to display, according to the pager data
    certificado_inspeccion = certificado_inspeccion.search(domain, order=sort_order, limit=self._items_per_page,
                                                           offset=pager['offset'])
    request.session['my_certificado_inspeccion_history'] = certificado_inspeccion.ids[:100]

    values.update({
        'date': date_begin,
        'certificado_inspeccion': certificado_inspeccion.sudo(),
        'page_name': 'certificado_inspeccion',
        'pager': pager,
        'archive_groups': archive_groups,
        'default_url': '/my/certificado-inspeccion',
        'searchbar_sortings': searchbar_sortings,
        'sortby': sortby,
    })

    return request.render("intn_camiones_tanque.portal_my_certificado_inspeccion", values)


@http.route(['/my/certificado-inspeccion/<int:certificado_id>'], type='http', auth="public", website=True)
def portal_certificado_inspeccion_page(self, certificado_id, report_type=None, access_token=None, message=False,
                                       download=False,
                                       **kw):
    try:
        inspeccion_sudo = self._document_check_access('certificado.inspeccion', certificado_id,
                                                      access_token=access_token)
    except (AccessError, MissingError):
        return request.redirect('/my')

    if report_type in ('html', 'pdf', 'text'):
        return self._show_report(model=inspeccion_sudo, report_type=report_type,
                                 report_ref='intn_camiones_tanque.reporte_certificado_inspeccion',
                                 download=download)

    # use sudo to allow accessing/viewing orders for public user
    # only if he knows the private token
    now = fields.Date.today()

    # Log only once a day
    if inspeccion_sudo and request.session.get(
            'view_quote_%s' % inspeccion_sudo.id) != now and request.env.user.share and access_token:
        request.session['view_quote_%s' % inspeccion_sudo.id] = now
        body = _('Certificado visto por el cliente')
        _message_post_helper(res_model='certificado.inspeccion', res_id=inspeccion_sudo.id, message=body,
                             token=inspeccion_sudo.access_token, message_type='notification',
                             subtype="mail.mt_note",
                             partner_ids=inspeccion_sudo.partner_id.user_id.sudo().partner_id.ids)

    values = {
        'certificado_inspeccion': inspeccion_sudo,
        'message': message,
        'token': access_token,
        'bootstrap_formatting': True,
        'partner_id': inspeccion_sudo.partner_id.id,
        'report_type': 'html',
        'page_name': 'certificado_inspeccion',
    }
    if inspeccion_sudo.company_id:
        values['res_company'] = inspeccion_sudo.company_id

    if inspeccion_sudo.state in ('done', 'cancel'):
        history = request.session.get('my_certificado_inspeccion_history', [])
    else:
        history = request.session.get('my_certificado_inspeccion_history', [])
    values.update(get_records_pager(history, inspeccion_sudo))

    return request.render('intn_camiones_tanque.certificado_inspeccion_portal_template', values)


@http.route(['/my/certificado-verificacion', '/my/certificado-verificacion/page/<int:page>'], type='http',
            auth="user",
            website=True)
def portal_my_certificado_verificacion(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
    values = self._prepare_portal_layout_values()
    partner = request.env.user.partner_id
    certificado_verificacion = request.env['registro.medicion']

    domain = [
        ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        ('state', 'in', ['done', 'cancel'])
    ]

    searchbar_sortings = {
        'date': {'label': _('Fecha de Creación'), 'order': 'create_date desc'},
        'name': {'label': _('Referencia'), 'order': 'name'},
        'stage': {'label': _('Estado'), 'order': 'state'},
    }

    # default sortby order
    if not sortby:
        sortby = 'date'
    sort_order = searchbar_sortings[sortby]['order']

    archive_groups = self._get_archive_groups('registro.medicion', domain)
    if date_begin and date_end:
        domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    # count for pager
    quotation_count = certificado_verificacion.search_count(domain)
    # make pager
    pager = portal_pager(
        url="/my/certificado-verificacion",
        url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        total=quotation_count,
        page=page,
        step=self._items_per_page
    )
    # search the count to display, according to the pager data
    certificado_verificacion = certificado_verificacion.search(domain, order=sort_order, limit=self._items_per_page,
                                                               offset=pager['offset'])
    request.session['my_certificado_verificacion_history'] = certificado_verificacion.ids[:100]

    values.update({
        'date': date_begin,
        'certificado_verificacion': certificado_verificacion.sudo(),
        'page_name': 'certificado_verificacion',
        'pager': pager,
        'archive_groups': archive_groups,
        'default_url': '/my/certificado-verificacion',
        'searchbar_sortings': searchbar_sortings,
        'sortby': sortby,
    })

    return request.render("intn_camiones_tanque.portal_my_certificado_verificacion", values)


@http.route(['/my/certificado-verificacion/<int:certificado_id>'], type='http', auth="public", website=True)
def portal_certificado_verificacion_page(self, certificado_id, report_type=None, access_token=None, message=False,
                                         download=False,
                                         **kw):
    try:
        verificacion_sudo = self._document_check_access('registro.medicion', certificado_id,
                                                        access_token=access_token)
    except (AccessError, MissingError):
        return request.redirect('/my')

    if report_type in ('html', 'pdf', 'text'):
        return self._show_report(model=verificacion_sudo, report_type=report_type,
                                 report_ref='intn_camiones_tanque.reporte_certificado_verificacion',
                                 download=download)

    # use sudo to allow accessing/viewing orders for public user
    # only if he knows the private token
    now = fields.Date.today()

    # Log only once a day
    if verificacion_sudo and request.session.get(
            'view_quote_%s' % verificacion_sudo.id) != now and request.env.user.share and access_token:
        request.session['view_quote_%s' % verificacion_sudo.id] = now
        body = _('Certificado visto por el cliente')
        _message_post_helper(res_model='registro.medicion', res_id=verificacion_sudo.id, message=body,
                             token=verificacion_sudo.access_token, message_type='notification',
                             subtype="mail.mt_note",
                             partner_ids=verificacion_sudo.partner_id.user_id.sudo().partner_id.ids)

    values = {
        'certificado_verificacion': verificacion_sudo,
        'message': message,
        'token': access_token,
        'bootstrap_formatting': True,
        'partner_id': verificacion_sudo.partner_id.id,
        'report_type': 'html',
        'page_name': 'certificado_verificacion',
    }
    if verificacion_sudo.company_id:
        values['res_company'] = verificacion_sudo.company_id

    if verificacion_sudo.state in ('done', 'cancel'):
        history = request.session.get('my_certificado_verificacion_history', [])
    else:
        history = request.session.get('my_certificado_verificacion_history', [])
    values.update(get_records_pager(history, verificacion_sudo))

    return request.render('intn_camiones_tanque.certificado_verificacion_portal_template', values)
