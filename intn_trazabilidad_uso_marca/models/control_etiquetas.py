from odoo import fields, api, models, exceptions
import uuid


class ControlEtiquetas(models.Model):
    _name = 'control.etiquetas'
    _description = "Control de Etiquetas Vendidas"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    fecha_hora = fields.Datetime(
        'Fecha/Hora', default=lambda self: fields.Datetime.now())
    name = fields.Char('Nombre', copy=False, default="Borrador", track_visibility='onchange')

    partner_id = fields.Many2one('res.partner', 'Cliente', required="True", track_visibility='onchange')

    archivo_excel = fields.Binary(string="Archivo Excel")
    excel_name = fields.Char(string="Archivo Excel")

    user_id = fields.Many2one(
        'res.users', string="Técnico Responsable", required=True, default=lambda self: self.env.user)

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company'])

    def _default_access_token(self):
        return uuid.uuid4().hex

    access_url = fields.Char('URL del portal de cliente', compute="_compute_access_url")
    access_token = fields.Char('Token de seguridad', default=_default_access_token)

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Control de Etiquetas', self.name)

    def _compute_access_url(self):
        # super(SolicitudesServicio, self)._compute_access_url()
        for verificacion in self:
            verificacion.access_url = '/my/control-etiquetas/%s' % (verificacion.id)

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    @api.multi
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        self.ensure_one()
        url = self.access_url + '%s?access_token=%s%s%s%s%s' % (
            suffix if suffix else '',
            self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            '#%s' % anchor if anchor else ''
        )
        return url

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            seq = self.env['ir.sequence'].sudo().next_by_code(
                'seq_control_etiquetas')
            vals['name'] = seq
        res = super(ControlEtiquetas, self).create(vals)
        for i in res:
            reg = {
                'res_id': i.id,
                'res_model': 'control.etiquetas',
                'partner_id': i.partner_id.id
            }
            follower_id = self.env['mail.followers'].create(reg)
        return res
