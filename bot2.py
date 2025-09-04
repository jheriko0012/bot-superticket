from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
import requests
import time
import threading
from flask import Flask

# -------- Configuración --------
INTERVALO_MONITOREO = 30  # segundos
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"  # tu token
CHAT_ID = 6944124547  # tu chat id
URL_EVENTO = "https://superticket.bo/Venta-de-Metros-Lineales"  # URL del evento
URL_PRINCIPAL = "https://superticket.bo/"

# -------- Función para revisar el estado del evento --------
def revisar_evento():
    mensajes = []
    estado_boton = "NO DISPONIBLE"
    url_actual = URL_EVENTO

    try:
        response = requests.get(URL_EVENTO, timeout=10)
        # Si nos redirige a la página principal -> evento no activo
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

    # Si llega aquí, la página del evento está activa
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
    await update.message.reply_text("🚀 Bot iniciado y listo para monitorear eventos!")

async def comandos(update, context):
    await update.message.reply_text("/start - Inicia el bot\n/comandos - Lista de comandos")

# -------- Flask para mantener Railway despierto --------
flask_app = Flask(__name__)

@flask_app.route("/")
def ping():
    return "Bot activo", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

# -------- Main --------
def main():
    # Hilo para Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Bot de Telegram
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))
    app.job_queue.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    print(f"⏱ El bot empezará a monitorear la página cada {INTERVALO_MONITOREO} segundos.")
    print("🔍 Analizando la página del evento...")

    app.run_polling()

if __name__ == "__main__":
    main()
