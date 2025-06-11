from odoo import models, fields, api, _
import logging

class ChequeraCheckOperations(models.Model):
    _inherit = 'chequera.check'
    
    # Métodos de acciones para botones
    def action_comprar(self):
        """En lugar de comprar directamente, abre el wizard para más flexibilidad"""
        return {
            'name': _('Compra de Cheques'),
            'view_mode': 'form',
            'res_model': 'chequera.purchase.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'active_model': 'chequera.check',
                'active_id': self.id,
            }
        }
    
    def action_edit_cheque(self):
        """Método para editar un cheque desde el wizard de compra"""
        # Obtener el ID del cheque del contexto
        cheque_id = self._context.get('cheque_id', self.id)
        wizard_id = self._context.get('wizard_id')
        
        return {
            'name': _('Editar Cheque'),
            'view_mode': 'form',
            'res_model': 'chequera.check',
            'res_id': cheque_id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_is_in_purchase_wizard': True,
                'wizard_id': wizard_id,
            },
            'target': 'new',
            'flags': {'mode': 'edit'},
        }
    
    def action_save_and_return(self):
        """Guarda el cheque y vuelve al wizard"""
        self.ensure_one()
        # Activamos logging para depuración
        _logger = logging.getLogger(__name__)
        _logger.info("Ejecutando action_save_and_return. ID del cheque: %s", self.id)
        
        # Obtenemos el ID del wizard del contexto
        wizard_id = self._context.get('wizard_id')
        _logger.info("wizard_id del contexto: %s", wizard_id)
        
        if wizard_id:
            # Como ahora el wizard es un modelo regular, será más fácil encontrarlo
            wizard = self.env['chequera.purchase.wizard'].browse(int(wizard_id))
            
            # Verificamos que el wizard exista
            if wizard.exists():
                _logger.info("Wizard encontrado, ID: %s", wizard.id)
                
                # Aseguramos que el cheque esté en la lista
                if self.id not in wizard.check_ids.ids:
                    wizard.write({'check_ids': [(4, self.id)]})
                    _logger.info("Cheque agregado al wizard, IDs actuales: %s", wizard.check_ids.ids)
                
                # Devolvemos una acción que reabra el wizard
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Compra de Cheques'),
                    'res_model': 'chequera.purchase.wizard',
                    'res_id': int(wizard_id),
                    'view_mode': 'form',
                    'target': 'current', # Cambiado de 'new' a 'current' para abrir en la misma ventana
                    'flags': {
                        'mode': 'edit',
                        'action_buttons': True,
                    },
                }
            else:
                _logger.warning("No se encontró el wizard con ID: %s", wizard_id)
        else:
            _logger.warning("No se encontró wizard_id en el contexto")
        
        # Si llegamos aquí, hubo un problema y solo cerramos la ventana actual
        # sin cerrar el wizard padre que debería seguir abierto
        return {'type': 'ir.actions.act_window_close'}
    
    def action_vender(self):
        """Acción para vender el cheque - ahora abre el wizard de venta múltiple"""
        return {
            'name': _('Venta de Cheques'),
            'view_mode': 'form',
            'res_model': 'chequera.sale.wizard',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_check_ids': [(6, 0, [self.id])],
            }
        }
    
    def action_anular(self):
        """Acción para anular el cheque"""
        self.write({'state': 'anulado'})
        return True
    
    def action_reset_to_draft(self):
        """Resetear a borrador"""
        # Solo permitir si está en estado disponible o anulado
        if self.state in ['disponible', 'anulado', 'rechazado']:
            # Si hay un movimiento de wallet asociado, también debería anularse
            self.write({'state': 'borrador'})
        return True
    
    @api.onchange('proveedor_id')
    def _onchange_proveedor_id(self):
        """Al cambiar el proveedor, cargar valores predeterminados"""
        if self.proveedor_id:
            # CAMBIO: Cargar tasas específicas de compra
            self.tasa_pesificacion_compra = self.proveedor_id.tasa_pesificacion_compra
            self.interes_mensual_compra = self.proveedor_id.interes_mensual_compra
            self.vendedor_id_compra = self.proveedor_id.assigned_seller_id
    
    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        """Al cambiar el cliente, cargar valores predeterminados"""
        if self.cliente_id:
            # CAMBIO: Cargar tasas específicas de venta
            self.tasa_pesificacion_venta = self.cliente_id.tasa_pesificacion_venta
            self.interes_mensual_venta = self.cliente_id.interes_mensual_venta
            self.vendedor_id_venta = self.cliente_id.assigned_seller_id
            
    def action_open_check_purchase(self):
        """Acción para abrir el wizard de compra desde el dashboard"""
        return {
            'name': _('Compra de Cheques'),
            'view_mode': 'form',
            'res_model': 'chequera.purchase.wizard',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    
    def action_open_check_sale(self):
        """Acción para abrir el wizard de venta múltiple desde el dashboard"""
        return {
            'name': _('Venta de Cheques'),
            'view_mode': 'form',
            'res_model': 'chequera.sale.wizard',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        
    # Mejorar el cálculo de datos del dashboard para asegurar que se muestren los registros
    @api.model
    def _compute_dashboard_data_static(self):
        """Método estático para obtener datos del dashboard"""
        # Últimas compras (5 más recientes)
        latest_purchases = self.env['chequera.check'].search([
            ('state', 'in', ['disponible', 'vendido', 'rechazado'])
        ], limit=5, order='create_date desc')
        
        # Cheques disponibles
        available_checks = self.env['chequera.check'].search([
            ('state', '=', 'disponible')
        ], limit=5, order='fecha_pago')
        
        return {
            'latest_purchases': latest_purchases,
            'available_checks': available_checks
        }