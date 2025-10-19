# 💇‍♀️ Sistema de Recordatorios de Estilista (Twilio WhatsApp Bot)

Este proyecto es un sistema de automatización para estilistas que gestiona una base de datos de clientas y envía recordatorios automáticos de retoque a través de WhatsApp, utilizando la API de Twilio.

## ✨ Funcionalidades

* **Mensajería Automatizada:** Envía mensajes de recordatorio personalizados vía WhatsApp (usando Twilio).
* **Gestión de Clientas:** Permite agregar, ver y actualizar el último tratamiento de las clientas desde la consola.
* **Persistencia de Datos:** Guarda y carga automáticamente la base de datos de clientas en `clientas.json`.
* **Programación Diaria:** Usa la librería `schedule` para verificar diariamente (a las 10:00 a.m.) qué clientas están próximas a su retoque.
* **Seguridad:** Utiliza variables de entorno para proteger las credenciales de Twilio.

## 🛠️ Requisitos de Instalación

Asegúrate de tener **Python 3.x** instalado.

### 1. Clona el Repositorio

```bash
git clone tu-repositorio-aqui
cd mi-estilista-bot