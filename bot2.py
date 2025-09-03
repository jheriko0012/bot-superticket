import asyncio
from playwright.async_api import async_playwright
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import os

# ================= CONFIGURACIÓN =================
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL = "https://superticket.bo/Venta-de-Metros-Lineales"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ================= FUNCIONES =================

async def revisar_pagina():
    async with async_playwright() as p:
        logging.info("Lanzando navegador...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-zygote",
                "--disable-gpu"
            ]
        )
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        logging.info(f"Abriendo página: {URL}")
        await page.goto(URL, wait_until="load", timeout=60000)

        contenido = await page.content()

        if "btn-comprar" in contenido or "Comprar" in contenido:
            mensaje = f"✅ Página habilitada para comprar.\n🔗 {URL}"
        else:
            mensaje = f"⚠️ Página aún no habilitada.\n🔗 {URL}"

        logging.info(f"Resultado: {mensaje}")
        await browser.close()
        return mensaje

async def enviar_mensaje(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        logging.info("Mensaje enviado a Telegram correctamente.")
    else:
        logging.error(f"Error enviando mensaje: {r.text}")

# ================= COMANDOS DE TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola! Usa /status para verificar la página en tiempo real.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Revisando página...")
    mensaje = await revisar_pagina()
    await update.message.reply_text(mensaje)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Comandos disponibles:\n/start - Inicia el bot\n/status - Revisa el estado de la página\n/comandos - Lista de comandos disponibles")

# ================= MAIN LOOP =================

async def heartbeat():
    while True:
        logging.info("✅ Bot sigue corriendo y monitoreando la página...")
        await asyncio.sleep(120)  # cada 2 minutos

async def main():
    logging.info("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")

    # lanza heartbeat
    asyncio.create_task(heartbeat())

    # crea bot
    application = ApplicationBuilder().token(TOKEN).build()

    # añade comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("comandos", comandos))

    # loop infinito para revisión automática cada 5 min
    async def ciclo_revision():
        while True:
            try:
                mensaje = await revisar_pagina()
                await enviar_mensaje(mensaje)
            except Exception as e:
                logging.error(f"Error en ciclo de revisión: {e}")
            await asyncio.sleep(300)  # cada 5 minutos

    asyncio.create_task(ciclo_revision())
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
