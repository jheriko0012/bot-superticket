import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ---------------- CONFIG ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 60  # segundos
TIMEOUT_PAGINA = 15000     # 15 segundos
estado_anterior = ""

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

# ---------------- FUNCIONES ----------------
async def revisar_pagina(page):
    """Revisa la página y retorna mensaje y estado positivo/negativo"""
    try:
        await page.goto(URL, timeout=TIMEOUT_PAGINA)
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

        return f"✅ Puesto entrada, página abierta\n{URL}", True

    except PlaywrightTimeoutError:
        return "⚠️ La página tardó demasiado en cargar", False
    except Exception as e:
        return f"❌ Error al revisar la página: {e}", False

async def send_message(context: ContextTypes.DEFAULT_TYPE, mensaje: str):
    """Envía mensaje a Telegram"""
    try:
        await context.bot.send_message(chat_id=CHAT_ID, text=mensaje)
        logging.info(f"📩 Mensaje enviado: {mensaje}")
    except Exception as e:
        logging.error(f"❌ Error al enviar mensaje: {e}")

# ---------------- JOB DE MONITOREO ----------------
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que revisa la página y envía mensaje si hay cambio"""
    global estado_anterior

    # Creamos Playwright dentro del job
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        mensaje, _ = await revisar_pagina(page)

        if mensaje != estado_anterior:
            await send_message(context, f"⚠️ Cambio detectado:\n{mensaje}")
            estado_anterior = mensaje
        await browser.close()

# ---------------- COMANDOS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot de monitoreo en ejecución.\nUsa /estado para ver el estado actual."
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global estado_anterior
    msg = estado_anterior if estado_anterior else "ℹ️ Aún no se ha verificado la página."
    await update.message.reply_text(msg)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = (
        "/start - Inicia el bot\n"
        "/estado - Muestra el estado actual de la página\n"
        "/ayuda - Lista de comandos"
    )
    await update.message.reply_text(comandos)

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    # Agregamos comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Configuramos JobQueue para monitoreo
    app.job_queue.run_repeating(monitor_job, interval=INTERVALO_MONITOREO, first=5)

    logging.info("🚀 Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    app.run_polling()

if __name__ == "__main__":
    main()


