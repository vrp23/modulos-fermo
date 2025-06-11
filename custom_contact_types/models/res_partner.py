from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Campo para asignar tipo de contacto
    partner_type_id = fields.Many2one('res.partner.type', string='Tipo de Contacto')
    
    # Campos personalizados mencionados en los requerimientos
    pesification_rate = fields.Float(string='Tasa de Pesificación (%)', default=0.0)
    monthly_interest = fields.Float(string='Interés mensual (%)', default=0.0)
    assigned_seller_id = fields.Many2one('res.users', string='Vendedor asignado')
    
    # Campos de comisiones
    commission_checks = fields.Float(string='Comisiones - Cheques (%)', default=0.0)
    commission_dollars = fields.Float(string='Comisiones - Dólares (%)', default=0.0)
    commission_crypto = fields.Float(string='Comisiones - Criptos (%)', default=0.0)
    commission_transfers = fields.Float(string='Comisiones - Transferencias (%)', default=0.0)
    commission_cables = fields.Float(string='Comisiones - Cables (%)', default=0.0)
    
    @api.onchange('assigned_seller_id')
    def _onchange_assigned_seller_id(self):
        """Sincroniza el vendedor asignado con el comercial nativo de Odoo"""
        if self.assigned_seller_id:
            self.user_id = self.assigned_seller_id
    
    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Sincroniza el comercial nativo de Odoo con el vendedor asignado"""
        if self.user_id:
            self.assigned_seller_id = self.user_id