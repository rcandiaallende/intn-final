from odoo import http
from odoo.http import request


class RegistryPortal(http.Controller):
    @http.route('/registry', type='http', auth="public", website=True)
    def registry(self, **kwargs):
        entries = request.env['registry.entry'].sudo().search([])
        countries = request.env['res.country'].sudo().search([])
        return request.render('my_module.registry_portal', {
            'registry_entries': entries,
            'countries': countries,
        })

    @http.route('/registry/search', type='http', auth="public", website=True, methods=['POST'])
    def registry_search(self, **post):
        search_term = post.get('search')
        country_id = post.get('country_id')
        domain = []
        if search_term:
            domain.append(('document_number', 'ilike', search_term))
        if country_id:
            domain.append(('country_id', '=', int(country_id)))

        entries = request.env['registry.entry'].sudo().search(domain)
        countries = request.env['res.country'].sudo().search([])

        return request.render('my_module.registry_portal', {
            'registry_entries': entries,
            'countries': countries,
        })
