from odoo import models, fields, api, _
import json
import re
from odoo.exceptions import UserError


class AppBasculas(models.Model):
    _name = 'app.basculas'
    _description = 'Datos de la app Basculas'

    id_serial = fields.Integer(string='ID Serial')
    creation_date = fields.Datetime(string='Fecha de creación')
    ruc_cliente = fields.Char(string='RUC')
    tecnico1 = fields.Char(string='Técnico 1')
    procesado = fields.Boolean(string='Procesado')
    data_receive = fields.Text(string='Data Recibido')
    tecnico2 = fields.Char(string='Técnico 1')
    imposibility = fields.Boolean(string='Imposibilidad')
    sale_order = fields.Many2one('sale.order', string='Presupuesto')
    account_invoice = fields.Many2one('account.invoice', string='Factura')
    formatted_html = fields.Html(string='Formatted HTML', compute='_compute_formatted_html')
    id_planificacion = fields.Char(string='Id planificacion', readonly=True)

    def button_test1(self):
        # raise UserError(_('Configure servicios asociados a la bascula'))
        raise UserError(_('No se encuentra su Factura/Pago asociado '))

    @api.model
    def create_sales_order(self, partner_id=220058, product_id=6722, quantity=1):
        # Verifica que se haya pasado un partner_id
        if not partner_id:
            raise ValueError("Debe proporcionar un partner_id")

        # Obtén el partner
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            raise ValueError("El partner con el ID proporcionado no existe")

        # Obtén el producto
        product = self.env['product.product'].browse(product_id)
        if not product.exists():
            raise ValueError("El producto con el ID proporcionado no existe")

        # Crear el sales.order
        order_vals = {
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': quantity,
                'price_unit': product.lst_price,
            })],
        }
        order = self.env['sale.order'].create(order_vals)
        return order

    @api.depends('data_receive')
    def _compute_formatted_html(self):
        for record in self:
            if record.data_receive:
                try:
                    parsed_json = json.loads(record.data_receive)
                    formatted_json = json.dumps(parsed_json, indent=4)
                    formatted_json = formatted_json.replace('"', '')
                    formatted_json = re.sub(r'\bstring\b', 'no data', formatted_json)
                    record.formatted_html = '<pre><code>{}</code></pre>'.format(formatted_json)
                except json.JSONDecodeError:
                    record.formatted_html = '<p>Invalid JSON</p>'
            else:
                record.formatted_html = '<p>No JSON data</p>'
