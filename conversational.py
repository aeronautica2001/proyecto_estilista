#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema conversacional para el bot de estilista.
Maneja sesiones en memoria y flujos paso a paso.
"""

from datetime import datetime
from estilista import clientas, guardar_clientas, TRATAMIENTOS

# Almacén de sesiones en memoria: {numero_telefono: {"estado": ..., "data": {...}}}
sesiones = {}

# Estados posibles del flujo
ESTADO_MENU = "menu"
ESTADO_AGREGAR_NOMBRE = "agregar_nombre"
ESTADO_AGREGAR_TELEFONO = "agregar_telefono"
ESTADO_AGREGAR_TRATAMIENTO = "agregar_tratamiento"
ESTADO_AGREGAR_ULTIMO = "agregar_ultimo"
ESTADO_AGREGAR_PROXIMO = "agregar_proximo"

ESTADO_ACTUALIZAR_ID = "actualizar_id"
ESTADO_ACTUALIZAR_CAMPO = "actualizar_campo"
ESTADO_ACTUALIZAR_VALOR = "actualizar_valor"

# ==============================================
# UTILIDADES
# ==============================================

def validar_fecha(texto):
    """Valida si el texto es una fecha AAAA-MM-DD válida."""
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except:
        return False

def validar_telefono(texto):
    """Valida formato +57... (mínimo 10 dígitos después del +)"""
    texto = texto.strip()
    if texto.startswith("+") and len(texto) >= 11 and texto[1:].isdigit():
        return True
    return False

def obtener_sesion(telefono):
    """Obtiene o crea una sesión para un número."""
    if telefono not in sesiones:
        sesiones[telefono] = {
            "estado": ESTADO_MENU,
            "data": {}
        }
    return sesiones[telefono]

def limpiar_sesion(telefono):
    """Limpia la sesión (volver al menú principal)."""
    if telefono in sesiones:
        sesiones[telefono] = {
            "estado": ESTADO_MENU,
            "data": {}
        }

# ==============================================
# MENSAJES
# ==============================================

def mensaje_menu():
    """Menú principal amigable."""
    return """👸 *MENÚ PRINCIPAL*

Escribe el número de la opción:

1️⃣ Agregar clienta nueva
2️⃣ Ver lista de clientas
3️⃣ Ver detalles de una clienta
4️⃣ Actualizar información
5️⃣ Ejecutar recordatorios ahora
6️⃣ Ayuda

💡 _Escribe el número para continuar_"""

def mensaje_ayuda():
    """Mensaje de ayuda."""
    return """📚 *AYUDA DEL SISTEMA*

Este bot te ayuda a gestionar tus clientas y enviar recordatorios automáticos.

*Opciones disponibles:*

1️⃣ *Agregar clienta:* Te guiaré paso a paso para registrar una nueva clienta

2️⃣ *Ver lista:* Muestra todas tus clientas registradas

3️⃣ *Ver detalles:* Consulta información completa de una clienta

4️⃣ *Actualizar:* Modifica datos de una clienta existente

5️⃣ *Recordatorios:* Envía los recordatorios programados ahora mismo

_Escribe MENU en cualquier momento para volver al inicio_ ✨"""

# ==============================================
# MANEJADOR PRINCIPAL
# ==============================================

def procesar_mensaje(telefono, mensaje):
    """
    Procesa el mensaje según el estado de la sesión.
    Retorna el texto de respuesta.
    """
    sesion = obtener_sesion(telefono)
    estado = sesion["estado"]
    data = sesion["data"]
    
    mensaje = mensaje.strip()
    mensaje_upper = mensaje.upper()
    
    # Comandos globales
    if mensaje_upper in ["MENU", "MENÚ", "INICIO"]:
        limpiar_sesion(telefono)
        return mensaje_menu()
    
    if mensaje_upper in ["AYUDA", "HELP"]:
        return mensaje_ayuda()
    
    # === MENÚ PRINCIPAL ===
    if estado == ESTADO_MENU:
        if mensaje == "1":
            sesion["estado"] = ESTADO_AGREGAR_NOMBRE
            sesion["data"] = {}
            return "✨ *AGREGAR CLIENTA NUEVA*\n\n¿Cuál es el nombre completo de la clienta?\n\n_Escribe MENU para cancelar_"
        
        elif mensaje == "2":
            return listar_clientas()
        
        elif mensaje == "3":
            return "🔍 *VER DETALLES*\n\nEscribe el ID de la clienta que quieres consultar.\n\n_Primero usa opción 2 para ver los IDs_"
        
        elif mensaje == "4":
            sesion["estado"] = ESTADO_ACTUALIZAR_ID
            sesion["data"] = {}
            return "✏️ *ACTUALIZAR INFORMACIÓN*\n\nEscribe el ID de la clienta que quieres actualizar.\n\n_Usa opción 2 para ver los IDs_"
        
        elif mensaje == "5":
            from estilista import verificar_tratamientos
            verificar_tratamientos()
            return "✅ Recordatorios ejecutados. Revisa los logs del sistema para ver los envíos."
        
        elif mensaje == "6":
            return mensaje_ayuda()
        
        else:
            # Si es un número directo (ID), mostrar detalles
            try:
                cid = int(mensaje)
                return ver_clienta(cid)
            except:
                return mensaje_menu()
    
    # === FLUJO AGREGAR CLIENTA ===
    elif estado == ESTADO_AGREGAR_NOMBRE:
        data["nombre"] = mensaje
        sesion["estado"] = ESTADO_AGREGAR_TELEFONO
        return f"Perfecto, *{mensaje}* ✨\n\n¿Cuál es su número de teléfono?\n\n_Formato: +573001234567_"
    
    elif estado == ESTADO_AGREGAR_TELEFONO:
        if not validar_telefono(mensaje):
            return "⚠️ Número inválido. Debe iniciar con *+* seguido del código de país.\n\nEjemplo: +573001234567\n\nInténtalo de nuevo:"
        data["telefono"] = mensaje
        sesion["estado"] = ESTADO_AGREGAR_TRATAMIENTO
        return mostrar_tratamientos()
    
    elif estado == ESTADO_AGREGAR_TRATAMIENTO:
        try:
            opcion = int(mensaje)
            keys = list(TRATAMIENTOS.keys())
            if 1 <= opcion <= len(keys):
                data["tipo_tratamiento"] = keys[opcion - 1]
                sesion["estado"] = ESTADO_AGREGAR_ULTIMO
                return "¿Cuándo fue su último tratamiento?\n\nFormato: *AAAA-MM-DD*\nEjemplo: 2024-10-15\n\n_O escribe SALTAR para usar la fecha de hoy_"
            else:
                return "⚠️ Opción inválida. " + mostrar_tratamientos()
        except:
            return "⚠️ Debes escribir el número de la opción.\n\n" + mostrar_tratamientos()
    
    elif estado == ESTADO_AGREGAR_ULTIMO:
        if mensaje_upper == "SALTAR":
            data["ultimo_tratamiento"] = datetime.now().strftime("%Y-%m-%d")
        elif validar_fecha(mensaje):
            data["ultimo_tratamiento"] = mensaje
        else:
            return "⚠️ Fecha inválida. Usa formato *AAAA-MM-DD*\n\nEjemplo: 2024-10-15\n\nInténtalo de nuevo:"
        
        sesion["estado"] = ESTADO_AGREGAR_PROXIMO
        return "¿Cuándo quieres enviar el recordatorio?\n\nFormato: *AAAA-MM-DD*\nEjemplo: 2025-01-15\n\n_O escribe SALTAR para dejarlo automático_"
    
    elif estado == ESTADO_AGREGAR_PROXIMO:
        if mensaje_upper == "SALTAR":
            data["proximo_recordatorio"] = None
        elif validar_fecha(mensaje):
            data["proximo_recordatorio"] = mensaje
        else:
            return "⚠️ Fecha inválida. Usa formato *AAAA-MM-DD*\n\nEjemplo: 2025-01-15\n\nInténtalo de nuevo:"
        
        # Guardar clienta
        resultado = guardar_clienta(data)
        limpiar_sesion(telefono)
        return resultado + "\n\n" + mensaje_menu()
    
    # === FLUJO ACTUALIZAR ===
    elif estado == ESTADO_ACTUALIZAR_ID:
        try:
            cid = int(mensaje)
            clienta = next((c for c in clientas if c.get("id") == cid), None)
            if clienta:
                data["id"] = cid
                data["clienta"] = clienta
                sesion["estado"] = ESTADO_ACTUALIZAR_CAMPO
                return f"Actualizando: *{clienta.get('nombre')}*\n\n¿Qué campo quieres actualizar?\n\n1️⃣ Nombre\n2️⃣ Teléfono\n3️⃣ Tipo de tratamiento\n4️⃣ Último tratamiento\n5️⃣ Próximo recordatorio\n\n_Escribe el número_"
            else:
                return f"⚠️ No existe clienta con ID {cid}.\n\nInténtalo de nuevo o escribe MENU:"
        except:
            return "⚠️ Debes escribir el ID (número).\n\nInténtalo de nuevo:"
    
    elif estado == ESTADO_ACTUALIZAR_CAMPO:
        campos = {
            "1": "nombre",
            "2": "telefono",
            "3": "tipo_tratamiento",
            "4": "ultimo_tratamiento",
            "5": "proximo_recordatorio"
        }
        if mensaje in campos:
            data["campo"] = campos[mensaje]
            sesion["estado"] = ESTADO_ACTUALIZAR_VALOR
            
            if mensaje == "3":
                return mostrar_tratamientos()
            elif mensaje in ["4", "5"]:
                return f"Nuevo valor para *{campos[mensaje]}*:\n\nFormato: *AAAA-MM-DD*\nEjemplo: 2024-10-15\n\n_O escribe NINGUNO para borrar_"
            else:
                return f"Nuevo valor para *{campos[mensaje]}*:"
        else:
            return "⚠️ Opción inválida. Escribe un número del 1 al 5:"
    
    elif estado == ESTADO_ACTUALIZAR_VALOR:
        campo = data["campo"]
        clienta = data["clienta"]
        
        # Validaciones específicas
        if campo == "telefono" and mensaje_upper != "NINGUNO":
            if not validar_telefono(mensaje):
                return "⚠️ Teléfono inválido. Formato: +573001234567\n\nInténtalo de nuevo:"
        
        if campo in ["ultimo_tratamiento", "proximo_recordatorio"] and mensaje_upper != "NINGUNO":
            if not validar_fecha(mensaje):
                return "⚠️ Fecha inválida. Formato: AAAA-MM-DD\n\nInténtalo de nuevo:"
        
        if campo == "tipo_tratamiento":
            try:
                opcion = int(mensaje)
                keys = list(TRATAMIENTOS.keys())
                if 1 <= opcion <= len(keys):
                    mensaje = keys[opcion - 1]
                else:
                    return "⚠️ Opción inválida. " + mostrar_tratamientos()
            except:
                return "⚠️ Debes escribir el número. " + mostrar_tratamientos()
        
        # Guardar cambio
        if mensaje_upper == "NINGUNO":
            clienta[campo] = None
        else:
            clienta[campo] = mensaje
        
        guardar_clientas()
        limpiar_sesion(telefono)
        return f"✅ Campo *{campo}* actualizado para {clienta.get('nombre')}\n\n" + mensaje_menu()
    
    # Fallback
    return mensaje_menu()

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

def mostrar_tratamientos():
    """Muestra lista de tratamientos disponibles."""
    texto = "💆‍♀️ *TRATAMIENTOS DISPONIBLES*\n\n"
    keys = list(TRATAMIENTOS.keys())
    for i, key in enumerate(keys, 1):
        t = TRATAMIENTOS[key]
        texto += f"{i}️⃣ {t['nombre']}\n   Duración: {t['duracion_meses']} meses\n   {t['precio']}\n\n"
    texto += "_Escribe el número del tratamiento_"
    return texto

def listar_clientas():
    """Lista todas las clientas."""
    if not clientas:
        return "📋 No hay clientas registradas aún.\n\n" + mensaje_menu()
    
    texto = "📋 *TUS CLIENTAS* (Total: {})\n\n".format(len(clientas))
    for c in clientas[:15]:  # Máximo 15 para no saturar
        texto += f"*{c.get('id')}* - {c.get('nombre')}\n"
        texto += f"   📱 {c.get('telefono')}\n"
        proximo = c.get('proximo_recordatorio') or '—'
        texto += f"   📅 Próximo: {proximo}\n\n"
    
    if len(clientas) > 15:
        texto += f"_...y {len(clientas) - 15} más_\n\n"
    
    texto += "💡 _Escribe el ID para ver detalles_"
    return texto

def ver_clienta(cid):
    """Muestra detalles de una clienta."""
    clienta = next((c for c in clientas if c.get("id") == cid), None)
    if not clienta:
        return f"⚠️ No existe clienta con ID {cid}\n\n" + mensaje_menu()
    
    trat = TRATAMIENTOS.get(clienta.get('tipo_tratamiento'), {})
    
    texto = f"👤 *{clienta.get('nombre')}* (ID: {cid})\n\n"
    texto += f"📱 Teléfono: {clienta.get('telefono')}\n"
    texto += f"💆‍♀️ Tratamiento: {trat.get('nombre', 'No especificado')}\n"
    texto += f"📅 Último tratamiento: {clienta.get('ultimo_tratamiento') or '—'}\n"
    texto += f"🔔 Próximo recordatorio: {clienta.get('proximo_recordatorio') or 'Automático'}\n"
    
    if clienta.get('ultimo_recordatorio_enviado'):
        texto += f"✅ Último envío: {clienta.get('ultimo_recordatorio_enviado')}\n"
    
    texto += f"\n💡 _Usa opción 4 del menú para actualizar_"
    return texto

def guardar_clienta(data):
    """Guarda una nueva clienta en la base de datos."""
    nuevo_id = max((c.get("id", 0) for c in clientas), default=0) + 1
    
    nueva = {
        "id": nuevo_id,
        "nombre": data.get("nombre"),
        "telefono": data.get("telefono"),
        "ultimo_tratamiento": data.get("ultimo_tratamiento"),
        "tipo_tratamiento": data.get("tipo_tratamiento"),
        "tipo_cabello": None,
        "notas": None,
        "proximo_recordatorio": data.get("proximo_recordatorio"),
        "ultimo_recordatorio_enviado": None
    }
    
    clientas.append(nueva)
    guardar_clientas()
    
    trat = TRATAMIENTOS.get(nueva["tipo_tratamiento"], {})
    
    return f"✅ *Clienta agregada exitosamente*\n\n👤 {nueva['nombre']}\n📱 {nueva['telefono']}\n💆‍♀️ {trat.get('nombre')}\nID: {nuevo_id}"