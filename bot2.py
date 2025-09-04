from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from bs4 import BeautifulSoup
import requests
from flask import Flask
import threading

# -------- Configuración --------
INTERVALO_MONITOREO = 30  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/La-Bicicleta-de-los-Huanca-II"
URL_PRINCIPAL = "https://superticket.bo/"

# -------- Función para revisar el estado del evento --------
def revisar_evento():
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = URL_EVENTO

    try:
        response = requests.get(URL_EVENTO, timeout=10)
        html_crudo = response.text

        if response.url == URL_PRINCIPAL:
            mensajes.append("🔒 Evento aún no activo")
            return mensajes, estado_boton, response.url
        elif response.status_code != 200:
            mensajes.append(f"❌ Error al cargar la página, status {response.status_code}")
            return mensajes, estado_boton, response.url

    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton, url_actual

    mensajes.append("✅ Evento habilitado")
    url_actual = response.url
    soup = BeautifulSoup(html_crudo, "lxml")

    # Buscamos el div del botón de compra
    div_boton = soup.find("div", id="div_boton_compra")
    if div_boton:
        # Buscar el <a> con clase btn-success
        a_tag = div_boton.find("a", class_="btn-success")
        if a_tag:
            texto_a = a_tag.get_text(strip=True).upper()
            if "COMPRA" in texto_a.split():
                estado_boton = "COMPRAR"
                mensajes.append("✅ La compra está habilitada")
            else:
                estado_boton = "NO DISPONIBLE"
                mensajes.append(f"🔒 La compra NO está habilitada (texto encontrado: '{texto_a}')")
        else:
            estado_boton = "NO DISPONIBLE"
            mensajes.append("ℹ️ No se encontró el botón de compra")
    else:
        estado_boton = "NO DISPONIBLE"
        mensajes.append("ℹ️ Página activa pero sin botón de compra")

    return mensajes, estado_boton, url_actual


# -------- Job de monitoreo --------
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    await context.bot.send_message(chat_id=CHAT_ID, text=texto_final)


# -------- Comandos --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot iniciado correctamente!")

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Inicia el bot\n"
        "/comandos - Lista de comandos\n"
        "/estado - Muestra el estado actual del evento\n"
        "/url - Muestra la URL actual y estado del evento\n"
        "/ayuda - Instrucciones y recomendaciones"
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    await update.message.reply_text(texto_final)

async def url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensajes, estado_boton, url_actual = revisar_evento()
    await update.message.reply_text(f"🌐 URL actual: {url_actual}\n📊 Estado del evento: {estado_boton}")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Usa los comandos para interactuar con el bot:\n"
        "/start - Inicia el bot\n"
        "/estado - Consulta el estado actual del evento\n"
        "/url - Ver la URL y el estado del evento\n"
        "/comandos - Lista todos los comandos\n"
        "/ayuda - Mostrar esta ayuda"
    )


# -------- Flask para mantener el bot activo 24/7 --------
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot activo ✅"

def run_flask():
    app_flask.run(host="0.0.0.0", port=5000)


# -------- Main --------
def main():
    # Ejecutar Flask en un hilo separado
    threading.Thread(target=run_flask, daemon=True).start()

    # Iniciar bot de Telegram
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

