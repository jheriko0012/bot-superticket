import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
URL = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 60  # en segundos

bot = Bot(token=TOKEN)
chat_id_global = None  # Se llenará cuando un usuario haga /start

# ---------------- FUNCIONES ----------------
def obtener_estado_pagina():
    """Revisa la página y devuelve el estado de la compra."""
    try:
        resp = requests.get(URL, timeout=15)
        if resp.status_code != 200:
            return f"❌ No se pudo acceder a la página. Status: {resp.status_code}"

        soup = BeautifulSoup(resp.text, "html.parser")

        overlay = soup.select_one(".overlay-content")
        if overlay and "Evento finalizado" in overlay.get_text():
            return "❌ El evento sigue cerrado"

        boton = soup.select_one("a.boton_compra")
        if boton:
            texto_boton = boton.get_text().strip().upper()
            clases_boton = boton.get("class", [])
            if "AÚN NO DISPONIBLE" in texto_boton or "AUN NO DISPONIBLE" in texto_boton:
                return f"🔒 La compra NO está habilitada\n{URL}"
            elif "COMPRAR" in texto_boton or "btn-success" in clases_boton:
                return f"✅ La compra está habilitada\n{URL}"

        return f"🔒 El evento aún no está habilitado\n{URL}"

    except Exception as e:
        return f"❌ Error al revisar la página: {e}"

# ---------------- COMANDOS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id_global
    chat_id_global = update.message.chat_id
    await update.message.reply_text(
        "🚀 Bot iniciado y guardado tu chat ID para monitoreo automático.\n"
        "Usa /estado para revisar el estado manualmente o /comandos para ver todos los comandos."
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado_actual = obtener_estado_pagina()
    await update.message.reply_text(estado_actual)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📌 Comandos disponibles:\n"
        "/start - Guardar tu chat para recibir mensajes automáticos\n"
        "/estado - Revisar el estado actual de la página\n"
        "/comandos - Mostrar los comandos disponibles"
    )
    await update.message.reply_text(msg)

# ---------------- MONITOREO PERIÓDICO ----------------
async def monitoreo_periodico():
    while True:
        if chat_id_global is not None:
            estado_actual = obtener_estado_pagina()
            try:
                await bot.send_message(chat_id=chat_id_global, text=estado_actual)
            except Exception as e:
                print(f"❌ Error enviando Telegram: {e}")
        await asyncio.sleep(INTERVALO_MONITOREO)

# ---------------- EJECUTAR ----------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("comandos", comandos))

    # Iniciar monitoreo periódico
    asyncio.create_task(monitoreo_periodico())

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
