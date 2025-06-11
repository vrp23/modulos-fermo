from odoo import models, fields, api, _
from datetime import date, timedelta

class ChequeraCheck(models.Model):
    _name = 'chequera.check'
    _description = 'Cheque comprado/vendido'
    _order = 'fecha_emision desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campo para código de cheque secuencial
    name = fields.Char(string='Código', default='Nuevo', readonly=True, copy=False)
    
    # Campos básicos
    numero_cheque = fields.Char(string='Número de cheque', required=True, tracking=True)
    banco_id = fields.Many2one('chequera.bank', string='Banco', required=True, tracking=True)
    
    # CAMBIO: Nuevo campo emisor_id reemplazando beneficiario
    emisor_id = fields.Many2one('chequera.emisor', string='Emisor de cheque', required=True, tracking=True)
    
    # CAMBIO: beneficiario ahora es computado para compatibilidad
    beneficiario = fields.Char(string='Nombre del beneficiario', compute='_compute_beneficiario', store=True)
    
    @api.depends('emisor_id')
    def _compute_beneficiario(self):
        for record in self:
            record.beneficiario = record.emisor_id.name if record.emisor_id else ''
    
    monto = fields.Float(string='Monto ($)', required=True, tracking=True)
    
    # Nuevos campos de fecha
    fecha_emision = fields.Date(string='Fecha de emisión', required=True, tracking=True)
    fecha_pago = fields.Date(string='Fecha de pago/cobro', required=True, tracking=True, 
                            help="En cheques diferidos, esta fecha puede ser posterior a la fecha de emisión.")
    fecha_vencimiento = fields.Date(string='Fecha de vencimiento', compute='_compute_fecha_vencimiento', 
                                   store=True, help="30 días después de la fecha de pago/cobro.")
    fecha_rechazo = fields.Date(string='Fecha de rechazo', readonly=True, tracking=True)

    # Relaciones con proveedores y clientes - Sin dominios complejos
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', tracking=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', tracking=True)

    # Imágenes del cheque
    archivo_frente_id = fields.Many2one('ir.attachment', string='Imagen Frente')
    archivo_dorso_id = fields.Many2one('ir.attachment', string='Imagen Dorso')
    
    # Campos para mostrar las imágenes
    image_frente = fields.Binary(string='Frente del Cheque', attachment=True)
    image_dorso = fields.Binary(string='Dorso del Cheque', attachment=True)

    # Checklist
    checklist_emisor = fields.Boolean(string='Viabilidad del emisor verificada', tracking=True)
    checklist_irregularidades = fields.Boolean(string='El cheque no posee irregularidades', tracking=True)
    checklist_firma = fields.Boolean(string='El Cheque está correctamente firmado', tracking=True)

    # Campos para rechazo
    motivo_rechazo = fields.Text(string='Motivo de rechazo', tracking=True)
    
    # NUEVO: Campos para devolución
    devuelto = fields.Boolean(string='¿Devuelto?', help='Marcar cuando el cheque rechazado haya sido devuelto al proveedor', tracking=True)
    fecha_devolucion = fields.Date(string='Fecha de devolución', tracking=True)

    # Tasas y valores (para compra y venta)
    # Campos para compra
    tasa_pesificacion_compra = fields.Float(string='Tasa de pesificación (%) - Compra', tracking=True)
    interes_mensual_compra = fields.Float(string='Interés mensual (%) - Compra', tracking=True)
    vendedor_id_compra = fields.Many2one('res.users', string='Operador - Compra', tracking=True)  # CAMBIO: Vendedor a Operador
    
    # Campos calculados para compra
    pesificacion_valor_compra = fields.Float(string='Valor de pesificación ($) - Compra', compute='_compute_valores_compra', store=True, tracking=True)
    interes_valor_compra = fields.Float(string='Valor de interés ($) - Compra', compute='_compute_valores_compra', store=True, tracking=True)
    precio_compra = fields.Float(string='Precio de compra ($)', compute='_compute_valores_compra', store=True, tracking=True)
    
    # Campos para venta
    tasa_pesificacion_venta = fields.Float(string='Tasa de pesificación (%) - Venta', tracking=True)
    interes_mensual_venta = fields.Float(string='Interés mensual (%) - Venta', tracking=True)
    vendedor_id_venta = fields.Many2one('res.users', string='Operador - Venta', tracking=True)  # CAMBIO: Vendedor a Operador
    
    # Campos calculados para venta
    pesificacion_valor_venta = fields.Float(string='Valor de pesificación ($) - Venta', compute='_compute_valores_venta', store=True, tracking=True)
    interes_valor_venta = fields.Float(string='Valor de interés ($) - Venta', compute='_compute_valores_venta', store=True, tracking=True)
    precio_venta = fields.Float(string='Precio de venta ($)', compute='_compute_valores_venta', store=True, tracking=True)

    # Estado del cheque
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('anulado', 'Anulado'),
        ('rechazado', 'Rechazado'),
    ], default='borrador', string='Estado', tracking=True)
    
    # Flag para saber si este cheque está siendo usado en un proceso de compra múltiple
    is_in_purchase_wizard = fields.Boolean(string='En proceso de compra múltiple', default=False, copy=False)
    
    # Campos computados
    dias_para_vencimiento = fields.Integer(string='Días para vencimiento', compute='_compute_dias_para_vencimiento', store=True)
    dias_para_disponibilidad = fields.Integer(string='Días para disponibilidad', compute='_compute_dias_para_disponibilidad', store=True)
    alerta_vencimiento = fields.Selection([
        ('normal', 'Normal'),
        ('alerta_30', 'Menos de 30 días'),
        ('alerta_15', 'Menos de 15 días'),
        ('alerta_7', 'Menos de 7 días'),
        ('vencido', 'Vencido'),
    ], string='Alerta de vencimiento', compute='_compute_dias_para_vencimiento', store=True)
    
    meses_hasta_vencimiento = fields.Float(string='Meses hasta vencimiento', compute='_compute_meses_hasta_vencimiento', store=True)

    # Campos para el dashboard
    latest_purchases = fields.Many2many('chequera.check', string='Últimas compras', compute='_compute_dashboard_data')
    available_checks = fields.Many2many('chequera.check', string='Cheques disponibles', compute='_compute_dashboard_data', relation='chequera_check_dashboard_rel')
    
    # Secuencia automática para el campo name
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = 'CHEQ#' + self.env['ir.sequence'].next_by_code('chequera.check.sequence') or '000000'
            
            # Asegurar que fecha_pago no sea anterior a fecha_emision
            if vals.get('fecha_emision') and vals.get('fecha_pago'):
                emision = fields.Date.from_string(vals.get('fecha_emision'))
                pago = fields.Date.from_string(vals.get('fecha_pago'))
                if pago < emision:
                    vals['fecha_pago'] = vals.get('fecha_emision')
            
        return super(ChequeraCheck, self).create(vals_list)
    
    @api.depends('fecha_pago')
    def _compute_fecha_vencimiento(self):
        for record in self:
            if record.fecha_pago:
                record.fecha_vencimiento = record.fecha_pago + timedelta(days=30)
            else:
                record.fecha_vencimiento = False
                
    @api.depends('fecha_pago')
    def _compute_dias_para_disponibilidad(self):
        today = date.today()
        for record in self:
            if record.fecha_pago:
                dias = (record.fecha_pago - today).days
                record.dias_para_disponibilidad = dias
            else:
                record.dias_para_disponibilidad = 0
                
    @api.onchange('fecha_emision')
    def _onchange_fecha_emision(self):
        """Al cambiar la fecha de emisión, actualizar la fecha de pago si es necesario"""
        if self.fecha_emision and (not self.fecha_pago or self.fecha_pago < self.fecha_emision):
            self.fecha_pago = self.fecha_emision
            
    # NUEVO: onchange para devolución
    @api.onchange('devuelto')
    def _onchange_devuelto(self):
        """Al marcar como devuelto, establecer fecha de devolución"""
        if self.devuelto and not self.fecha_devolucion:
            self.fecha_devolucion = fields.Date.today()
        elif not self.devuelto:
            self.fecha_devolucion = False
            
    def action_rechazar(self):
        """Abrir wizard para rechazar el cheque"""
        self.ensure_one()
        
        # CAMBIO: Prevención de doble rechazo
        if self.state == 'rechazado':
            raise models.ValidationError(_('Este cheque ya ha sido rechazado.'))
            
        return {
            'name': _('Rechazar Cheque'),
            'view_mode': 'form',
            'res_model': 'chequera.rejection.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'chequera.check',
            }
        }