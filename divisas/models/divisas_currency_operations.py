# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class DivisasCurrencyOperations(models.Model):
    _inherit = 'divisas.currency'
    
    # Métodos de operaciones
    def action_confirm(self):
        """Confirma la operación y crea el movimiento en la wallet"""
        self.ensure_one()
        
        if not self.currency_type or not self.payment_currency_type:
            raise UserError(_('Debe seleccionar ambas monedas para la operación'))
        
        if self.currency_type == self.payment_currency_type:
            raise UserError(_('La moneda de operación y de pago no pueden ser iguales'))
        
        if self.amount <= 0:
            raise UserError(_('El monto debe ser mayor a cero'))
        
        if not self.exchange_rate or self.exchange_rate <= 0:
            raise UserError(_('El tipo de cambio debe ser mayor a cero'))
        
        # Crear el movimiento en la wallet
        wallet_movement = self.env['divisas.wallet.movement'].create({
            'partner_id': self.partner_id.id,
            'currency_operation_id': self.id,
            'operation_type': self.operation_type,
            'currency_type': self.currency_type,
            'payment_currency_type': self.payment_currency_type,
            'amount': self.amount,
            'payment_amount': self.payment_amount,
            'date': self.date,
            'notes': self.notes,
        })
        
        self.wallet_movement_id = wallet_movement.id
        self.state = 'confirmed'
        return True
    
    def action_cancel(self):
        """Cancela la operación y revierte el movimiento en la wallet"""
        self.ensure_one()
        
        if self.state != 'confirmed':
            raise UserError(_('Solo se pueden cancelar operaciones confirmadas'))
        
        if self.wallet_movement_id:
            self.wallet_movement_id.action_cancel()
            
        self.state = 'cancelled'
        return True