# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from datetime import date
import json
import base64


class CustomerPortal(CustomerPortal):

    @http.route(['/my/control-etiquetas', '/my/cont0rol-etiquetas/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_control_etiquetas(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ControlEtiquetas = request.env['control.etiquetas']

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])
        ]

        searchbar_sortings = {
            'date': {'label': _('Fecha/Hora'), 'order': 'fecha_hora desc'},
            'name': {'label': _('Referencia'), 'order': 'name'},
            # 'stage': {'label': _('Estado'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('control.etiquetas', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = ControlEtiquetas.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/control-etiquetas",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = ControlEtiquetas.search(domain, order=sort_order, limit=self._items_per_page,
                                             offset=pager['offset'])
        request.session['my_control_etiquetas_history'] = quotations.ids[:100]

        values.update({
            'date': date_begin,
            'control_etiquetas': quotations.sudo(),
            'page_name': 'control_etiquetas',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/control-etiquetas',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("intn_trazabilidad_uso_marca.portal_my_control_etiquetas", values)

    @http.route(['/my/control-metci', '/my/control-metci/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_control_metci(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('state', 'in', ['sale', 'done', 'pending']),
            ('service_type', '=', 'metci'),
        ]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/control-metci",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/control-metci',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("intn_trazabilidad_uso_marca.portal_my_control_metci", values)

    @http.route(['/my/control-etiquetas/<int:control_id>'], type='http', auth="public", website=True)
    def portal_control_etiquetas_page(self, control_id, report_type=None, access_token=None, message=False,
                                      download=False,
                                      **kw):
        try:
            control_sudo = self._document_check_access('control.etiquetas', control_id,
                                                       access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=control_sudo, report_type=report_type,
                                     report_ref='intn_trazabilidad_uso_marca.reporte_control_etiquetas',
                                     download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if control_sudo and request.session.get(
                'view_quote_%s' % control_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % control_sudo.id] = now
            body = _('Control de Etiqueta Vista por el cliente')
            _message_post_helper(res_model='control.etiquetas', res_id=control_sudo.id, message=body,
                                 token=control_sudo.access_token, message_type='notification', subtype="mail.mt_note",
                                 partner_ids=control_sudo.partner_id.user_id.sudo().partner_id.ids)

        values = {
            'control_etiquetas': control_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': control_sudo.partner_id.id,
            'report_type': 'html',
            'page_name': 'control_etiquetas',
        }
        if control_sudo.company_id:
            values['res_company'] = control_sudo.company_id

        if control_sudo:
            history = request.session.get('my_control_etiquetas_history', [])
        else:
            history = request.session.get('my_control_etiquetas_history', [])
        values.update(get_records_pager(history, control_sudo))

        return request.render('intn_trazabilidad_uso_marca.control_etiquetas_portal_template', values)

    @http.route(['/new/control-etiquetas'], type='http', auth="user", website=True)
    def portal_new_control_etiquetas(self, **kw):
        session_uid = request.session.uid
        if session_uid:
            partner = request.env['res.users'].browse(request.session.uid).partner_id
            if partner.parent_id:
                partner = partner.parent_id

        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        # csrf_token = self.csrf_token()

        return http.request.render('intn_trazabilidad_uso_marca.nueva_control_etiquetas',
                                   {'fecha_actual': fecha_actual, 'partner': partner, 'page_name': 'control_etiquetas'})

    @http.route(['/new/control-metci'], type='http', auth="user", website=True)
    def portal_new_control_metci(self, **kw):
        session_uid = request.session.uid
        if session_uid:
            partner = request.env['res.users'].browse(session_uid).partner_id
            if partner.parent_id:
                partner = partner.parent_id

        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        laboratorios = request.env['intn.laboratorios'].sudo().search([])
        laboratorios_list = [{'id': lab.id, 'name': lab.name} for lab in laboratorios]

        productos_list = []
        servicios_list = []
        laboratorio_id = kw.get('laboratorio_id', False)

        if laboratorio_id:
            productos = request.env['product.template'].sudo().search([('laboratorio_id', '=', int(laboratorio_id))])
            servicios = request.env['product.product'].sudo().search([])

            servicios_list = [{'id': servicio.id, 'name': servicio.name, 'price': servicio.lst_price,
                               'additional_cost': 'Si' if servicio.product_tmpl_id.additional_cost else 'No'} for
                              servicio
                              in servicios]

        return request.render('intn_trazabilidad_uso_marca.formulario_crear_presupuesto', {
            'fecha_actual': fecha_actual,
            'laboratorios': laboratorios_list,
            'servicios': servicios_list,
        })

    @http.route('/new/save/control-etiquetas', auth='user', website=True, csrf=False)
    def save_control_etiquetas(self, **kw):
        partner = kw['partner']
        excel = kw['archivo']
        excel = excel.read()
        excel = base64.b64encode(excel)

        values = {
            'partner_id': partner,
            'fecha_hora': datetime.datetime.now(),
            'archivo_excel': excel,
            'excel_name': 'Control de Etiqueta'
        }
        control_etiquetas = request.env['control.etiquetas'].sudo().create(values)

        return http.request.render('intn_trazabilidad_uso_marca.control_etiquetas_creada',
                                   {'control_etiquetas': control_etiquetas, 'page_name': 'control_etiquetas'})

    @http.route('/nuevo_presupuesto', type='http', auth="user", website=True)
    def nuevo_presupuesto(self, **kw):

        laboratorios = request.env['intn.laboratorios'].sudo().search([])
        productos = request.env['product.template'].sudo().search([('laboratorio_id', '=', 207)])
        servicios = request.env['product.product'].sudo().search([('product_tmpl_id', 'in', productos.ids)])

        return request.render('intn_trazabilidad_uso_marca.formulario_crear_presupuesto', {
            'servicios': servicios,
            'laboratorios': laboratorios
        })

    @http.route('/submit/nuevo_presupuesto', type='http', auth="user", website=True, methods=['POST'])
    def submit_nuevo_presupuesto(self, **post):
        # Obtener los datos del formulario
        sucursal = post.get('sucursal')

        # Inicializar listas para los ítems
        servicios = []
        cantidades = []
        line_totals = []

        # Recorrer los datos del formulario y agregar a las listas
        index = 0
        while f"servicio_{index}" in post:
            servicios.append(int(post.get(f"servicio_{index}")))
            cantidades.append(float(post.get(f"cantidad_{index}")))
            line_totals.append(float(post.get(f"line_total_{index}")))
            index += 1

        # Verificar que todas las listas tengan el mismo tamaño
        if not (len(servicios) == len(cantidades) == len(line_totals)):
            return request.render('error_template', {
                'error_message': 'Los datos de los ítems no coinciden en tamaño.',
            })

        # Obtener el cliente (usuario del portal)
        partner = request.env.user.partner_id

        # Crear un nuevo presupuesto en el modelo sale.order
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'state': 'pending',
            'service_type': 'metci',
        })
        calibration_request = request.env['calibration.request'].sudo().create(
            {'state': 'revision', 'partner_id': partner.id})
        sale_order.calibration_request = calibration_request.id

        # Crear las líneas del presupuesto
        for servicio_id, cantidad, line_total in zip(servicios, cantidades, line_totals):
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': servicio_id,
                'product_uom_qty': cantidad,
                'price_unit': line_total / cantidad if cantidad != 0 else 0,
                'price_subtotal': line_total,
            })

        # Redirigir al listado de presupuestos o a la página de éxito
        return request.redirect('/my/control-metci')
