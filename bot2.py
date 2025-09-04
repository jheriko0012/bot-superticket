import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIGURACIÓN ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = 6944124547
URL = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 30  # segundos

ultimo_estado = None
bot = Bot(token=TOKEN)

# ---------------- FUNCIONES ----------------
def obtener_estado():
    try:
        resp = requests.get(URL, timeout=10)
        if resp.status_code != 200:
            return f"❌ No se pudo acceder a la página ({resp.status_code})", False

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Detectar overlay de evento cerrado
        overlay = soup.select_one(".overlay-content")
        if overlay and "Evento finalizado" in overlay.text:
            return "❌ El evento sigue cerrado", False

        # Detectar botón de compra
        boton = soup.select_one("a.boton_compra")
        if boton:
            texto = boton.get_text(strip=True).upper()
            clases = boton.get("class", [])
            if "AÚN NO DISPONIBLE" in texto or "AUN NO DISPONIBLE" in texto:
                return "🔒 La compra NO está habilitada", False
            elif "COMPRAR" in texto or "btn-success" in clases:
                return "✅ La compra está habilitada", True

        # Si la página carga pero no hay overlay ni botón
        if not overlay and not boton:
            return "✅ Página abierta, pero sin información de compra", True

        return "🔒 El evento aún no está habilitado", False

    except Exception as e:
        return f"❌ Error al acceder a la página: {e}", False


async def enviar_estado_si_cambia():
    global ultimo_estado
    while True:
        estado_actual, positivo = obtener_estado()
        mensaje_completo = f"{estado_actual}\n{URL}"
        if estado_actual != ultimo_estado:
            await bot.send_message(chat_id=CHAT_ID, text=mensaje_completo)
            ultimo_estado = estado_actual
        await asyncio.sleep(INTERVALO_MONITOREO)


# ---------------- COMANDOS ----------------
async def comando_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado_actual, positivo = obtener_estado()
    mensaje = f"{estado_actual}\n{URL}"
    await update.message.reply_text(mensaje)


# ---------------- MAIN ----------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("estado", comando_estado))

    # Lanzar monitoreo periódico en paralelo
    asyncio.create_task(enviar_estado_si_cambia())

    # Ejecutar el bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


# ---------------- EJECUCIÓN ----------------
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except RuntimeError:
        # En entornos que ya tienen loop en ejecución
        asyncio.create_task(main())

