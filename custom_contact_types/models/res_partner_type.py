from odoo import models, fields, api

class ResPartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Tipo de Contacto'
    
    name = fields.Char(string='Nombre del Tipo', required=True)
    code = fields.Char(string='Código', required=True)
    description = fields.Text(string='Descripción')
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', '¡El código del tipo de contacto debe ser único!')
    ]