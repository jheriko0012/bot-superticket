import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ---------------- CONFIG ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 60  # en segundos
TIMEOUT_PAGINA = 15000     # 15 segundos
estado_anterior = ""

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

# ---------------- FUNCIONES ----------------
async def send_message(app: Application, text: str):
    """Envía mensaje a Telegram"""
    try:
        await app.bot.send_message(chat_id=CHAT_ID, text=text)
        logging.info(f"📩 Mensaje enviado: {text}")
    except Exception as e:
        logging.error(f"❌ Error al enviar mensaje: {e}")

async def revisar_pagina(page):
    """Revisa el estado de la página y retorna mensaje y estado positivo/negativo"""
    try:
        await page.goto(URL, timeout=TIMEOUT_PAGINA)
        html = await page.content()

        # Lógica para detectar el estado
        boton = await page.query_selector("a.boton_compra")
        overlay = await page.query_selector(".overlay-content")

        if overlay:
            texto_overlay = await overlay.inner_text()
            if "Evento finalizado" in texto_overlay:
                return "❌ El evento sigue cerrado", False

        if boton:
            texto_boton = (await boton.inner_text()).strip().upper()
            clases_boton = await boton.get_attribute("class") or ""
            if "AÚN NO DISPONIBLE" in texto_boton or "AUN NO DISPONIBLE" in texto_boton:
                return "🔒 La compra NO está habilitada", False
            elif "COMPRAR" in texto_boton or "btn-success" in clases_boton:
                return f"✅ La compra está habilitada\n{URL}", True

        # Si la página cargó pero no hay overlay ni botón
        return f"✅ Puesto entrada, página abierta\n{URL}", True

    except PlaywrightTimeoutError:
        return "⚠️ La página tardó demasiado en cargar", False
    except Exception as e:
        return f"❌ Error al revisar la página: {e}", False

# ---------------- MONITOREO ----------------
async def main_task(app: Application):
    global estado_anterior
    logging.info("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while True:
            logging.info("🔎 Bot sigue corriendo y monitoreando la página...")
            mensaje, positivo = await revisar_pagina(page)

            if mensaje != estado_anterior:
                await send_message(app, f"⚠️ Cambio detectado:\n{mensaje}")
                estado_anterior = mensaje

            await asyncio.sleep(INTERVALO_MONITOREO)

# ---------------- COMANDOS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de monitoreo en ejecución.\nUsa /estado para ver el estado actual.")

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global estado_anterior
    msg = estado_anterior if estado_anterior else "ℹ️ Aún no se ha verificado la página."
    await update.message.reply_text(msg)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = "/start - Inicia el bot\n/estado - Muestra el estado actual de la página\n/ayuda - Lista de comandos"
    await update.message.reply_text(comandos)

# ---------------- MAIN ----------------
async def main():
    app = Application.builder().token(TOKEN).build()

    # Agregamos comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("ayuda", ayuda))

    async with app:
        # Ejecuta bot y monitoreo en paralelo
        await asyncio.gather(
            app.start(),
            main_task(app)
        )

if __name__ == "__main__":
    asyncio.run(main())
