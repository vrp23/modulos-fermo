# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class DivisasCurrency(models.Model):
    _name = 'divisas.currency'
    _description = 'Operación de Divisa/Cripto'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    
    # Campos para el dashboard
    recent_buys = fields.Many2many('divisas.currency', compute='_compute_dashboard_data',
                                  string='Últimas Compras')
    recent_sells = fields.Many2many('divisas.currency', compute='_compute_dashboard_data', 
                                   string='Últimas Ventas')
    current_rates = fields.Many2many('divisas.exchange.rate', compute='_compute_dashboard_data',
                                    string='Tipos de Cambio Actuales')

    # Campos básicos
    name = fields.Char(string='Referencia', required=True, copy=False, 
                       readonly=True, default=lambda self: _('Nuevo'))
    
    # Estado de la operación
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)
    
    # Tipo de operación
    operation_type = fields.Selection([
        ('buy', 'Compra'),
        ('sell', 'Venta')
    ], string='Tipo de Operación', required=True, tracking=True)
    
    # Fechas
    date = fields.Date(string='Fecha de Operación', required=True, 
                       default=fields.Date.context_today, tracking=True)
    
    # Cliente/Proveedor
    partner_id = fields.Many2one('res.partner', string='Cliente/Contacto', 
                                 required=True, tracking=True)
    
    # Monedas de la operación (ahora como selección directa)
    currency_type = fields.Selection([
        ('USD', 'Dólares (USD)'),
        ('USDT', 'Tether (USDT)'),
        ('ARS', 'Pesos (ARS)')
    ], string='Moneda', required=True, tracking=True)
    
    payment_currency_type = fields.Selection([
        ('ARS', 'Pesos (ARS)'),
        ('USD', 'Dólares (USD)'),
        ('USDT', 'Tether (USDT)')
    ], string='Moneda de Pago', required=True, tracking=True)
    
    # Montos
    amount = fields.Float(string='Monto', required=True, tracking=True, default=1.0)  # Valor por defecto para evitar errores
    payment_amount = fields.Float(string='Monto a Pagar', compute='_compute_payment_amount', 
                                 store=True, tracking=True)
    
    # Tipo de cambio
    exchange_rate = fields.Float(string='Tipo de Cambio', digits=(16, 6), 
                                required=True, tracking=True, default=1.0)  # Valor por defecto para evitar errores
    is_custom_rate = fields.Boolean(string='Tipo de Cambio Personalizado', default=False)
    
    # Notas
    notes = fields.Text(string='Notas')
    
    # Wallet Movement
    wallet_movement_id = fields.Many2one('divisas.wallet.movement', string='Movimiento de Wallet', 
                                         readonly=True)
    
    # Multi-compañía
    company_id = fields.Many2one('res.company', string='Compañía', 
                                required=True, default=lambda self: self.env.company)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                if vals.get('operation_type') == 'buy':
                    prefix = 'COMPRA'
                else:
                    prefix = 'VENTA'
                vals['name'] = prefix + self.env['ir.sequence'].next_by_code('divisas.currency') or _('Nuevo')
            
            # Asegurarse de que el tipo de cambio tenga un valor
            if 'exchange_rate' not in vals or not vals.get('exchange_rate'):
                vals['exchange_rate'] = 1.0
                
            # Asegurarse de que el monto tenga un valor
            if 'amount' not in vals or not vals.get('amount'):
                vals['amount'] = 1.0
                
        return super(DivisasCurrency, self).create(vals_list)
    
    @api.depends('amount', 'exchange_rate', 'operation_type')
    def _compute_payment_amount(self):
        for record in self:
            # Asegurarse de que hay valores válidos
            if not record.amount:
                record.amount = 0.0
            
            if not record.exchange_rate or record.exchange_rate <= 0:
                record.exchange_rate = 1.0
                
            if record.operation_type == 'buy':
                # En compra, multiplicamos por el tipo de cambio (por ejemplo, USD a ARS)
                record.payment_amount = record.amount * record.exchange_rate
            else:
                # En venta, dividimos por el tipo de cambio (por ejemplo, ARS a USD)
                if record.exchange_rate > 0:
                    record.payment_amount = record.amount / record.exchange_rate
                else:
                    record.payment_amount = record.amount
    
    @api.onchange('currency_type', 'payment_currency_type', 'operation_type')
    def _onchange_currencies(self):
        """Carga el tipo de cambio actual cuando cambian las monedas"""
        if self.currency_type and self.payment_currency_type:
            if self.currency_type == self.payment_currency_type:
                raise UserError(_('La moneda de operación y de pago no pueden ser iguales'))
            
            # Buscar el tipo de cambio actual
            try:
                exchange_rate_obj = self.env['divisas.exchange.rate']
                rate = exchange_rate_obj.get_current_rate(
                    self.currency_type, 
                    self.payment_currency_type,
                    self.operation_type
                )
                self.exchange_rate = rate
                self.is_custom_rate = False
            except Exception as e:
                # En caso de error, establecer un tipo de cambio por defecto
                self.exchange_rate = 1.0
                self.is_custom_rate = True
    
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
    
    def action_draft(self):
        """Regresa la operación a estado borrador"""
        self.ensure_one()
        
        if self.state != 'cancelled':
            raise UserError(_('Solo se pueden reactivar operaciones canceladas'))
        
        self.state = 'draft'
        return True
        
    def _compute_dashboard_data(self):
        """Calcula los datos para el dashboard"""
        # Para evitar errores cuando se llama desde una función en data.xml durante la instalación
        if not self.env.is_installed("divisas"):
            return
            
        # Obtener las últimas compras
        recent_buys = self.env['divisas.currency'].search(
            [('operation_type', '=', 'buy'), ('state', '=', 'confirmed')],
            order='date desc, id desc',
            limit=10
        )
        
        # Obtener las últimas ventas
        recent_sells = self.env['divisas.currency'].search(
            [('operation_type', '=', 'sell'), ('state', '=', 'confirmed')],
            order='date desc, id desc',
            limit=10
        )
        
        # Obtener los tipos de cambio actuales
        current_rates = self.env['divisas.exchange.rate'].search(
            [('active', '=', True)],
            order='date desc, id desc'
        )
        
        # Filtrar para obtener solo el último tipo de cambio para cada par de monedas
        unique_rates = {}
        for rate in current_rates:
            key = (rate.from_currency_type, rate.to_currency_type)
            if key not in unique_rates:
                unique_rates[key] = rate.id
        
        current_rates = self.env['divisas.exchange.rate'].browse(list(unique_rates.values()))
        
        # Asignar a todas las instancias (incluso si es una sola para el dashboard)
        for record in self:
            record.recent_buys = recent_buys
            record.recent_sells = recent_sells
            record.current_rates = current_rates
    
    def action_open_buy_wizard(self):
        """Abre el wizard para comprar divisa"""
        return {
            'name': _('Comprar Divisa'),
            'type': 'ir.actions.act_window',
            'res_model': 'divisas.exchange.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_operation_type': 'buy'}
        }
    
    def action_open_sell_wizard(self):
        """Abre el wizard para vender divisa"""
        return {
            'name': _('Vender Divisa'),
            'type': 'ir.actions.act_window',
            'res_model': 'divisas.exchange.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_operation_type': 'sell'}
        }