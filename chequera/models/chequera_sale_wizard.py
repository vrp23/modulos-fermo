from odoo import models, fields, api, _
import logging

class ChequeraSaleWizard(models.Model):
    _name = 'chequera.sale.wizard'
    _description = 'Wizard para venta múltiple de cheques'
    
    name = fields.Char(string='Referencia', default='Nueva Venta', readonly=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    fecha_operacion = fields.Date(string='Fecha de operación', default=fields.Date.today, required=True)
    
    # Valores para actualización masiva - NO RELATED para evitar modificar el contacto
    tasa_pesificacion_masiva = fields.Float(string='Tasa de pesificación (%) para todos', default=0.0)
    interes_mensual_masivo = fields.Float(string='Interés mensual (%) para todos', default=0.0)
    vendedor_id_masivo = fields.Many2one('res.users', string='Operador para todos')  # CAMBIO: de "Vendedor" a "Operador"
    
    # Relación con los cheques - relación many2many
    check_ids = fields.Many2many('chequera.check', string='Cheques a vender', domain=[('state', '=', 'disponible')])
    
    # Campos computados para totales
    cantidad_cheques = fields.Integer(string='Cantidad de cheques', compute='_compute_totales')
    monto_total = fields.Float(string='Monto total', compute='_compute_totales')
    precio_total = fields.Float(string='Precio total de venta', compute='_compute_totales')
    
    # Añadimos un estado para el wizard
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado')
    ], default='borrador', string='Estado', tracking=True)
    
    # Agregar secuencia automática para el nombre
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nueva Venta') == 'Nueva Venta':
                vals['name'] = self.env['ir.sequence'].next_by_code('chequera.sale.sequence') or 'OPV#000'
        return super(ChequeraSaleWizard, self).create(vals_list)
    
    @api.depends('check_ids', 'check_ids.monto', 'check_ids.precio_venta')
    def _compute_totales(self):
        for wizard in self:
            wizard.cantidad_cheques = len(wizard.check_ids)
            wizard.monto_total = sum(wizard.check_ids.mapped('monto'))
            wizard.precio_total = sum(wizard.check_ids.mapped('precio_venta'))
    
    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        """Al cambiar el cliente, actualizar los valores de las tasas masivas"""
        if self.cliente_id:
            # CAMBIO: Usar tasas específicas de venta
            self.tasa_pesificacion_masiva = self.cliente_id.tasa_pesificacion_venta
            self.interes_mensual_masivo = self.cliente_id.interes_mensual_venta
            self.vendedor_id_masivo = self.cliente_id.assigned_seller_id
            
            # Actualizar el cliente de los cheques ya seleccionados
            for cheque in self.check_ids:
                cheque.cliente_id = self.cliente_id
    
    def action_update_tasas_masivas(self):
        """Actualiza las tasas de todos los cheques seleccionados SIN cerrar el wizard"""
        self.ensure_one()
        if not self.check_ids:
            return
        
        # Actualizamos solo los valores para los cheques en la operación actual,
        # NO modificamos el contacto/cliente, solo los cheques
        values = {
            'tasa_pesificacion_venta': self.tasa_pesificacion_masiva,
            'interes_mensual_venta': self.interes_mensual_masivo,
        }
        
        if self.vendedor_id_masivo:
            values['vendedor_id_venta'] = self.vendedor_id_masivo.id
        
        # Actualizar todos los cheques seleccionados
        self.check_ids.write(values)
        
        # Forzar el recálculo del precio de venta de cada cheque
        self.check_ids._compute_valores_venta()
        
        # Recalcular los totales
        self._compute_totales()
        
        # NO retornamos nada para mantener el wizard abierto
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'chequera.sale.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
            'flags': {'mode': 'edit'},
        }
    
    def action_confirmar_venta(self):
        """Confirmar la venta de todos los cheques seleccionados"""
        # Obtener cheques directamente del campo
        cheques = self.check_ids
        
        if not cheques:
            raise models.ValidationError(_('Debe seleccionar al menos un cheque para realizar la venta.'))
        
        if not self.cliente_id:
            raise models.ValidationError(_('Debe seleccionar un cliente para la venta.'))
        
        # Guardar los valores importantes antes de cualquier operación
        cheque_ids = cheques.ids
        cantidad_cheques = len(cheque_ids)
        monto_total = sum(cheques.mapped('monto'))
        precio_total = sum(cheques.mapped('precio_venta'))
        
        # Cambiar estado de todos los cheques a vendido
        self.env['chequera.check'].browse(cheque_ids).write({
            'state': 'vendido',
            'cliente_id': self.cliente_id.id,
        })
        
        # Crear un solo movimiento en la wallet por el total
        movement = self.env['chequera.wallet.movement'].create({
            'partner_id': self.cliente_id.id,
            'tipo': 'venta',
            'monto': precio_total,
            'fecha': self.fecha_operacion,
            'multiple_checks': True,
            'check_ids': [(6, 0, cheque_ids)],
            'notes': f'Venta múltiple: {cantidad_cheques} cheques por un total de {monto_total}'
        })
        
        # Confirmar el movimiento
        movement.action_confirm()
        
        # Cambiar el estado del wizard a confirmado
        self.write({'state': 'confirmado'})
        
        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Venta Exitosa'),
                'message': _('Se han vendido %s cheques por un total de $ %s') % (cantidad_cheques, precio_total),
                'sticky': False,
            }
        }
    
    def action_cancelar(self):
        """Cancelar la operación de venta"""
        self.write({'state': 'cancelado'})
        return True