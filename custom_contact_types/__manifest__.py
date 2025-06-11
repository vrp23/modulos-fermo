{
    'name': 'Tipos de Contacto Personalizados',
    'version': '1.0',
    'summary': 'Personaliza los tipos de contactos y añade campos personalizados',
    'description': """
        Este módulo permite:
        - Crear diferentes tipos de contactos
        - Añadir campos personalizados para tasas y comisiones
    """,
    'category': 'Contacts',
    'author': 'VRP',
    'website': 'https://virtualremotepartner.com/',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_type_views.xml',
        'views/res_partner_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}