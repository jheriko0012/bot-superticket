import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

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

        overlay = soup.select_one(".overlay-content")
        if overlay and "Evento finalizado" in overlay.text:
            return "❌ El evento sigue cerrado", False

        boton = soup.select_one("a.boton_compra")
        if boton:
            texto = boton.get_text(strip=True).upper()
            clases = boton.get("class", [])
            if "AÚN NO DISPONIBLE" in texto or "AUN NO DISPONIBLE" in texto:
                return "🔒 La compra NO está habilitada", False
            elif "COMPRAR" in texto or "btn-success" in clases:
                return "✅ La compra está habilitada", True

        if not overlay and not boton:
            return "✅ Página abierta, pero sin información de compra", True

        return "🔒 El evento aún no está habilitado", False

    except Exception as e:
        return f"❌ Error al acceder a la página: {e}", False


def monitorar():
    global ultimo_estado
    while True:
        estado_actual, positivo = obtener_estado()
        mensaje_completo = f"{estado_actual}\n{URL}"
        if estado_actual != ultimo_estado:
            bot.send_message(chat_id=CHAT_ID, text=mensaje_completo)
            ultimo_estado = estado_actual
        time.sleep(INTERVALO_MONITOREO)


# ---------------- COMANDOS ----------------
def comando_estado(update, context):
    estado_actual, positivo = obtener_estado()
    mensaje = f"{estado_actual}\n{URL}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)


# ---------------- MAIN ----------------
def main():
    # Crear aplicación de telegram
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("estado", comando_estado))

    # Inicia el bot en modo polling
    app.run_polling(poll_interval=5, timeout=10, drop_pending_updates=True)

    # Inicia el monitoreo continuo
    monitorar()


if __name__ == "__main__":
    main()

