from odoo import http
from odoo.http import request


class GenerarPresupuestoPortal(http.Controller):

    @http.route('/my/nuevo-presupuesto', type='http', auth="user", website=True)
    def portal_nuevo_presupuesto(self, **kwargs):
        servicios = request.env['product.product'].sudo().search([])
        payment_terms = request.env['account.payment.term'].sudo().search([])
        servicios_list = [{'id': servicio.id, 'name': servicio.name, 'price': servicio.lst_price} for servicio in
                          servicios]
        return request.render('test.portal_my_generar_presupuesto',
                              {'servicios': servicios_list, 'payment_terms': payment_terms})

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
            'state': 'draft',
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
        return request.redirect('/my/orders')
