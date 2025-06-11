README.md - Módulo de Divisas
Módulo de Gestión de Compra-Venta de Divisas y Criptomonedas para Odoo 17 CE
Este módulo implementa la gestión completa de operaciones de compra y venta de divisas (USD), pesos (ARS) y criptomonedas (USDT).
Características principales

Gestión de wallets en múltiples monedas: Soporte para wallets en ARS, USD y USDT por contacto
Dashboard con operaciones rápidas: Acceso inmediato a las funciones más utilizadas y visualización de últimas transacciones
Compra y venta de divisas: Operaciones bidireccionales entre todas las monedas soportadas
Tipos de cambio configurables: Posibilidad de definir y actualizar tipos de cambio personalizados
Historial detallado: Registro completo de todas las operaciones por cliente
Integración con módulo Chequera: Sincronización con la wallet ARS existente

Flujo de operación
Compra de divisas:

La empresa compra divisa al partner (el partner entrega divisa y recibe pago)
Seleccionar contacto
Seleccionar divisa a comprar (USD, USDT, ARS)
Seleccionar moneda de pago (diferente a la comprada)
El sistema aplica el tipo de cambio configurado (personalizable por operación)
Al confirmar, se actualizan las wallets correspondientes del partner

Venta de divisas:

La empresa vende divisa al partner (el partner recibe divisa y entrega pago)
Seleccionar contacto
Seleccionar divisa a vender (USD, USDT, ARS)
Seleccionar moneda de pago (diferente a la vendida)
El sistema aplica el tipo de cambio configurado (personalizable por operación)
Al confirmar, se actualizan las wallets correspondientes del partner

Configuración
Tipos de cambio:

Mantenimiento de tasas: Posibilidad de crear y actualizar tipos de cambio entre pares de monedas
Tasas de compra y venta: Definición de tipos de cambio diferentes para compra y venta
Historial de cambios: Registro temporal de las modificaciones de tipos de cambio

Dependencias

Módulo chequera (para la integración con wallet ARS)
Módulos base de Odoo (base, mail, web)

Instalación

Copiar el módulo en la carpeta de addons de Odoo
Actualizar la lista de módulos desde el menú Aplicaciones
Buscar "Compra y Venta de Divisas y Criptomonedas" e instalar

Uso básico

Dashboard: Acceso rápido desde el menú principal a las operaciones de compra y venta
Operaciones: Realizar compras o ventas desde los wizards correspondientes
Configuración: Gestionar tipos de cambio desde el menú de configuración
Consultas: Ver movimientos de wallet para cada contacto desde su ficha

Información de soporte
Para soporte técnico o consultas sobre el módulo:

Desarrollado por: VRP - Virtual Remote Partner
Versión: 1.0
Compatibilidad: Odoo 17 Community Edition

Consideraciones para desarrollos futuros

Este módulo está diseñado para integrarse con un futuro módulo de "Caja" para gestionar el flujo físico de dinero
La arquitectura permite extender fácilmente para soportar más monedas
Se pueden implementar restricciones o validaciones adicionales según requerimientos específicos

Nota: Las wallets de los contactos pueden quedar con saldo negativo sin restricciones.