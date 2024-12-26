from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from datetime import date
import json


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()

        session_uid = request.session.uid
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id

        licencia_conformidad = request.env['licencia.conformidad']
        licencia_conformidad_count = licencia_conformidad.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['done', 'cancel'])
        ])

        licencia_conformidad_dos = request.env['licencia.conformidad.dos']
        licencia_conformidad_dos_count = licencia_conformidad_dos.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['done', 'cancel'])
        ])

        licencia_servicios = request.env['licencia.servicios']
        licencia_servicios_count = licencia_servicios.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['done', 'cancel'])
        ])

        certificado_conformidad = request.env['certificado.conformidad']
        certificado_conformidad_count = certificado_conformidad.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['done', 'cancel'])
        ])

        # partner_habilitado = partner.commercial_partner_id.state_uso_marca == 'habilitado' or partner.commercial_partner_id.mapped('licencia_servicios_ids').filtered(lambda x: x.state == 'done' and x.fecha_vencimiento >= fields.Date.today())
        partner_habilitado = True

        solicitud_impresion = request.env['solicitud.impresiones']
        solicitud_impresion_count = solicitud_impresion.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['draft', 'verificado', 'asignado', 'cancel'])
        ])

        control_etiquetas = request.env['control.etiquetas']
        control_etiquetas_count = control_etiquetas.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])
        ])
        onm_metci = request.env['sale.order']
        onm_metci_count = onm_metci.search_count([
            ('service_type', '=', 'metci')
        ])
        onn_normas = request.env['sale.order']
        onn_normas_count = onn_normas.search_count([
            ('service_type', '=', 'onn_normas')
        ])

        values.update({
            'licencia_conformidad_count': licencia_conformidad_count,
            'licencia_conformidad_dos_count': licencia_conformidad_dos_count,
            'licencia_servicios_count': licencia_servicios_count,
            'certificado_conformidad_count': certificado_conformidad_count,
            'partner_habilitado': partner_habilitado,
            'solicitud_impresion_count': solicitud_impresion_count,
            'control_etiquetas_count': control_etiquetas_count,
            'onn_normas_count': onn_normas_count,
            'onm_metci_count': onm_metci_count,
        })

        return values

    @http.route(['/my/licencia-conformidad', '/my/licencia-conformidad/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_licencia_conformidad(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        licencia_conformidad = request.env['licencia.conformidad']

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

        archive_groups = self._get_archive_groups('licencia.conformidad', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = licencia_conformidad.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/licencia-conformidad",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        licencia_conformidad = licencia_conformidad.search(domain, order=sort_order, limit=self._items_per_page,
                                                           offset=pager['offset'])
        request.session['my_licencia_conformidad_history'] = licencia_conformidad.ids[:100]

        values.update({
            'date': date_begin,
            'licencia_conformidad': licencia_conformidad.sudo(),
            'page_name': 'licencia_conformidad',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/licencia-conformidad',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_licencia_conformidad", values)

    @http.route(['/my/licencia-conformidad/<int:licencia_id>'], type='http', auth="public", website=True)
    def portal_licencia_conformidad_page(self, licencia_id, report_type=None, access_token=None, message=False,
                                         download=False, **kw):
        try:
            licencia_conformidad_sudo = self._document_check_access('licencia.conformidad', licencia_id,
                                                                    access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=licencia_conformidad_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_licencia_conformidad',
                                     download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if licencia_conformidad_sudo and request.session.get(
                'view_quote_%s' % licencia_conformidad_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % licencia_conformidad_sudo.id] = now
            body = _('Licencia vista por el cliente')
            _message_post_helper(res_model='licencia.conformidad', res_id=licencia_conformidad_sudo.id, message=body,
                                 token=licencia_conformidad_sudo.access_token, message_type='notification',
                                 subtype="mail.mt_note",
                                 partner_ids=licencia_conformidad_sudo.solicitante_id.user_id.sudo().partner_id.ids)

        values = {
            'licencia_conformidad': licencia_conformidad_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': licencia_conformidad_sudo.solicitante_id.id,
            'report_type': 'html',
            'page_name': 'licencia_conformidad',
        }
        if licencia_conformidad_sudo.company_id:
            values['res_company'] = licencia_conformidad_sudo.company_id

        if licencia_conformidad_sudo.state in ('done', 'cancel'):
            history = request.session.get('my_licencia_conformidad_history', [])
        else:
            history = request.session.get('my_licencia_conformidad_history', [])
        values.update(get_records_pager(history, licencia_conformidad_sudo))

        return request.render('intn_trazabilidad_uso_marca.licencia_conformidad_portal_template', values)

    @http.route(['/my/licencia-conformidad-dos', '/my/licencia-conformidad-dos/page/<int:page>'], type='http',
                auth="user",
                website=True)
    def portal_my_licencia_conformidad_dos(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        licencia_conformidad_dos = request.env['licencia.conformidad.dos']

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

        archive_groups = self._get_archive_groups('licencia.conformidad.dos', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = licencia_conformidad_dos.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/licencia-conformidad-2",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        licencia_conformidad_dos = licencia_conformidad_dos.search(domain, order=sort_order, limit=self._items_per_page,
                                                                   offset=pager['offset'])
        request.session['my_licencia_conformidad_dos_history'] = licencia_conformidad_dos.ids[:100]

        values.update({
            'date': date_begin,
            'licencia_conformidad_dos': licencia_conformidad_dos.sudo(),
            'page_name': 'licencia_conformidad_dos',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/licencia-conformidad-2',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_licencia_conformidad_dos", values)

    @http.route(['/my/licencia-conformidad-dos/<int:certificado_id>'], type='http', auth="public", website=True)
    def portal_licencia_conformidad_dos_page(self, certificado_id, report_type=None, access_token=None, message=False,
                                             download=False,
                                             **kw):
        try:
            licencia_conformidad_dos_sudo = self._document_check_access('licencia.conformidad.dos', certificado_id,
                                                                        access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=licencia_conformidad_dos_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_licencia_conformidad_dos',
                                     download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if licencia_conformidad_dos_sudo and request.session.get(
                'view_quote_%s' % licencia_conformidad_dos_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % licencia_conformidad_dos_sudo.id] = now
            body = _('Licencia vista por el cliente')
            _message_post_helper(res_model='licencia.conformidad.dos', res_id=licencia_conformidad_dos_sudo.id,
                                 message=body,
                                 token=licencia_conformidad_dos_sudo.access_token, message_type='notification',
                                 subtype="mail.mt_note",
                                 partner_ids=licencia_conformidad_dos_sudo.solicitante_id.user_id.sudo().partner_id.ids)

        values = {
            'licencia_conformidad_dos': licencia_conformidad_dos_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': licencia_conformidad_dos_sudo.solicitante_id.id,
            'report_type': 'html',
            'page_name': 'licencia_conformidad_dos',
        }
        if licencia_conformidad_dos_sudo.company_id:
            values['res_company'] = licencia_conformidad_dos_sudo.company_id

        if licencia_conformidad_dos_sudo.state in ('done', 'cancel'):
            history = request.session.get('my_licencia_conformidad_dos_history', [])
        else:
            history = request.session.get('my_licencia_conformidad_dos_history', [])
        values.update(get_records_pager(history, licencia_conformidad_dos_sudo))

        return request.render('intn_trazabilidad_uso_marca.licencia_conformidad_dos_portal_template', values)

    @http.route(['/my/licencia-servicios', '/my/licencia-servicios/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_licencia_servicios(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        licencia_servicios = request.env['licencia.servicios']

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

        archive_groups = self._get_archive_groups('licencia.servicios', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = licencia_servicios.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/licencia-servicios",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        licencia_servicios = licencia_servicios.search(domain, order=sort_order, limit=self._items_per_page,
                                                       offset=pager['offset'])
        request.session['my_licencia_servicios_history'] = licencia_servicios.ids[:100]

        values.update({
            'date': date_begin,
            'licencia_servicios': licencia_servicios.sudo(),
            'page_name': 'licencia_servicios',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/licencia-servicios',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_licencia_servicios", values)

    @http.route(['/my/licencia-servicios/<int:certificado_id>'], type='http', auth="public", website=True)
    def portal_licencia_servicios_page(self, certificado_id, report_type=None, access_token=None, message=False,
                                       download=False,
                                       **kw):
        try:
            licencia_servicios_sudo = self._document_check_access('licencia.servicios', certificado_id,
                                                                  access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=licencia_servicios_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_licencia_servicios',
                                     download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if licencia_servicios_sudo and request.session.get(
                'view_quote_%s' % licencia_servicios_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % licencia_servicios_sudo.id] = now
            body = _('Certificado visto por el cliente')
            _message_post_helper(res_model='licencia.servicios', res_id=licencia_servicios_sudo.id, message=body,
                                 token=licencia_servicios_sudo.access_token, message_type='notification',
                                 subtype="mail.mt_note",
                                 partner_ids=licencia_servicios_sudo.solicitante_id.user_id.sudo().partner_id.ids)

        values = {
            'licencia_servicios': licencia_servicios_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': licencia_servicios_sudo.solicitante_id.id,
            'report_type': 'html',
            'page_name': 'licencia_servicios',
        }
        if licencia_servicios_sudo.company_id:
            values['res_company'] = licencia_servicios_sudo.company_id

        if licencia_servicios_sudo.state in ('done', 'cancel'):
            history = request.session.get('my_licencia_servicios_history', [])
        else:
            history = request.session.get('my_licencia_servicios_history', [])
        values.update(get_records_pager(history, licencia_servicios_sudo))

        return request.render('intn_trazabilidad_uso_marca.licencia_servicios_portal_template', values)

    @http.route(['/my/certificado-conformidad', '/my/certificado-conformidad/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_certificado_conformidad(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        certificado_conformidad = request.env['certificado.conformidad']

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

        archive_groups = self._get_archive_groups('certificado.conformidad', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = certificado_conformidad.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/certificado-conformidad",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        certificado_conformidad = certificado_conformidad.search(domain, order=sort_order, limit=self._items_per_page,
                                                                 offset=pager['offset'])
        request.session['my_certificado_conformidad_history'] = certificado_conformidad.ids[:100]

        values.update({
            'date': date_begin,
            'certificado_conformidad': certificado_conformidad.sudo(),
            'page_name': 'certificado_conformidad',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/certificado-conformidad',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_certificado_conformidad", values)

    @http.route(['/my/certificado-conformidad/<int:certificado_conformidad_id>'], type='http', auth="public",
                website=True)
    def portal_certificado_conformidad_page(self, certificado_conformidad_id, report_type=None, access_token=None,
                                            message=False, download=False,
                                            **kw):
        try:
            certificado_conformidad_sudo = self._document_check_access('certificado.conformidad',
                                                                       certificado_conformidad_id,
                                                                       access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=certificado_conformidad_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_certificado_conformidad', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if certificado_conformidad_sudo and request.session.get(
                'view_quote_%s' % certificado_conformidad_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % certificado_conformidad_sudo.id] = now
            body = _('certificado_conformidad vista por el cliente')
            _message_post_helper(res_model='certificado.conformidad', res_id=certificado_conformidad_sudo.id,
                                 message=body,
                                 token=certificado_conformidad_sudo.access_token, message_type='notification',
                                 subtype="mail.mt_note",
                                 partner_ids=certificado_conformidad_sudo.solicitante_id.user_id.sudo().partner_id.ids)

        values = {
            'certificado_conformidad': certificado_conformidad_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': certificado_conformidad_sudo.solicitante_id.id,
            'report_type': 'html',
            'page_name': 'certificado_conformidad',
        }
        if certificado_conformidad_sudo.company_id:
            values['res_company'] = certificado_conformidad_sudo.company_id

        if certificado_conformidad_sudo.state in ('done', 'cancel'):
            history = request.session.get('my_certificado_conformidad_history', [])
        else:
            history = request.session.get('my_certificado_conformidad_history', [])
        values.update(get_records_pager(history, certificado_conformidad_sudo))

        return request.render('intn_trazabilidad_uso_marca.certificado_conformidad_portal_template', values)
