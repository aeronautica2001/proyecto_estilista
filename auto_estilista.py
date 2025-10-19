# =============================================================
# 💇‍♀️ AUTO ESTILISTA - MODO AUTOMÁTICO PARA RENDER
# -------------------------------------------------------------
# Este script ejecuta el sistema de recordatorios de la estilista
# en modo automático (24/7) para que funcione en servidores
# como Render sin necesidad de interacción manual.
# =============================================================

from estilista import verificar_recordatorios_diarios
import schedule
import time

print("💇‍♀️ Modo automático iniciado en Render...")

# Ejecutar la verificación de recordatorios todos los días a las 10:00 a.m.
schedule.every().day.at("10:00").do(verificar_recordatorios_diarios)

# Ejecutar una vez al inicio (útil para pruebas o primer arranque)
print("🔔 Enviando recordatorios iniciales...")
verificar_recordatorios_diarios()

# Bucle principal: mantiene el servicio vivo
while True:
    schedule.run_pending()
    time.sleep(60)  # Espera 1 minuto entre cada chequeo

