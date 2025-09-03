import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import requests

# ---------------- CONFIGURACIÓN ----------------
TOKEN = "7301448066:AAHQYM4AZlQLWK9cNJWDEgac8OcikvPAvMY"
CHAT_ID = "6944124547"
URL_EVENTO = "https://superticket.bo/Venta-de-Metros-Lineales"
INTERVALO_MONITOREO = 10
ACTUALIZACIONES_PERIODICAS = 15

estado_anterior = {
    "pagina_activa": False,
    "boton_compra": None,
    "ultimo_mensaje": []
}

# ---------------- FUNCIONES ----------------
def log_terminal(msg):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{hora}] {msg}")

def enviar_telegram(mensajes, chat_id=CHAT_ID):
    for msg in mensajes:
        try:
            # Incluye automáticamente la URL del evento en todos los mensajes
            mensaje_completo = f"{msg}\n\n🔗 {URL_EVENTO}"
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": mensaje_completo, "parse_mode": "Markdown"}
            requests.post(url, data=data)
        except Exception as e:
            log_terminal(f"❌ Error enviando Telegram: {e}")

async def revisar_evento(page):
    mensajes = []
    estado_boton = None
    try:
        response = await page.goto(URL_EVENTO, wait_until="domcontentloaded")
        if not response or response.status != 200 or page.url != URL_EVENTO:
            mensajes.append("🔒 Página aún no activada")
            return mensajes, estado_boton
    except Exception as e:
        mensajes.append(f"❌ Error al cargar la página: {e}")
        return mensajes, estado_boton

    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    overlay = soup.select_one(".overlay-content")
    if overlay:
        texto_overlay = overlay.get_text(strip=True)
        if "Evento finalizado" in texto_overlay:
            mensajes.append("❌ El evento sigue cerrado")

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

    if not overlay and not boton:
        mensajes.append("✅ Página del evento activa, pero sin información específica")

    return mensajes, estado_boton

# ---------------- MONITOREO AUTOMÁTICO ----------------
async def monitoreo_automatico(page):
    global estado_anterior
    contador_actualizaciones = 0

    while True:
        try:
            log_terminal("Bot activo: revisando página automáticamente...")
            mensajes, estado_boton = await revisar_evento(page)
            pagina_activa = any("Página del evento activa" in m or "compra" in m for m in mensajes)

            if (pagina_activa != estado_anterior["pagina_activa"] or
                estado_boton != estado_anterior["boton_compra"]):
                log_terminal("---- Cambio detectado ----")
                for msg in mensajes:
                    log_terminal(msg)
                enviar_telegram(mensajes)
                estado_anterior["pagina_activa"] = pagina_activa
                estado_anterior["boton_compra"] = estado_boton
                estado_anterior["ultimo_mensaje"] = mensajes
                contador_actualizaciones = 0
            else:
                contador_actualizaciones += 1
                if contador_actualizaciones >= ACTUALIZACIONES_PERIODICAS:
                    log_terminal("ℹ️ Estado periódico:")
                    for msg in mensajes:
                        log_terminal(msg)
                    enviar_telegram(mensajes)
                    estado_anterior["ultimo_mensaje"] = mensajes
                    contador_actualizaciones = 0

        except Exception as e:
            log_terminal(f"❌ Error en monitoreo automático: {e}")

        await asyncio.sleep(INTERVALO_MONITOREO)

# ---------------- ESCUCHAR COMANDOS ----------------
async def escuchar_comandos(page):
    last_update_id = None
    comandos_disponibles = (
        "/estado - Muestra el estado actual del evento y del botón\n"
        "/ultimo - Muestra el último mensaje enviado automáticamente\n"
        "/comandos - Lista todos los comandos disponibles\n"
        "/ayuda - Explica qué hace el bot"
    )

    while True:
        try:
            url_api = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            if last_update_id:
                url_api += f"?offset={last_update_id + 1}"
            resp = requests.get(url_api, timeout=10).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {}).get("text", "").strip().lower()
                chat_id = update.get("message", {}).get("chat", {}).get("id")

                if not chat_id:
                    continue

                if message == "/estado":
                    mensajes, _ = await revisar_evento(page)
                    mensajes.append("ℹ️ Comando /estado ejecutado correctamente")
                    enviar_telegram(mensajes, chat_id)

                elif message == "/comandos":
                    enviar_telegram([comandos_disponibles], chat_id)

                elif message == "/ultimo":
                    if estado_anterior["ultimo_mensaje"]:
                        enviar_telegram(estado_anterior["ultimo_mensaje"], chat_id)
                    else:
                        enviar_telegram(["No hay mensajes anteriores"], chat_id)

                elif message == "/ayuda":
                    ayuda = (
                        "Este bot monitorea automáticamente la página del evento en Superticket.\n"
                        "Detecta si la página está activa y si el botón de compra está habilitado.\n"
                        "Comandos disponibles:\n" + comandos_disponibles
                    )
                    enviar_telegram([ayuda], chat_id)

        except Exception as e:
            log_terminal(f"❌ Error escuchando comandos: {e}")

        await asyncio.sleep(3)

# ---------------- EJECUTAR ----------------
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        task1 = asyncio.create_task(monitoreo_automatico(page))
        task2 = asyncio.create_task(escuchar_comandos(page))
        await asyncio.gather(task1, task2)

if __name__ == "__main__":
    log_terminal("Bot iniciado correctamente con todos los comandos y URL incluida en los mensajes.")
    asyncio.run(main())
