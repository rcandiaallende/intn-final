# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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

    @http.route(['/my/solicitud-impresion', '/my/solicitud-impresion/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_solicitud_impresion(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SolicitudImpresiones = request.env['solicitud.impresiones']

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['draft','asignado', 'vertificado', 'cancel'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Fecha Solicitud'), 'order': 'fecha_solicitud desc'},
            'name': {'label': _('Referencia'), 'order': 'name'},
            'stage': {'label': _('Estado'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('solicitud.impresiones', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = SolicitudImpresiones.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/solicitud-impresiones",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SolicitudImpresiones.search(domain, order=sort_order, limit=self._items_per_page,
                                                offset=pager['offset'])
        request.session['my_solicitudes_impresion_history'] = quotations.ids[:100]

        values.update({
            'date': date_begin,
            'solicitud_impresion': quotations.sudo(),
            'page_name': 'solicitud_impresion',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/solicitud-impresion',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_solicitud_impresion", values)


    @http.route(['/my/solicitud-impresion/<int:solicitud_id>'], type='http', auth="public", website=True)
    def portal_solicitud_impresion_page(self, solicitud_id, report_type=None, access_token=None, message=False, download=False,
                              **kw):
        try:
            solicitud_sudo = self._document_check_access('solicitud.impresiones', solicitud_id,
                                                         access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=solicitud_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_solicitud_impresion', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if solicitud_sudo and request.session.get(
                'view_quote_%s' % solicitud_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % solicitud_sudo.id] = now
            body = _('Solicitud vista por el cliente')
            _message_post_helper(res_model='solicitud.impresiones', res_id=solicitud_sudo.id, message=body,
                                 token=solicitud_sudo.access_token, message_type='notification', subtype="mail.mt_note",
                                 partner_ids=solicitud_sudo.partner_id.user_id.sudo().partner_id.ids)

        values = {
            'solicitud_impresion': solicitud_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': solicitud_sudo.partner_id.id,
            'report_type': 'html',
            'page_name': 'solicitud_impresion',
        }
        if solicitud_sudo.company_id:
            values['res_company'] = solicitud_sudo.company_id

        if solicitud_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_solicitudes_impresion_history', [])
        else:
            history = request.session.get('my_solicitudes_impresion_history', [])
        values.update(get_records_pager(history, solicitud_sudo))

        return request.render('intn_trazabilidad_uso_marca.solicitud_impresion_portal_template', values)


    @http.route(['/new/solicitud-impresion'], type='http', auth="user", website=True)
    def portal_new_solicitud_impresion(self, **kw):
        session_uid = request.session.uid
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id
            sucursales = partner.child_ids

        licencia_vigente = partner.mapped('licencia_servicios_ids').filtered(
            lambda x: x.state == 'done' and x.fecha_vencimiento >= fields.Date.today()).sorted(key=lambda r: r.name)
        etiquetas_disponibles = licencia_vigente.mapped('agentes_1.etiqueta_ids')
        #etiquetas_disponibles = [(6, 0, etiquetas_disponibles.ids)]

        fecha_actual = date.today().strftime("%d/%m/%Y")

        return http.request.render('intn_trazabilidad_uso_marca.nueva_solicitud_impresion',
                                   {'etiquetas': etiquetas_disponibles,
                                    'fecha_actual': fecha_actual, 'partner': partner, 'sucursales':sucursales,
                                    'page_name': 'solicitud_impresion'})

    @http.route('/save/solicitud-impresion', auth='user', website=True, )
    def save_solicitud_impresion(self, **kw):
        partner = kw['partner']
        lines = json.loads(kw['lines'])
        x = 1

        values = {
            'partner_id': partner,
            'fecha_solicitud': date.today()
        }
        solicitud = request.env['solicitud.impresiones'].sudo().create(values)

        while x < len(lines):
            #print(lines[x])
            product = request.env['product.product'].search([('id','=',int(lines[x].get('product')))])
            linea = {
                'solicitud_id': solicitud.id,
                'product_id': lines[x].get('product'),
                'qty': int(lines[x].get('qty')),
                'kg_polvo': product.kg_polvo,
                'kg_polvo_total': product.kg_polvo * int(lines[x].get('qty'))
            }
            request.env['solicitud.impresiones.lines'].sudo().create(linea)
            #solicitud.sudo().write({'solicitud_impresiones_ids': [(0, 0, linea)]})

            x = x + 1


        return http.request.render('intn_trazabilidad_uso_marca.solicitud_impresion_creada',
                                   {'solicitud': solicitud,'page_name':'solicitud_impresion'})


class SolicitudImpresionesController(http.Controller):
    @http.route('/solicitud_impresiones/dynamic_form', type='json', auth='user')
    def dynamic_form(self):
        # Obtener los campos dinámicos
        fields = request.env['solicitud.impresiones.lines'].get_certificado_fields()

        # Generar los campos XML para la vista dinámica
        fields_xml = ''.join([
            f'<field name="{field["name"]}" string="{field["label"]}" required="{str(field["required"]).lower()}"/>'
            for field in fields
        ])

        # Crear la estructura XML del formulario
        form_xml = f"""
        <form>
            <sheet>
                <group>
                    <field name="product_id"/>
                    {fields_xml}
                </group>
            </sheet>
        </form>
        """

        return {
            'view_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'arch': form_xml,
        }