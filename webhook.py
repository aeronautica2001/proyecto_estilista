#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook para WhatsApp (Twilio Sandbox) + loop de recordatorios en background.
Endpoint principal: POST /whatsapp  (recibe From y Body de Twilio)
Health: GET / (o /health)
Start command recomendado en Render: gunicorn webhook:app -b 0.0.0.0:$PORT -w 1
"""

from flask import Flask, request, abort, Response
import os
import json
import threading
import sys
import traceback

# Importar las funciones y datos desde estilista.py
# estilista.py debe definir: cargar_clientas, guardar_clientas, clientas,
# verificar_tratamientos, crear_mensaje_recordatorio, enviar_whatsapp, iniciar_sistema
from estilista import cargar_clientas, guardar_clientas, clientas, verificar_tratamientos, crear_mensaje_recordatorio, enviar_whatsapp, iniciar_sistema

app = Flask(__name__)

# Cargar clientas al iniciar
cargar_clientas()

# ---------- Utilidades de parseo de comandos ----------
def parse_command(body):
    if not body:
        return ("", "")
    txt = body.strip()
    parts = txt.split(None, 1)
    if len(parts) == 0:
        return ("", "")
    if len(parts) == 1:
        return (parts[0].upper(), "")
    return (parts[0].upper(), parts[1].strip())

def safe_reply_xml(text):
    # Responder TwiML simple
    # Escapar caracteres especiales si hace falta (Twilio tolera texto plano)
    xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{text}</Message></Response>"
    return Response(xml, status=200, mimetype='application/xml')

# ---------- Endpoints ----------
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return "Estilista: OK\n", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # Twilio envía form-encoded: 'From' y 'Body' entre otros campos
    try:
        from_num = request.form.get("From", "")
        body = request.form.get("Body", "").strip()
    except Exception as e:
        return safe_reply_xml("Error leyendo el mensaje."), 400

    cmd, args = parse_command(body)
    reply = "Comando no reconocido. Envía AYUDA para ver opciones."

    try:
        if cmd in ("AYUDA", "HELP"):
            reply = ("Comandos:\n"
                     "- AGREGAR Nombre; telefono; tratamiento; ultimo(AAAA-MM-DD opcional); proximo(AAAA-MM-DD opcional)\n"
                     "- LISTAR\n"
                     "- VER id\n"
                     "- ACTUALIZAR id; campo; valor\n"
                     "- RECORDAR  -> Ejecuta verificación ahora\n"
                     "- AYUDA")
        elif cmd == "LISTAR":
            if not clientas:
                reply = "No hay clientas registradas."
            else:
                lines = []
                for c in clientas:
                    lines.append(f"{c['id']}: {c['nombre']} - Próx: {c.get('proximo_recordatorio') or '—'}")
                reply = "\n".join(lines[:20])
        elif cmd == "VER":
            try:
                cid = int(args)
                c = next((x for x in clientas if x.get("id") == cid), None)
                if c:
                    # Mostrar campos clave (sin JSON crudo largo)
                    reply = (f"ID {c['id']}\nNombre: {c.get('nombre')}\nTel: {c.get('telefono')}\n"
                             f"Tratamiento: {c.get('tipo_tratamiento')}\nÚltimo: {c.get('ultimo_tratamiento')}\n"
                             f"Próx record: {c.get('proximo_recordatorio') or '—'}")
                else:
                    reply = f"ID {cid} no encontrado."
            except Exception:
                reply = "Uso: VER <id>"
        elif cmd == "AGREGAR":
            # Formato: Nombre; telefono; tratamiento; ultimo; proximo
            parts = [p.strip() for p in args.split(";")]
            if len(parts) < 2:
                reply = "Uso: AGREGAR Nombre; +57300...; tratamiento; ultimo(AAAA-MM-DD opt); proximo(AAAA-MM-DD opt)"
            else:
                nuevo_id = max((c.get("id",0) for c in clientas), default=0) + 1
                nombre = parts[0]
                telefono = parts[1]
                tipo_trat = parts[2] if len(parts) > 2 and parts[2] else None
                ultimo = parts[3] if len(parts) > 3 and parts[3] else None
                pr = parts[4] if len(parts) > 4 and parts[4] else None
                nueva = {
                    "id": nuevo_id,
                    "nombre": nombre,
                    "telefono": telefono,
                    "ultimo_tratamiento": ultimo or None,
                    "tipo_tratamiento": tipo_trat,
                    "tipo_cabello": None,
                    "notas": None,
                    "proximo_recordatorio": pr,
                    "ultimo_recordatorio_enviado": None
                }
                clientas.append(nueva)
                guardar_clientas()
                reply = f"✅ Clienta agregada: {nombre} (ID {nuevo_id})"
        elif cmd == "ACTUALIZAR":
            # ACTUALIZAR id; campo; valor
            parts = [p.strip() for p in args.split(";")]
            if len(parts) < 3:
                reply = "Uso: ACTUALIZAR id; campo; valor"
            else:
                try:
                    cid = int(parts[0])
                except:
                    reply = "ID inválido."
                    return safe_reply_xml(reply)
                campo = parts[1]
                valor = parts[2]
                clienta = next((x for x in clientas if x.get("id")==cid), None)
                if not clienta:
                    reply = f"ID {cid} no encontrado."
                else:
                    clienta[campo] = valor
                    guardar_clientas()
                    reply = f"✅ Actualizado {campo} para ID {cid}."
        elif cmd == "RECORDAR":
            # Ejecutar verificación ahora
            verificar_tratamientos()
            reply = "✅ Verificación ejecutada. Revisa logs para envíos."
        else:
            reply = "Comando no reconocido. Envía AYUDA."
    except Exception as e:
        tb = traceback.format_exc()
        print("Error al procesar webhook:", tb, file=sys.stderr)
        reply = "Error interno al procesar comando."

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