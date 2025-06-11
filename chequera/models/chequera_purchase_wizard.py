from odoo import models, fields, api, _
import logging

class ChequeraPurchaseWizard(models.Model):  # Cambiado de TransientModel a Model
    _name = 'chequera.purchase.wizard'
    _description = 'Wizard para compra múltiple de cheques'
    
    name = fields.Char(string='Referencia', default='Nueva Compra', readonly=True)
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    fecha_operacion = fields.Date(string='Fecha de operación', default=fields.Date.today, required=True)
    
    # Valores para actualización masiva - NO RELATED para evitar modificar el contacto
    tasa_pesificacion_masiva = fields.Float(string='Tasa de pesificación (%) para todos', default=0.0)
    interes_mensual_masivo = fields.Float(string='Interés mensual (%) para todos', default=0.0)
    vendedor_id_masivo = fields.Many2one('res.users', string='Operador para todos')  # CAMBIO: de "Vendedor" a "Operador"
    
    # Relación con los cheques - relación many2many
    check_ids = fields.Many2many('chequera.check', string='Cheques a comprar', domain=[('state', '=', 'borrador')])
    
    # Campos computados para totales
    cantidad_cheques = fields.Integer(string='Cantidad de cheques', compute='_compute_totales')
    monto_total = fields.Float(string='Monto total', compute='_compute_totales')
    precio_total = fields.Float(string='Precio total de compra', compute='_compute_totales')
    
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
            if vals.get('name', 'Nueva Compra') == 'Nueva Compra':
                vals['name'] = self.env['ir.sequence'].next_by_code('chequera.purchase.sequence') or 'OPC#000'
        return super(ChequeraPurchaseWizard, self).create(vals_list)
    
    @api.depends('check_ids', 'check_ids.monto', 'check_ids.precio_compra')
    def _compute_totales(self):
        for wizard in self:
            wizard.cantidad_cheques = len(wizard.check_ids)
            wizard.monto_total = sum(wizard.check_ids.mapped('monto'))
            wizard.precio_total = sum(wizard.check_ids.mapped('precio_compra'))
    
    @api.onchange('proveedor_id')
    def _onchange_proveedor_id(self):
        """Al cambiar el proveedor, actualizar los valores de las tasas masivas"""
        if self.proveedor_id:
            # CAMBIO: Usar tasas específicas de compra
            self.tasa_pesificacion_masiva = self.proveedor_id.tasa_pesificacion_compra
            self.interes_mensual_masivo = self.proveedor_id.interes_mensual_compra
            self.vendedor_id_masivo = self.proveedor_id.assigned_seller_id
            
            # Actualizar el proveedor de los cheques ya seleccionados
            for cheque in self.check_ids:
                cheque.proveedor_id = self.proveedor_id
    
    def action_add_cheque(self):
        """Acción para agregar un nuevo cheque para la compra"""
        self.ensure_one()
        _logger = logging.getLogger(__name__)
        
        # Guardamos el wizard si no está ya guardado (para asegurar que tenga ID)
        if self.state == 'borrador' and not self.id:
            self = self.create({
                'proveedor_id': self.proveedor_id.id,
                'fecha_operacion': self.fecha_operacion,
                'tasa_pesificacion_masiva': self.tasa_pesificacion_masiva,
                'interes_mensual_masivo': self.interes_mensual_masivo,
                'vendedor_id_masivo': self.vendedor_id_masivo.id if self.vendedor_id_masivo else False,
            })
        
        _logger.info("Iniciando acción agregar cheque desde wizard ID: %s", self.id)
        
        return {
            'name': _('Nuevo Cheque'),
            'view_mode': 'form',
            'res_model': 'chequera.check',
            'view_id': self.env.ref('chequera.view_chequera_check_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_is_in_purchase_wizard': True,
                'default_proveedor_id': self.proveedor_id.id,
                'default_tasa_pesificacion_compra': self.tasa_pesificacion_masiva,
                'default_interes_mensual_compra': self.interes_mensual_masivo,
                'default_vendedor_id_compra': self.vendedor_id_masivo.id if self.vendedor_id_masivo else False,
                'default_state': 'borrador',
                'form_view_initial_mode': 'edit',
                'wizard_id': self.id,
            },
            'target': 'new',
            'flags': {'mode': 'edit'},
        }
    
    def action_edit_cheque(self):
        """Acción para editar un cheque existente"""
        self.ensure_one()
        cheque_id = self._context.get('cheque_id')
        if not cheque_id:
            return {'type': 'ir.actions.act_window_close'}
            
        return {
            'name': _('Editar Cheque'),
            'view_mode': 'form',
            'res_model': 'chequera.check',
            'res_id': cheque_id,
            'view_id': self.env.ref('chequera.view_chequera_check_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_is_in_purchase_wizard': True,
                'wizard_id': self.id,
            },
            'target': 'new',
        }
    
    def action_update_tasas_masivas(self):
        """Actualiza las tasas de todos los cheques seleccionados SIN cerrar el wizard"""
        self.ensure_one()
        if not self.check_ids:
            return
        
        # Actualizamos solo los valores para los cheques en la operación actual,
        # NO modificamos el contacto/proveedor, solo los cheques
        values = {
            'tasa_pesificacion_compra': self.tasa_pesificacion_masiva,
            'interes_mensual_compra': self.interes_mensual_masivo,
        }
        
        if self.vendedor_id_masivo:
            values['vendedor_id_compra'] = self.vendedor_id_masivo.id
        
        # Actualizar todos los cheques seleccionados
        self.check_ids.write(values)
        
        # Forzar el recálculo del precio de compra de cada cheque
        self.check_ids._compute_valores_compra()
        
        # Recalcular los totales
        self._compute_totales()
        
        # NO retornamos nada para mantener el wizard abierto
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'chequera.purchase.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
            'flags': {'mode': 'edit'},
        }
    
    @api.model
    def default_get(self, fields_list):
        """Obtener valores predeterminados, incluyendo cheque activo si existe"""
        res = super(ChequeraPurchaseWizard, self).default_get(fields_list)
        
        # Si viene de un cheque específico, lo agregamos a la lista
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        
        if active_model == 'chequera.check' and active_id:
            cheque = self.env['chequera.check'].browse(active_id)
            if cheque.state == 'borrador':
                res['check_ids'] = [(4, active_id)]
                
                # Si hay proveedor, establecemos también los valores de tasas
                if cheque.proveedor_id:
                    res['proveedor_id'] = cheque.proveedor_id.id
                    # CAMBIO: Usar tasas específicas de compra
                    res['tasa_pesificacion_masiva'] = cheque.proveedor_id.tasa_pesificacion_compra
                    res['interes_mensual_masivo'] = cheque.proveedor_id.interes_mensual_compra
                    if cheque.proveedor_id.assigned_seller_id:
                        res['vendedor_id_masivo'] = cheque.proveedor_id.assigned_seller_id.id
        
        return res
    
    def action_confirmar_compra(self):
        """Confirmar la compra de todos los cheques seleccionados"""
        # Obtener cheques directamente del campo
        cheques = self.check_ids
        
        if not cheques:
            raise models.ValidationError(_('Debe agregar al menos un cheque para realizar la compra.'))
        
        if not self.proveedor_id:
            raise models.ValidationError(_('Debe seleccionar un proveedor para la compra.'))
        
        # Verificar el checklist de todos los cheques
        cheques_sin_checklist = cheques.filtered(
            lambda c: not (c.checklist_emisor and c.checklist_irregularidades and c.checklist_firma)
        )
        if cheques_sin_checklist:
            raise models.ValidationError(_('Todos los cheques deben tener el checklist completo antes de confirmar la compra.'))
        
        # Guardar los valores importantes antes de cualquier operación
        cheque_ids = cheques.ids
        cantidad_cheques = len(cheque_ids)
        monto_total = sum(cheques.mapped('monto'))
        precio_total = sum(cheques.mapped('precio_compra'))
        
        # Cambiar estado de todos los cheques a disponible
        self.env['chequera.check'].browse(cheque_ids).write({
            'state': 'disponible',
            'proveedor_id': self.proveedor_id.id,
            'is_in_purchase_wizard': False  # Liberar el flag
        })
        
        # Crear un solo movimiento en la wallet por el total
        movement = self.env['chequera.wallet.movement'].create({
            'partner_id': self.proveedor_id.id,
            'tipo': 'compra',
            'monto': precio_total,
            'fecha': self.fecha_operacion,
            'multiple_checks': True,
            'check_ids': [(6, 0, cheque_ids)],
            'notes': f'Compra múltiple: {cantidad_cheques} cheques por un total de {monto_total}'
        })
        
        # Cambiar el estado del wizard a confirmado
        self.write({'state': 'confirmado'})
        
        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Compra Exitosa'),
                'message': _('Se han comprado %s cheques por un total de $ %s') % (cantidad_cheques, precio_total),
                'sticky': False,
            }
        }
    
    def action_cancelar(self):
        """Cancelar la operación de compra"""
        self.write({'state': 'cancelado'})
        return True