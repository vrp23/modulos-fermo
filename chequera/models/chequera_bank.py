from odoo import models, fields, api

class ChequeraBank(models.Model):
    _name = 'chequera.bank'
    _description = 'Banco para Cheques'
    _order = 'name'

    name = fields.Char(string='Nombre del Banco', required=True)
    code = fields.Char(string='Código', required=True)
    active = fields.Boolean(string='Activo', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del banco debe ser único.')
    ]