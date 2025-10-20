#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook para WhatsApp (Twilio Sandbox) + loop de recordatorios en background.
Endpoint principal: POST /whatsapp  (recibe From y Body de Twilio)
Health: GET / (o /health)
Start command recomendado en Render: gunicorn webhook:app -b 0.0.0.0:$PORT -w 1
"""

from flask import Flask, request, Response
import os
import threading
import sys
import traceback

# Importar las funciones desde estilista.py
from estilista import cargar_clientas, iniciar_sistema

# Importar el sistema conversacional
from conversational import procesar_mensaje, mensaje_menu

app = Flask(__name__)

# Cargar clientas al iniciar
cargar_clientas()

def safe_reply_xml(text):
    """Responder TwiML simple con escape de caracteres especiales."""
    from xml.sax.saxutils import escape
    text_safe = escape(text)
    xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{text_safe}</Message></Response>"
    return Response(xml, status=200, mimetype='application/xml')

# ---------- Endpoints ----------
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return "Estilista: OK\n", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Webhook principal que maneja mensajes de WhatsApp usando sistema conversacional."""
    try:
        from_num = request.form.get("From", "")
        body = request.form.get("Body", "").strip()
    except Exception as e:
        return safe_reply_xml("Error leyendo el mensaje."), 400

    # Extraer número limpio (quitar whatsapp: prefix si existe)
    telefono = from_num.replace("whatsapp:", "").strip()
    
    try:
        # Si es el primer mensaje, mostrar menú
        if not body:
            reply = mensaje_menu()
        else:
            # Procesar mensaje según estado de sesión
            reply = procesar_mensaje(telefono, body)
    except Exception as e:
        tb = traceback.format_exc()
        print("Error al procesar webhook:", tb, file=sys.stderr)
        reply = "⚠️ Error interno. Escribe MENU para reiniciar."

    return safe_reply_xml(reply)

# ---------- Background logic: iniciar schedule en hilo ----------
def start_background_logic():
    try:
        # iniciar_sistema() contiene su propio loop (schedule.run_pending)
        # Lo corremos en un hilo demonio para que no bloquee el servidor web
        iniciar_sistema()
    except Exception as e:
        print("Excepción en start_background_logic:", e, file=sys.stderr)

# Lanzar el hilo solo una vez al importar el módulo (en gunicorn esto corre en cada worker)
if os.getenv("RUN_BACKGROUND_LOGIC", "1") == "1":
    t = threading.Thread(target=start_background_logic, daemon=True)
    t.start()

# El app Flask se exporta como 'app' para gunicorn
if __name__ == "__main__":
    # Ejecutar en modo debug si se corre localmente
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)