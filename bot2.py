import requests
from bs4 import BeautifulSoup
import time
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 60  # en segundos

bot = Bot(token=TOKEN)

# ---------------- FUNCIONES ----------------
def obtener_estado_pagina():
    """Revisa la página y devuelve el estado de la compra."""
    try:
        resp = requests.get(URL, timeout=15)
        if resp.status_code != 200:
            return f"❌ No se pudo acceder a la página. Status: {resp.status_code}"

        soup = BeautifulSoup(resp.text, "html.parser")

        # Verificar overlay de evento cerrado
        overlay = soup.select_one(".overlay-content")
        if overlay and "Evento finalizado" in overlay.get_text():
            return "❌ El evento sigue cerrado"

        # Verificar botón de compra
        boton = soup.select_one("a.boton_compra")
        if boton:
            texto_boton = boton.get_text().strip().upper()
            clases_boton = boton.get("class", [])
            if "AÚN NO DISPONIBLE" in texto_boton or "AUN NO DISPONIBLE" in texto_boton:
                return f"🔒 La compra NO está habilitada\n{URL}"
            elif "COMPRAR" in texto_boton or "btn-success" in clases_boton:
                return f"✅ La compra está habilitada\n{URL}"

        # Si no se encuentra nada
        return f"🔒 El evento aún no está habilitado\n{URL}"

    except Exception as e:
        return f"❌ Error al revisar la página: {e}"

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado_actual = obtener_estado_pagina()
    await update.message.reply_text(estado_actual)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📌 Comandos disponibles:\n"
        "/estado - Revisar el estado actual de la página\n"
        "/comandos - Mostrar los comandos disponibles"
    )
    await update.message.reply_text(msg)

# ---------------- MONITOREO PERIÓDICO ----------------
def monitoreo_periodico():
    while True:
        estado_actual = obtener_estado_pagina()
        try:
            bot.send_message(chat_id=CHAT_ID, text=estado_actual)
        except Exception as e:
            print(f"Error enviando Telegram: {e}")
        time.sleep(INTERVALO_MONITOREO)

# ---------------- EJECUTAR ----------------
if __name__ == "__main__":
    import threading

    # Ejecutar monitoreo en un hilo separado
    t = threading.Thread(target=monitoreo_periodico, daemon=True)
    t.start()

    # Ejecutar bot con comandos
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("comandos", comandos))

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    app.run_polling()
