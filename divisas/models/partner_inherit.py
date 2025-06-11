# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # La wallet en ARS ya existe en el módulo anterior (chequera)
    # wallet_balance = fields.Float(string='Saldo Wallet ARS', default=0.0)
    
    wallet_usd_balance = fields.Float(string='Saldo Wallet USD', default=0.0)
    wallet_usdt_balance = fields.Float(string='Saldo Wallet USDT', default=0.0)
    
    def action_view_wallet_movements(self):
        """Acción para ver los movimientos de wallet del contacto"""
        self.ensure_one()
        return {
            'name': _('Movimientos de Wallet'),
            'type': 'ir.actions.act_window',
            'res_model': 'divisas.wallet.movement',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }