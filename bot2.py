import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

# ---------------- CONFIG ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"  # Lo puedes dejar así, se obtiene automáticamente del chat
URL_EVENTO = "https://superticket.bo/Venta-de-Metros-Lineales"
URL_PRINCIPAL = "https://superticket.bo"
INTERVALO_MONITOREO = 30  # segundos

bot = Bot(token=TOKEN)

# ---------------- FUNCIONES ----------------
def revisar_evento():
    mensajes = []
    estado_boton = "DESCONOCIDO"

    try:
        response = requests.get(URL_EVENTO, allow_redirects=True, timeout=15)
        final_url = response.url

        if final_url == URL_PRINCIPAL:
            mensajes.append("🔒 Evento aún no activo")
            estado_boton = "NO DISPONIBLE"
            return mensajes, estado_boton, final_url

    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton, URL_EVENTO

    # Si sigue en la URL del evento
    html = response.text
    soup = BeautifulSoup(html, "lxml")

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
    else:
        mensajes.append("✅ Página del evento activa, pero sin información específica")
        estado_boton = "DESCONOCIDO"

    return mensajes, estado_boton, final_url

# ---------------- JOB ----------------
def monitor_job():
    print("🔍 Analizando la página del evento...")
    mensajes, estado_boton, url_actual = revisar_evento()
    estado_actual = f"📊 Estado actual: {estado_boton}, URL: {url_actual}"

    for mensaje in mensajes:
        print(mensaje)

    print(estado_actual)
    try:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(mensajes) + f"\n{estado_actual}")
        print("✅ Mensaje enviado a Telegram")
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")

# ---------------- COMANDOS ----------------
async def start(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.\n"
             f"⏱ El bot empezará a monitorear la página cada {INTERVALO_MONITOREO} segundos."
    )

# ---------------- MAIN ----------------
async def main():
    print("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    while True:
        monitor_job()
        time.sleep(INTERVALO_MONITOREO)

# ---------------- RUN ----------------
import asyncio
asyncio.run(main())
