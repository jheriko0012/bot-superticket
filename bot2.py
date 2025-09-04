import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from bs4 import BeautifulSoup
import requests
from flask import Flask

TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/La-Bicicleta-de-los-Huanca-II"
INTERVALO_MONITOREO = 30  # segundos

# ---- Flask para mantener vivo ----
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot activo ✅"

def run_flask():
    app_flask.run(host="0.0.0.0", port=5000)

# ---- Función de revisión ----
def revisar_evento(url_evento=URL_EVENTO):
    estado_boton = "NO DISPONIBLE"
    mensajes = []

    try:
        r = requests.get(url_evento, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        div_boton = soup.find("div", id="div_boton_compra")
        if div_boton and div_boton.find("a"):
            texto = div_boton.find("a").get_text(strip=True).upper()
            if "COMPRA" in texto:
                estado_boton = "COMPRAR"
                mensajes.append("✅ La compra está habilitada")
            else:
                mensajes.append(f"🔒 Botón encontrado pero texto: {texto}")
        else:
            mensajes.append("ℹ️ Botón de compra no encontrado")
    except Exception as e:
        mensajes.append(f"❌ Error: {e}")

    return estado_boton, "\n".join(mensajes)

# ---- Comandos de Telegram ----
async def start(update, context):
    await update.message.reply_text("🚀 Bot iniciado correctamente!")

async def estado(update, context):
    estado_boton, mensajes = revisar_evento()
    await update.message.reply_text(f"{mensajes}\nEstado: {estado_boton}")

# ---- Monitoreo periódico ----
async def monitor(bot):
    estado_prev = None
    while True:
        estado_actual, mensajes = revisar_evento()
        if estado_actual != estado_prev:
            await bot.send_message(chat_id=CHAT_ID, text=f"{mensajes}\nEstado: {estado_actual}")
            estado_prev = estado_actual
        await asyncio.sleep(INTERVALO_MONITOREO)

# ---- Main ----
async def main():
    # Flask en otro thread
    import threading
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))

    # Iniciar polling
    await app.initialize()
    await app.start()
    print("🚀 Bot iniciado y polling activo")

    # Monitoreo
    asyncio.create_task(monitor(app.bot))

    # Mantener vivo
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())

