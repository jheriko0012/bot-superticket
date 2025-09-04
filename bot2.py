import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# ---------------- CONFIG ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL_EVENTO = "https://superticket.bo/evento/tu-evento"  # Cambia por tu evento real
INTERVALO_MONITOREO = 60  # en segundos

bot = Bot(token=TOKEN)

# ---------------- FUNCIONES ----------------
def revisar_evento():
    mensajes = []
    try:
        respuesta = requests.get(URL_EVENTO, timeout=10, allow_redirects=True)
        # Si nos redirige a la página principal
        if respuesta.url.rstrip("/") == "https://superticket.bo":
            mensajes.append("🔒 Evento aún no activo")
            estado_boton = "NO DISPONIBLE"
            return mensajes, estado_boton, respuesta.url
    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        estado_boton = "NO DISPONIBLE"
        return mensajes, estado_boton, URL_EVENTO

    # Si entramos al evento
    soup = BeautifulSoup(respuesta.text, "lxml")

    overlay = soup.select_one(".overlay-content")
    if overlay:
        texto_overlay = overlay.get_text(strip=True)
        if "Evento finalizado" in texto_overlay:
            mensajes.append("❌ El evento sigue cerrado")

    boton = soup.select_one("a.boton_compra")
    if boton:
        texto_boton = boton.get_text(strip=True).upper()
        clases_boton = boton.get("class") or []

        if "COMPRAR" in texto_boton or "btn-success" in clases_boton:
            estado_boton = "COMPRAR"
            mensajes.append("✅ La compra está habilitada")
        else:
            estado_boton = "NO DISPONIBLE"
            mensajes.append("🔒 La compra NO está habilitada")
    else:
        estado_boton = "NO DISPONIBLE"
        mensajes.append("🔒 Botón no encontrado")

    mensajes.insert(0, "✅ Evento habilitado")
    return mensajes, estado_boton, respuesta.url

# ---------------- JOB ----------------
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    await bot.send_message(chat_id=CHAT_ID, text=texto_final)

# ---------------- COMANDOS ----------------
async def start(update, context):
    await update.message.reply_text("Bot iniciado y monitoreando el evento.")

async def comandos(update, context):
    cmds = "/start - Inicia el bot\n/comandos - Muestra comandos disponibles"
    await update.message.reply_text(cmds)

# ---------------- MAIN ----------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))

    # Job de monitoreo
    app.job_queue.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    await app.run_polling()

# ---------------- RUN ----------------
if __name__ == "__main__":
    asyncio.run(main())

