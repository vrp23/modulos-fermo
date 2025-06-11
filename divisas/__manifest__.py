# -*- coding: utf-8 -*-
{
    'name': 'Compra y Venta de Divisas y Criptomonedas',
    'version': '1.0',
    'category': 'Finance',
    'summary': 'Gestión de operaciones de compra y venta de USD y USDT',
    'description': """
Módulo de Gestión de Compra-Venta de Divisas y Criptomonedas
============================================================

Este módulo implementa la gestión completa de operaciones de compra y venta de divisas (USD) y criptomonedas (USDT).

Características principales:
---------------------------
* Gestión de wallets en múltiples monedas (ARS, USD, USDT)
* Dashboard con acceso rápido a operaciones y visualización de últimas transacciones
* Compra y venta de divisas con tipos de cambio configurables
* Intercambio entre diferentes pares de monedas
* Historial detallado de operaciones por cliente
* Tipos de cambio personalizables con historial

Desarrollado por VRP - Virtual Remote Partner
    """,
    'author': 'VRP - Virtual Remote Partner',
    'website': 'https://vrp.com.ar',
    'depends': [
        'base',
        'mail',
        'web',
        # Asumimos que el módulo de cheques se llama 'chequera'
        'chequera',
    ],
    'data': [
        'security/divisas_security.xml',
        'security/ir.model.access.csv',
        'data/divisas_data.xml',
        'views/divisas_dashboard_view.xml',
        'views/divisas_currency_view.xml',
        'views/divisas_exchange_wizard_view.xml',
        'views/divisas_wallet_view.xml',
        'views/divisas_exchange_rate_view.xml',
        'views/partner_view_inherit.xml',  # Agregar esta línea
        'views/divisas_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
    'assets': {
        'web.assets_backend': [
            'divisas/static/src/scss/divisas.scss',
        ],
    },
}