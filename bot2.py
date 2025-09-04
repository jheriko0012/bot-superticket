from telegram.ext import Updater, CommandHandler, Job
from bs4 import BeautifulSoup
import requests
from flask import Flask
import threading
import time

# -------- Configuración --------
INTERVALO_MONITOREO = 30  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/La-Bicicleta-de-los-Huanca-II"

# -------- Función para revisar el estado del evento --------
def revisar_evento(url_evento=URL_EVENTO):
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = url_evento

    try:
        response = requests.get(url_evento, timeout=10)
        html_crudo = response.text
        url_actual = response.url

        if response.status_code != 200:
            mensajes.append(f"❌ Error al cargar la página, status {response.status_code}")
            return mensajes, estado_boton, url_actual

    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton, url_actual

    soup = BeautifulSoup(html_crudo, "lxml")

    # Buscar el div del botón de compra
    div_boton = soup.find("div", id="div_boton_compra")
    if div_boton:
        a_tag = div_boton.find("a")
        if a_tag:
            texto_a = a_tag.get_text(strip=True).upper()
            if "COMPRA" in texto_a:
                estado_boton = "COMPRAR"
                mensajes.append("✅ La compra está habilitada")
            else:
                mensajes.append(f"🔒 La compra NO está habilitada (texto encontrado: '{texto_a}')")
        else:
            mensajes.append("ℹ️ No se encontró etiqueta <a> dentro del div")
    else:
        mensajes.append("ℹ️ Página activa pero sin botón de compra")

    return mensajes, estado_boton, url_actual

# -------- Funciones de comandos de Telegram --------
def start(update, context):
    update.message.reply_text("🚀 Bot iniciado correctamente!")

def comandos(update, context):
    update.message.reply_text(
        "/start - Inicia el bot\n"
        "/comandos - Lista de comandos\n"
        "/estado - Muestra el estado actual del evento\n"
        "/url - Muestra la URL actual y estado del evento\n"
        "/ayuda - Instrucciones y recomendaciones"
    )

def estado(update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    update.message.reply_text(texto_final)

def url(update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    update.message.reply_text(f"🌐 URL actual: {url_actual}\n📊 Estado del evento: {estado_boton}")

def ayuda(update, context):
    update.message.reply_text(
        "💡 Usa los comandos para interactuar con el bot:\n"
        "/start - Inicia el bot\n"
        "/estado - Consulta el estado actual del evento\n"
        "/url - Ver la URL y el estado del evento\n"
        "/comandos - Lista todos los comandos\n"
        "/ayuda - Mostrar esta ayuda"
    )

# -------- Job de monitoreo periódico --------
def monitor_job(context):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    context.bot.send_message(chat_id=CHAT_ID, text=texto_final)

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
    threading.Thread(target=run_flask).start()

    # Iniciar bot de Telegram
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Agregar handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("comandos", comandos))
    dp.add_handler(CommandHandler("estado", estado))
    dp.add_handler(CommandHandler("url", url))
    dp.add_handler(CommandHandler("ayuda", ayuda))

    # Job que revisa el evento cada INTERVALO_MONITOREO segundos
    jq = updater.job_queue
    jq.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    print(f"🚀 Bot iniciado correctamente. Monitoreando la página cada {INTERVALO_MONITOREO} segundos.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
