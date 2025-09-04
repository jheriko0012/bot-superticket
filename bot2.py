from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
import requests

# -------- Configuración --------
INTERVALO_MONITOREO = 30  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/Venta-de-Metros-Lineales"
URL_PRINCIPAL = "https://superticket.bo/"

# -------- Función para revisar el estado del evento --------
def revisar_evento():
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = URL_EVENTO

    try:
        response = requests.get(URL_EVENTO, timeout=10)
        if response.url == URL_PRINCIPAL:
            mensajes.append("🔒 Evento aún no activo")
            estado_boton = "NO DISPONIBLE"
            url_actual = response.url
            return mensajes, estado_boton, url_actual
        elif response.status_code != 200:
            mensajes.append(f"❌ Error al cargar la página, status {response.status_code}")
            estado_boton = "NO DISPONIBLE"
            url_actual = response.url
            return mensajes, estado_boton, url_actual
    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton, url_actual

    # Página del evento activa
    mensajes.append("✅ Evento habilitado")
    url_actual = response.url

    soup = BeautifulSoup(response.text, "lxml")
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

    if not boton:
        mensajes.append("ℹ️ Página del evento activa, pero sin botón de compra")

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
    await update.message.reply_text("🚀 Bot iniciado correctamente!")

async def comandos(update, context):
    await update.message.reply_text(
        "/start - Inicia el bot\n"
        "/comandos - Lista de comandos\n"
        "/estado - Muestra el estado actual del evento\n"
        "/url - Muestra la URL actual y estado del evento\n"
        "/ayuda - Instrucciones y recomendaciones"
    )

async def estado(update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    await update.message.reply_text(texto_final)

async def url(update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    await update.message.reply_text(f"🌐 URL actual: {url_actual}\n📊 Estado del evento: {estado_boton}")

async def ayuda(update, context):
    await update.message.reply_text(
        "💡 Usa los comandos para interactuar con el bot:\n"
        "/start - Inicia el bot\n"
        "/estado - Consulta el estado actual del evento\n"
        "/url - Ver la URL y el estado del evento\n"
        "/comandos - Lista todos los comandos\n"
        "/ayuda - Mostrar esta ayuda"
    )

# -------- Main --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("url", url))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Job que revisa el evento cada INTERVALO_MONITOREO segundos
    app.job_queue.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    print(f"⏱ El bot empezará a monitorear la página cada {INTERVALO_MONITOREO} segundos.")

    app.run_polling()

if __name__ == "__main__":
    main()



