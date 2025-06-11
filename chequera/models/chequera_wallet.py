from odoo import models, fields, api

class ChequeraWalletMovement(models.Model):
    _name = 'chequera.wallet.movement'
    _description = 'Movimiento de Wallet de Chequera'
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Referencia', compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', required=True, index=True)
    cheque_id = fields.Many2one('chequera.check', string='Cheque', index=True)
    tipo = fields.Selection([
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ('anulacion', 'Anulación')
    ], string='Tipo de operación', required=True, index=True)
    monto = fields.Float(string='Monto', required=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True, index=True)
    active = fields.Boolean(string='Activo', default=True, 
                           help="Si se desactiva, este movimiento no se considerará para el cálculo del saldo")
    
    # Estado del movimiento
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('anulado', 'Anulado')
    ], string='Estado', default='confirmado', required=True, index=True)
    
    # Campo para almacenar los detalles de cheques en operaciones múltiples
    multiple_checks = fields.Boolean(string='Operación múltiple', default=False, 
                                    help="Indica si este movimiento corresponde a una operación con múltiples cheques")
    check_ids = fields.Many2many('chequera.check', string='Cheques relacionados', 
                                help="Cheques incluidos en esta operación")
    
    # Campo de notas para cualquier aclaración
    notes = fields.Text(string='Notas')
    
    # Campos para compensaciones por rechazos
    es_compensacion = fields.Boolean(string='Es compensación', default=False, 
                                    help="Indica si este movimiento es una compensación por rechazo de cheque")
    movement_origin_id = fields.Many2one('chequera.wallet.movement', string='Movimiento original',
                                        help="Movimiento original que se está compensando")
    
    @api.depends('partner_id', 'tipo', 'cheque_id', 'fecha', 'multiple_checks', 'check_ids', 'es_compensacion')
    def _compute_name(self):
        for record in self:
            if record.es_compensacion:
                if record.cheque_id:
                    cheque_name = record.cheque_id.name or 'S/N'
                    record.name = f"Compensación - {cheque_name} - {record.fecha.strftime('%d/%m/%Y') if record.fecha else ''}"
                else:
                    record.name = f"Compensación - {record.fecha.strftime('%d/%m/%Y') if record.fecha else ''}"
            elif record.multiple_checks and record.check_ids:
                cantidad_cheques = len(record.check_ids)
                partner_name = record.partner_id.name or 'S/N'
                tipo_desc = dict(record._fields['tipo'].selection).get(record.tipo, '')
                
                if record.fecha:
                    fecha_str = record.fecha.strftime('%d/%m/%Y')
                    record.name = f"{tipo_desc} Múltiple - {cantidad_cheques} cheques - {partner_name} - {fecha_str}"
                else:
                    record.name = f"{tipo_desc} Múltiple - {cantidad_cheques} cheques - {partner_name}"
            else:
                cheque_name = record.cheque_id.name or 'S/N'
                partner_name = record.partner_id.name or 'S/N'
                tipo_desc = dict(record._fields['tipo'].selection).get(record.tipo, '')
                
                if record.fecha:
                    fecha_str = record.fecha.strftime('%d/%m/%Y')
                    record.name = f"{tipo_desc} - {cheque_name} - {partner_name} - {fecha_str}"
                else:
                    record.name = f"{tipo_desc} - {cheque_name} - {partner_name}"
    
    def action_confirm(self):
        """Confirmar el movimiento"""
        self.write({'state': 'confirmado'})
        return True
    
    def action_cancel(self):
        """Anular el movimiento"""
        self.write({'state': 'anulado', 'active': False})
        return True
    
    def action_reset_to_draft(self):
        """Volver a borrador"""
        self.write({'state': 'borrador'})
        return True