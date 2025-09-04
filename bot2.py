from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
import requests
import time

# -------- Configuración --------
INTERVALO_MONITOREO = 60  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/evento/..."  # URL del evento

# -------- Función para revisar el estado del evento --------
def revisar_evento():
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = URL_EVENTO

    try:
        response = requests.get(URL_EVENTO, timeout=10)
        if response.status_code != 200 or response.url != URL_EVENTO:
            mensajes.append("🔒 Página aún no activada")
            estado_boton = "NO DISPONIBLE"
            url_actual = response.url
            return mensajes, estado_boton, url_actual
    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton, url_actual

    soup = BeautifulSoup(response.text, "lxml")

    overlay = soup.select_one(".overlay-content")
    if overlay:
        texto_overlay = overlay.get_text(strip=True)
        if "Evento finalizado" in texto_overlay:
            mensajes.append("❌ El evento sigue cerrado")

    boton = soup.select_one("a.boton_compra")
    if boton:
        texto_boton = boton.get_text(strip=True).upper()
        clases_boton = boton.get("class") or []
        if "AÚN NO DISPONIBLE" in texto_boton or "AUN NO DISPONIBLE" in texto_boton:
            estado_boton = "NO DISPONIBLE"
            mensajes.append("🔒 La compra NO está habilitada")
        elif "btn-success" in clases_boton or "COMPRAR" in texto_boton:
            estado_boton = "COMPRAR"
            mensajes.append("✅ La compra está habilitada")

    if not overlay and not boton:
        mensajes.append("✅ Página del evento activa, pero sin información específica")

    return mensajes, estado_boton, url_actual

# -------- Job de monitoreo --------
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    print("🔍 Analizando la página del evento...")
    mensajes, estado_boton, url_actual = revisar_evento()
    print(f"📊 Estado actual: {estado_boton}, URL: {url_actual}")
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    await context.bot.send_message(chat_id=CHAT_ID, text=texto_final)
    print("✅ Mensaje enviado a Telegram\n")

# -------- Comandos --------
async def start(update, context):
    await update.message.reply_text("Bot iniciado!")

async def comandos(update, context):
    await update.message.reply_text("/start - Inicia el bot\n/comandos - Lista de comandos")

# -------- Main --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))

    app.job_queue.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    print(f"⏱ El bot empezará a monitorear la página cada {INTERVALO_MONITOREO} segundos.")

    app.run_polling()

if __name__ == "__main__":
    main()
