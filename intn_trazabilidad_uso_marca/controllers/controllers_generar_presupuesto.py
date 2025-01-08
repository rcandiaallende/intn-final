from odoo import http
from odoo.http import request
from odoo import fields, http, _
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError


class GenerarPresupuestoPortal(http.Controller):

    @http.route('/my/normas', type='http', auth="user", website=True)
    def portal_listar_normas(self, sortby=None, **kwargs):
        # sorts
        searchbar_sortings = {
            'date': {'label': _('Fecha/Hora'), 'order': 'date_order desc'},
            'name': {'label': _('Referencia'), 'order': 'name'},
            'state': {'label': _('Estado'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        # Obtener normas del modelo relacionado y aplicar el orden
        normas = request.env['sale.order'].sudo().search(
            [('service_type', 'in', ['onn_normas', 'reprint_onn_normas'])],
            order=sort_order
        )

        # Obtener la descripción legible del campo selection
        state_selection = dict(request.env['sale.order'].fields_get(['state'])['state']['selection'])
        service_type_selection = dict(
            request.env['sale.order'].fields_get(['service_type'])['service_type']['selection']
        )
        normas_list = [
            {
                'id': norma.id,
                'name': norma.name,
                'document_printing_count': norma.document_printing_count,
                'service_type': service_type_selection.get(norma.service_type, norma.service_type),
                'paid': norma.is_paid(),
                'state': state_selection.get(norma.state, norma.state),  # Obtener string legible
            }
            for norma in normas
        ]
        return request.render(
            'intn_trazabilidad_uso_marca.portal_my_listar_normas',
            {'normas': normas_list, 'searchbar_sortings': searchbar_sortings, 'sortby': sortby}
        )

    @http.route('/my/nuevo-presupuesto', type='http', auth="user", website=True)
    def portal_nuevo_presupuesto(self, **kwargs):
        laboratorios = request.env['intn.laboratorios'].sudo().search([])
        laboratorios_list = [{'id': lab.id, 'name': lab.name} for lab in laboratorios]

        servicios = request.env['product.product'].sudo().search([])
        payment_terms = request.env['account.payment.term'].sudo().search([]).filtered(lambda term: sum(
            term.line_ids.mapped('days')) == 0 or sum(term.line_ids.mapped('days')) == 30)
        servicios_list = [{'id': servicio.id, 'name': servicio.name, 'price': servicio.lst_price} for servicio in
                          servicios]
        return request.render('intn_trazabilidad_uso_marca.portal_my_generar_presupuesto',
                              {'servicios': servicios_list, 'payment_terms': payment_terms,
                               'laboratorios': laboratorios_list})

    @http.route('/get_servicios', type='json', auth="user")
    def get_servicios(self):
        data = request.jsonrequest
        laboratorio_id = data.get('laboratorio_id')

        if not laboratorio_id:
            return {'error': 'El laboratorio_id es obligatorio.'}
        servicios = request.env['product.template'].sudo().search([('laboratorio_id', '=', int(laboratorio_id))])
        servicios = request.env['product.product'].sudo().search([('product_tmpl_id', 'in', servicios.ids)])
        servicios_list = [{
            'id': servicio.id,
            'name': servicio.name,
            'price': servicio.list_price,
            'determinacion': servicio.product_tmpl_id.determinacion if servicio.product_tmpl_id.determinacion else 'N/A',
            'additional_cost': 'Si' if servicio.product_tmpl_id.verificacion_insitu else 'No'
        } for servicio in servicios]
        return servicios_list

    @http.route('/submit/nuevo_presupuesto_1', type='http', auth="user", website=True, methods=['POST'])
    def submit_nuevo_presupuesto(self, **post):
        # Obtener los datos del formulario
        sucursal = post.get('sucursal')
        payment_term_id = post.get('payment_term_id')

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
            'service_type': 'onn_normas',
            'payment_term_id': int(payment_term_id) if payment_term_id else False,
        })

        # Crear las líneas del presupuesto
        for servicio_id, cantidad, line_total in zip(servicios, cantidades, line_totals):
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': servicio_id,
                'product_uom_qty': cantidad,
                'price_unit': line_total / cantidad if cantidad != 0 else 0,
                'price_subtotal': line_total,
            })

        # Redirigir al listado de presupuestos
        return request.redirect('/my/normas')

    @http.route('/my/imprimir-norma/<int:norma_id>', type='http', auth="user", website=True)
    def imprimir_norma(self, norma_id, **kw):
        norma = request.env['sale.order'].browse(norma_id)

        # Forzar el acceso con permisos de administrador
        norma = norma.sudo()

        if not norma.exists():
            return "Norma no encontrada"

        if norma.document_printing_count > 0:
            raise UserError(_("Sólo puede imprimir una vez el Documente, solicite una reimpresión!',"))

        norma.document_printing_count += 1

        # Usamos la referencia del reporte 'report_norma_onn'
        report = request.env.ref('intn_trazabilidad_uso_marca.action_report_norma_onn')

        # Generamos el PDF utilizando el método de reporte adecuado
        pdf_content, content_type = report.sudo().render_qweb_pdf([norma.id])

        # Verificamos si se está generando el PDF correctamente
        if not pdf_content:
            return "Error al generar el PDF"

        # Retornamos la respuesta con el PDF
        return request.make_response(pdf_content, headers=[('Content-Type', content_type), (
            'Content-Disposition', 'attachment; filename="norma_onn.pdf"')])

    @http.route('/my/previsualizar-norma/<int:norma_id>', type='http', auth="user", website=True)
    def previsualizar_norma(self, norma_id, **kw):
        # Buscar el registro de la norma
        norma = request.env['sale.order'].browse(norma_id)
        norma = norma.sudo()

        # Verificar si la norma existe
        if not norma.exists():
            return "Norma no encontrada"

        # Verificar si la norma ha sido pagada
        if not norma.is_paid:
            raise UserError(_("Debe realizar el pago para la previsualización!"))

        # Obtener el reporte 'report_norma_onn'
        report = request.env.ref('intn_trazabilidad_uso_marca.action_report_preview_norma_onn')
        html_content = report.sudo().render_qweb_html([norma.id])
        return request.make_response(html_content[0], headers=[('Content-Type', 'text/html')])

    @http.route('/my/solicitar-reimpresion/<int:norma_id>', type='http', auth="user", website=True)
    def reimpresion_norma(self, norma_id, **kw):
        # Buscar el registro de la norma
        norma = request.env['sale.order'].browse(norma_id)
        norma = norma.sudo()

        # Verificar si la norma existe
        if not norma.exists():
            return "Norma no encontrada"

        # Verificar si la norma ha sido pagada
        if not norma.is_paid:
            raise UserError(_("Debe realizar el pago para la previsualización!"))

        partner = request.env.user.partner_id
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'state': 'pending',
            'service_type': 'reprint_onn_normas',
            # 'payment_term_id': int(payment_term_id) if payment_term_id else False,
        })
        norma.re_printing_so_ids = [(4, sale_order.id)]

        servicio_id = request.env['product.product'].sudo().search([('default_code', '=', 'REPRINT01')], limit=1)
        request.env['sale.order.line'].sudo().create({
            'order_id': sale_order.id,
            'product_id': servicio_id.id,
            'product_uom_qty': 1,
            'price_unit': servicio_id.list_price,
            'price_subtotal': servicio_id.list_price,
        })

        # Redirigir al listado de normas
        return request.redirect('/my/normas')
