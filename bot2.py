from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from bs4 import BeautifulSoup
from flask import Flask
import threading
import requests
import time

# -------- Configuración --------
INTERVALO_MONITOREO = 30  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL_EVENTO = "https://superticket.bo/La-Bicicleta-de-los-Huanca-II"
URL_PRINCIPAL = "https://superticket.bo/"

# Guardar estado previo del botón para no spamear
estado_anterior = None

# -------- Función para revisar el estado del evento --------
def revisar_evento():
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = URL_EVENTO

    try:
        response = requests.get(URL_EVENTO, timeout=10)
        html_crudo = response.text
        url_actual = response.url

        if response.url == URL_PRINCIPAL:
            mensajes.append("🔒 Evento aún no activo")
            return mensajes, estado_boton, url_actual
        elif response.status_code != 200:
            mensajes.append(f"❌ Error al cargar la página, status {response.status_code}")
            return mensajes, estado_boton, url_actual

        soup = BeautifulSoup(html_crudo, "lxml")

        div_boton = soup.find("div", id="div_boton_compra")
        if div_boton:
            a_tag = div_boton.find("a", class_=lambda x: x and "btn-success" in x)
            if a_tag:
                texto_a = a_tag.get_text(strip=True).upper()
                if "COMPRA" in texto_a.split():
                    estado_boton = "COMPRAR"
                    mensajes.append("✅ La compra está habilitada")
                else:
                    mensajes.append(f"🔒 La compra NO está habilitada (texto encontrado: '{texto_a}')")
            else:
                mensajes.append("ℹ️ No se encontró el botón de compra")
        else:
            mensajes.append("ℹ️ Página activa pero sin botón de compra")

    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")

    return mensajes, estado_boton, url_actual

# -------- Job de monitoreo (solo envía mensaje si cambia el estado) --------
def monitor_job_sync(context):
    global estado_anterior
    mensajes, estado_boton, url_actual = revisar_evento()
    if estado_boton != estado_anterior:
        estado_anterior = estado_boton
        texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
        context.bot.send_message(chat_id=CHAT_ID, text=texto_final)

# -------- Comandos del bot --------
def start(update: Update, context):
    update.message.reply_text("🚀 Bot iniciado correctamente!")

def comandos(update: Update, context):
    update.message.reply_text(
        "/start - Inicia el bot\n"
        "/comandos - Lista de comandos\n"
        "/estado - Muestra el estado actual del evento\n"
        "/url - Muestra la URL actual y estado del evento\n"
        "/ayuda - Instrucciones y recomendaciones"
    )

def estado(update: Update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    texto_final = "\n".join(mensajes) + f"\n🌐 URL: {url_actual}"
    update.message.reply_text(texto_final)

def url(update: Update, context):
    mensajes, estado_boton, url_actual = revisar_evento()
    update.message.reply_text(f"🌐 URL actual: {url_actual}\n📊 Estado del evento: {estado_boton}")

def ayuda(update: Update, context):
    update.message.reply_text(
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
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("url", url))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Job de monitoreo
    app.job_queue.run_repeating(monitor_job_sync, interval=INTERVALO_MONITOREO, first=5)

    print(f"🚀 Bot iniciado correctamente. Monitoreando la página cada {INTERVALO_MONITOREO} segundos.")
    app.run_polling()

if __name__ == "__main__":
    main()
