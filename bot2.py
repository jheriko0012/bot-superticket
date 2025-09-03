import asyncio
import logging
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
TOKEN = "TU_TOKEN_DE_TELEGRAM"
CHAT_ID = "TU_CHAT_ID"

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)

# ---------------- FUNCIONES DEL BOT ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot funcionando y monitoreando la página...")

async def main_task():
    logging.info("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        logging.info("✅ Bot sigue corriendo y monitoreando la página...")
        # Aquí va tu lógica de monitoreo
        await page.goto("https://superticket.bo/Venta-de-Metros-Lineales")
        await asyncio.sleep(10)  # Simula espera
        logging.info("✅ Página cargada, verificando datos...")

        await browser.close()

async def run_telegram_bot():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # Usamos start() en vez de asyncio.run() para evitar el error
    await application.start()
    await application.updater.start_polling()
    logging.info("🤖 Bot de Telegram escuchando comandos...")

    # Mantener corriendo el bot
    while True:
        await asyncio.sleep(3600)

async def main():
    # Ejecutamos las dos tareas en paralelo sin reiniciar el loop
    await asyncio.gather(
        main_task(),
        run_telegram_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            logging.warning("⚠️ Event loop ya estaba corriendo, iniciando con alternativa...")
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise

