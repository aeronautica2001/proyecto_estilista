#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Estilista - Sistema de recordatorios WhatsApp (Twilio)

Nota: Se añadió un alias verificar_recordatorios_diarios() para mantener
compatibilidad con imports antiguos (por ejemplo desde auto_estilista.py).
"""

import json
import os
import schedule
import time
from datetime import datetime, date, timedelta
from twilio.rest import Client

# ==============================================
# CONFIGURACIÓN INICIAL (SEGURA)
# ==============================================

# Las credenciales deben establecerse en variables de entorno
# TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# Valor por defecto sólo como placeholder; en producción define la variable de entorno.
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# DummyClient correcto que imita client.messages.create(...) para pruebas locales
class DummyMessages:
    def create(self, **kwargs):
        to = kwargs.get("to")
        body = kwargs.get("body", "")
        print(f"[DEBUG] Simulado envío WhatsApp -> {to}\n       Mensaje: {body[:120]}{'...' if len(body) > 120 else ''}")
        # Simular objeto con sid
        class DummyMessageResult:
            sid = "SMDUMMY123"
        return DummyMessageResult()

class DummyClient:
    def __init__(self):
        self.messages = DummyMessages()

# Inicializar client (Twilio real o Dummy)
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    print("⚠️ Advertencia: No se encontraron variables de entorno de Twilio.")
    print("   El sistema funcionará en MODO DEBUG (no enviará mensajes reales).")
    client = DummyClient()
else:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("🔑 Credenciales Twilio cargadas correctamente.")

# ==============================================
# RUTA DE DATOS
# ==============================================

RUTA_DATOS = "clientas.json"

# ==============================================
# FUNCIONES DE GUARDADO Y CARGA
# ==============================================

def guardar_clientas():
    """Guarda la lista global clientas en clientas.json"""
    try:
        with open(RUTA_DATOS, "w", encoding="utf-8") as f:
            json.dump(clientas, f, ensure_ascii=False, indent=4)
        print("💾 Datos guardados correctamente.")
    except Exception as e:
        print(f"❌ Error al guardar datos: {e}")

def cargar_clientas():
    """Carga clientas desde clientas.json si existe"""
    global clientas
    if os.path.exists(RUTA_DATOS):
        try:
            with open(RUTA_DATOS, "r", encoding="utf-8") as f:
                clientas = json.load(f)
            print(f"📂 {len(clientas)} clientas cargadas desde {RUTA_DATOS}.")
        except Exception as e:
            print(f"⚠️ Error al cargar datos: {e}")
            clientas = []
    else:
        clientas = []
        print("📁 No existe archivo de datos. Se creará cuando agregues la primera clienta.")

# ==============================================
# DATOS INICIALES (se cargarán desde JSON)
# ==============================================

cargar_clientas()

# Si no hay clientas, opcionalmente inicializar con ejemplos (comentado por defecto)
if not clientas:
    # Si quieres ejemplos por primera vez, descomenta este bloque.
    clientas = [
        {
            "id": 1,
            "nombre": "Ana María López",
            "telefono": "+573001234567",
            "ultimo_tratamiento": "2024-08-15",
            "tipo_tratamiento": "keratina",
            "tipo_cabello": "rizado",
            "notas": "Prefiere citas los sábados",
            "proximo_recordatorio": None,
            "ultimo_recordatorio_enviado": None
        },
        {
            "id": 2,
            "nombre": "Carolina Ruiz",
            "telefono": "+573007654321",
            "ultimo_tratamiento": "2024-09-20",
            "tipo_tratamiento": "botox_capilar",
            "tipo_cabello": "ondulado",
            "notas": "Cabello teñido, usar productos sin sal",
            "proximo_recordatorio": None,
            "ultimo_recordatorio_enviado": None
        }
    ]
    guardar_clientas()

# ==============================================
# TIPOS DE TRATAMIENTOS Y DURACIÓN (configurable)
# ==============================================

TRATAMIENTOS = {
    "keratina": {
        "nombre": "Keratina / Alisado",
        "duracion_meses": 3,
        "precio": "$150.000 - $250.000",
        "beneficios": [
            "Cabello liso y manejable",
            "Brillo intenso",
            "Reduce el frizz",
            "Elimina el volumen"
        ]
    },
    "botox_capilar": {
        "nombre": "Botox Capilar",
        "duracion_meses": 2,
        "precio": "$120.000 - $180.000",
        "beneficios": [
            "Hidratación profunda",
            "Reparación del cabello",
            "Brillo y suavidad",
            "Fortalece la fibra capilar"
        ]
    },
    # Agrega más tratamientos aquí si hace falta
}

# ==============================================
# UTILIDADES DE FECHAS
# ==============================================

def hoy_str():
    return date.today().strftime("%Y-%m-%d")

def sumar_meses_aproximado(fecha_str, meses):
    """Suma 'meses' a una fecha (aproximación: 30 días por mes)."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        return None
    return (dt + timedelta(days=int(30 * meses))).strftime("%Y-%m-%d")

# ==============================================
# MENSAJERÍA (plantillas)
# ==============================================

def enviar_whatsapp(telefono, mensaje):
    """Envía mensaje por WhatsApp usando Twilio (o simula en modo debug)."""
    try:
        # Formatear número 'to' como whatsapp:+...
        to_number = telefono if telefono.startswith("whatsapp:") else f"whatsapp:{telefono}"
        result = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=mensaje,
            to=to_number
        )
        # Si DummyClient retorna un objeto simulado sin 'sid', igual reportamos éxito
        sid = getattr(result, "sid", "SID_DESCONOCIDO")
        print(f"✓ Mensaje enviado a {telefono} (sid: {sid})")
        return True
    except Exception as e:
        print(f"✗ Error al enviar a {telefono}: {e}")
        return False

def crear_mensaje_recordatorio(clienta):
    """Plantilla de recordatorio (personalizable)."""
    t_key = clienta.get("tipo_tratamiento")
    tratamiento = TRATAMIENTOS.get(t_key, {"nombre": "tu tratamiento", "precio": "Consultar"})
    mensaje = f"""
💆‍♀️ ¡Hola {clienta.get('nombre')}! ✨

Es momento de consentir tu cabello de nuevo 💕
📅 Tu recordatorio: {clienta.get('proximo_recordatorio') or 'Hoy'}

🔸 Servicio: {tratamiento.get('nombre')}
💰 Inversión estimada: {tratamiento.get('precio')}

🎁 PROMO: Si agendas esta semana, trato hidratante GRATIS + 10% dto.

📱 Agenda tu cita respondiendo este mensaje o llamando al: 350-231-7566

¿Te va bien este día para agendar? 😊
"""
    return mensaje.strip()

# ==============================================
# LÓGICA DE VERIFICACIÓN (basada en campo manual)
# ==============================================

def verificar_tratamientos():
    """
    Verifica clientas y envía recordatorio si 'proximo_recordatorio' == hoy.
    Si no existe 'proximo_recordatorio', se considera un fallback calculado
    según 'duracion_meses' (pero solo si no existe campo manual).
    Evita reenvíos múltiples marcando 'ultimo_recordatorio_enviado'.
    """
    print(f"\n{'='*48}")
    print(f"Verificación de recordatorios - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*48}\n")

    hoy = hoy_str()
    enviados = 0

    for clienta in clientas:
        # Validaciones básicas
        nombre = clienta.get("nombre", "Desconocida")
        telefono = clienta.get("telefono")
        if not telefono:
            print(f"⚠️ {nombre} no tiene teléfono registrado. Se omite.")
            continue

        # Si existe campo manual y es hoy -> enviar
        pr = clienta.get("proximo_recordatorio")
        if pr:
            if pr == hoy:
                # Evitar reenvío si ya se envió hoy
                if clienta.get("ultimo_recordatorio_enviado") == hoy:
                    print(f"ℹ️ Ya se envió recordatorio hoy a {nombre}. Se omite.")
                    continue
                mensaje = crear_mensaje_recordatorio(clienta)
                if enviar_whatsapp(telefono, mensaje):
                    clienta["ultimo_recordatorio_enviado"] = hoy
                    # Limpiar proximo_recordatorio para que la estilista ponga uno nuevo si desea
                    clienta["proximo_recordatorio"] = None
                    guardar_clientas()
                    enviados += 1
            else:
                # fecha manual pero no es hoy; no hacemos nada
                pass
        else:
            # Sin fecha manual: fallback automático calculado a partir de 'ultimo_tratamiento' y duracion_meses
            ultimo = clienta.get("ultimo_tratamiento")
            tipo = clienta.get("tipo_tratamiento")
            if ultimo and tipo and tipo in TRATAMIENTOS:
                dur = TRATAMIENTOS[tipo].get("duracion_meses", 0)
                if dur > 0:
                    fecha_estim = sumar_meses_aproximado(ultimo, dur)
                    # Si la fecha estimada coincide con hoy — tratamos esto como recordatorio (respaldo)
                    if fecha_estim == hoy:
                        if clienta.get("ultimo_recordatorio_enviado") == hoy:
                            print(f"ℹ️ (fallback) Ya se envió hoy a {nombre}.")
                            continue
                        mensaje = crear_mensaje_recordatorio(clienta)
                        if enviar_whatsapp(telefono, mensaje):
                            clienta["ultimo_recordatorio_enviado"] = hoy
                            # Dejar proximo_recordatorio en None (estaba vacío)
                            guardar_clientas()
                            enviados += 1
            else:
                # No hay forma de calcular; se omite
                print(f"ℹ️ No hay 'proximo_recordatorio' ni datos suficientes para {nombre}.")
                continue

    print(f"\n✅ Verificación finalizada. Total mensajes enviados: {enviados}")

# --- Añadido: alias para compatibilidad con nombre antiguo usado por auto_estilista.py ---
def verificar_recordatorios_diarios():
    """
    Wrapper/alias para mantener compatibilidad con importaciones que esperan
    'verificar_recordatorios_diarios'. Llama a verificar_tratamientos.
    """
    return verificar_tratamientos()

# ==============================================
# FUNCIONES DE GESTIÓN (Agregar / Mostrar / Actualizar)
# ==============================================

def input_fecha_validada(prompt, allow_empty=True):
    """Pide una fecha AAAA-MM-DD; devuelve string o None."""
    while True:
        entrada = input(prompt).strip()
        if entrada == "" and allow_empty:
            return None
        try:
            # Validar formato
            datetime.strptime(entrada, "%Y-%m-%d")
            return entrada
        except ValueError:
            print("⚠️ Formato inválido. Usa AAAA-MM-DD (ej: 2025-12-10) o deja vacío.")

def validar_telefono(prompt):
    """Solicita teléfono en formato E.164 (+571234...)"""
    while True:
        t = input(prompt).strip()
        if t.startswith("+") and t[1:].isdigit() and len(t) >= 9:
            return t
        print("⚠️ Formato inválido. Debe empezar con '+' seguido del código de país y número (ej: +573001234567).")

def agregar_clienta():
    """Agrega una nueva clienta solicitando datos en consola."""
    print("\n--- ➕ AGREGAR NUEVA CLIENTA ---")
    nuevo_id = max((c.get("id", 0) for c in clientas), default=0) + 1

    nombre = input("Nombre completo: ").strip()
    telefono = validar_telefono("Teléfono (Ej: +573001234567): ")

    # Selección de tratamiento
    print("\nTratamientos disponibles:")
    keys = list(TRATAMIENTOS.keys())
    for i, k in enumerate(keys, start=1):
        t = TRATAMIENTOS[k]
        print(f"  {i}. {t['nombre']} ({t['duracion_meses']} meses)")

    while True:
        try:
            opt = int(input(f"Selecciona tratamiento (1-{len(keys)}): ").strip())
            if 1 <= opt <= len(keys):
                tipo_trat = keys[opt - 1]
                break
        except ValueError:
            pass
        print("⚠️ Opción inválida.")

    ultimo_trat = input_fecha_validada("Fecha del último tratamiento (AAAA-MM-DD) o deja vacío para hoy: ")
    if not ultimo_trat:
        ultimo_trat = hoy_str()

    tipo_cabello = input("Tipo de cabello (liso/ondulado/rizado/muy_rizado) (opcional): ").strip()
    notas = input("Notas (opcional): ").strip()

    # Campo manual proximo_recordatorio
    print("\nPuedes definir una fecha manual para el próximo recordatorio (opcional).")
    print("Si la dejas vacía, el sistema usará un cálculo automático según el tratamiento (respaldo).")
    pr = input_fecha_validada("Próximo recordatorio (AAAA-MM-DD) o ENTER: ", allow_empty=True)

    nueva = {
        "id": nuevo_id,
        "nombre": nombre,
        "telefono": telefono,
        "ultimo_tratamiento": ultimo_trat,
        "tipo_tratamiento": tipo_trat,
        "tipo_cabello": tipo_cabello or None,
        "notas": notas or None,
        "proximo_recordatorio": pr,
        "ultimo_recordatorio_enviado": None
    }

    clientas.append(nueva)
    guardar_clientas()
    print(f"\n✅ Clienta '{nombre}' agregada (ID: {nuevo_id}).")

def mostrar_clientas():
    """Muestra la lista de clientas en tabla formateada."""
    print("\n--- 📋 LISTA DE CLIENTAS ---")
    if not clientas:
        print("Aún no hay clientas registradas.")
        return

    header = f"{'ID':>2}  {'Nombre':<22}  {'Teléfono':<15}  {'Último':<10}  {'Próx. Record.':<12}  {'Tratamiento':<18}"
    print(header)
    print("-" * len(header))

    for c in clientas:
        id_s = str(c.get("id", ""))
        nombre = (c.get("nombre") or "")[:22].ljust(22)
        tel = (c.get("telefono") or "")[:15].ljust(15)
        ult = (c.get("ultimo_tratamiento") or "")[:10].ljust(10)
        pr = (c.get("proximo_recordatorio") or "—")[:12].ljust(12)
        trat = TRATAMIENTOS.get(c.get("tipo_tratamiento"), {}).get("nombre", "Desconocido")[:18].ljust(18)
        print(f"{id_s:>2}  {nombre}  {tel}  {ult}  {pr}  {trat}")

def actualizar_tratamiento():
    """Actualizar la fecha/servicio/proximo_recordatorio de una clienta existente."""
    print("\n--- ✍️ ACTUALIZAR TRATAMIENTO / RECORDATORIO ---")
    mostrar_clientas()
    if not clientas:
        return

    while True:
        try:
            cid = int(input("Ingresa ID de la clienta a actualizar (0 para cancelar): ").strip())
            if cid == 0:
                return
            clienta = next((x for x in clientas if x.get("id") == cid), None)
            if clienta:
                break
            print("⚠️ ID no encontrado.")
        except ValueError:
            print("⚠️ Debes ingresar un número.")

    print(f"\nActualizando -> {clienta.get('nombre')} (ID {cid})")
    # Permitir cambiar tipo de tratamiento
    print("\nTratamientos:")
    keys = list(TRATAMIENTOS.keys())
    for i, k in enumerate(keys, start=1):
        t = TRATAMIENTOS[k]
        print(f"  {i}. {t['nombre']} ({t['duracion_meses']} meses)")
    while True:
        try:
            opt = input(f"Selecciona tratamiento (1-{len(keys)}) o ENTER para mantener ({clienta.get('tipo_tratamiento')}): ").strip()
            if opt == "":
                nuevo_tipo = clienta.get("tipo_tratamiento")
                break
            opt = int(opt)
            if 1 <= opt <= len(keys):
                nuevo_tipo = keys[opt - 1]
                break
        except ValueError:
            pass
        print("⚠️ Opción inválida.")

    # Fecha del último tratamiento (por defecto hoy si ENTER)
    nuevo_ultimo = input_fecha_validada("Nueva fecha de último tratamiento (AAAA-MM-DD) o ENTER para hoy: ", allow_empty=True)
    if not nuevo_ultimo:
        nuevo_ultimo = hoy_str()

    # Fecha manual del próximo recordatorio
    print("\nEstablece la fecha del próximo recordatorio (manual) o deja vacío para usar cálculo automático:")
    nuevo_pr = input_fecha_validada("Próximo recordatorio (AAAA-MM-DD) o ENTER: ", allow_empty=True)

    # Aplicar cambios
    clienta["tipo_tratamiento"] = nuevo_tipo
    clienta["ultimo_tratamiento"] = nuevo_ultimo
    clienta["proximo_recordatorio"] = nuevo_pr
    # resetear ultimo_recordatorio_enviado si deseas (opcional) -- aquí no lo hacemos para mantener historial
    guardar_clientas()

    print(f"\n✅ Datos actualizados para {clienta.get('nombre')} (ID {cid}).")

# ==============================================
# INICIO AUTOMÁTICO (schedule)
# ==============================================

def iniciar_sistema():
    """Inicia loop schedule para verificar recordatorios diariamente."""
    print("\n💇‍♀️ Sistema de Recordatorios - Iniciado")
    schedule.every().day.at("10:00").do(verificar_tratamientos)
    print("✓ Verificación programada diariamente a las 10:00 AM (hora del servidor).")
    print("✓ Ejecutando verificación inicial ahora...\n")
    verificar_tratamientos()
    print("\nPresiona Ctrl+C para detener el sistema automático y volver al menú.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Sistema automático detenido por el usuario. Volviendo al menú.")

# ==============================================
# MENÚ PRINCIPAL
# ==============================================

def main_menu():
    while True:
        print("\n" * 2)
        print("""
╔═══════════════════════════════════════════════╗
║          SISTEMA DE RECORDATORIOS - ESTILISTA 👸
╚═══════════════════════════════════════════════╝
--- Automatización ---
1. Iniciar sistema automático (24/7)
2. Enviar recordatorios AHORA

--- Gestión de Clientes ---
3. Ver lista de clientas
4. Añadir nueva clienta
5. Actualizar tratamiento / recordatorio

--- Otros ---
6. Salir
""")
        opcion = input("Selecciona una opción (1-6): ").strip()
        if opcion == "1":
            iniciar_sistema()
        elif opcion == "2":
            verificar_tratamientos()
        elif opcion == "3":
            mostrar_clientas()
        elif opcion == "4":
            agregar_clienta()
        elif opcion == "5":
            actualizar_tratamiento()
        elif opcion == "6":
            print("¡Hasta pronto! Gracias por usar el Asistente de Estilista. 💕")
            break
        else:
            print("⚠️ Opción no válida. Selecciona un número entre 1 y 6.")

if __name__ == "__main__":
    main_menu()