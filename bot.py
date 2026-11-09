"""Bot educativo: Telegram -> busca no Spotify -> links dos resultados."""
import logging
import os
import time
import unicodedata
import re
from html import escape

import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

WELCOME = (
    "🎧 <b>Spotify Finder</b>\n\n"
    "Uma música na cabeça? Vamos encontrar.\n"
    "Descubra músicas, artistas e álbuns no Spotify. 💚\n\n"
    "Escolha o que quer buscar no menu."
)

HELP = (
    "💡 <b>Ajuda</b>\n\n"
    "Escolha música, artista ou álbum no menu e envie o nome.\n"
    "Depois, toque em <b>Abrir no Spotify</b>."
)


async def setup_menu(app):
    try:
        await app.bot.set_my_commands([
            ("start", "🎧 Conheça o Spotify Finder"),
            ("musica", "🎵 Buscar música"),
            ("artista", "🎤 Buscar artista"),
            ("album", "💿 Buscar álbum"),
            ("ajuda", "💡 Ajuda"),
        ])
    except TelegramError:
        logging.warning("Não foi possível atualizar o menu. Os comandos continuam disponíveis.")


def format_result(item, kind):
    icon = {"track": "🎵", "artist": "🎤", "album": "💿"}[kind]
    lines = [f'{icon} <b>{escape(item.get("name", "Sem título"))}</b>']
    if kind != "artist":
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        lines.append("🎤 <b>Artista:</b> " + escape(artists or "Artista não informado"))
    if kind == "track":
        lines.append("💿 <b>Álbum:</b> " + escape(item.get("album", {}).get("name", "Álbum não informado")))
    lines.append("\n<i>Encontrado no Spotify</i>")
    link = item.get("external_urls", {}).get("spotify")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Abrir no Spotify", url=link)]
    ]) if link else None
    return "\n".join(lines), keyboard


def normalize_name(text):
    """Ignora maiúsculas, acentos e pontuação na comparação dos nomes."""
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"\w+", text))


def filter_results(items, query, kind):
    name = normalize_name(query)
    if not name:
        return []
    exact = [item for item in items if normalize_name(item.get("name", "")) == name]
    if exact:
        return exact
    # Permite nomes incompletos, mas exige todas as palavras pesquisadas.
    words = set(name.split())
    if kind == "track":
        # Procura as palavras no conjunto título + artistas + álbum.
        # Assim nenhum dos três campos precisa ser informado separadamente.
        return [item for item in items if words.issubset(set(normalize_name(
            item.get("name", "") + " " + " ".join(
                artist.get("name", "") for artist in item.get("artists", [])
            ) + " " + item.get("album", {}).get("name", "")
        ).split()))]
    return [item for item in items
            if words.issubset(set(normalize_name(item.get("name", "")).split()))]


class Spotify:
    def __init__(self, client_id, secret):
        self.auth = (client_id, secret)
        self.token = None
        self.expires = 0

    async def search(self, query, kind):
        async with httpx.AsyncClient(timeout=15) as client:
            for attempt in range(2):
                if time.monotonic() >= self.expires:
                    response = await client.post(
                        "https://accounts.spotify.com/api/token",
                        auth=self.auth, data={"grant_type": "client_credentials"},
                    )
                    response.raise_for_status()
                    data = response.json()
                    self.token = data["access_token"]
                    self.expires = time.monotonic() + max(0, data["expires_in"] - 60)
                response = await client.get(
                    "https://api.spotify.com/v1/search",
                    headers={"Authorization": f"Bearer {self.token}"},
                    params={"q": query, "type": kind, "market": "BR", "limit": 3},
                )
                if response.status_code == 401 and attempt == 0:
                    self.expires = 0
                    continue
                response.raise_for_status()
                items = response.json().get(kind + "s", {}).get("items", [])
                return filter_results(items, query, kind)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        context.user_data.pop(f"search:{update.effective_chat.id}", None)
        await update.effective_message.reply_text(WELCOME, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await update.effective_message.reply_text(HELP, parse_mode="HTML")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return
    command = message.text.split()[0].split("@")[0][1:]
    key = f"search:{update.effective_chat.id}"
    context.user_data.pop(key, None)
    query = " ".join(context.args).strip()
    if not query:
        context.user_data[key] = command
        prompt = {
            "musica": "🎵 Qual música você quer encontrar?",
            "artista": "🎤 Qual artista você quer encontrar?",
            "album": "💿 Qual álbum você quer encontrar?",
        }[command]
        await message.reply_text(prompt)
        return
    await perform_search(message, context, command, query)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return
    key = f"search:{update.effective_chat.id}"
    command = context.user_data.get(key)
    if not command:
        await help_command(update, context)
        return
    query = message.text.strip()
    if not query or len(query) > 200:
        await message.reply_text("Envie um nome com até 200 caracteres.")
        return
    context.user_data.pop(key, None)
    await perform_search(message, context, command, query)


async def perform_search(message, context, command, query):
    kind = {"musica": "track", "artista": "artist", "album": "album"}[command]
    if len(query) > 200:
        await message.reply_text("Use uma busca com até 200 caracteres.")
        return
    try:
        items = await context.application.bot_data["spotify"].search(query, kind)
    except httpx.HTTPStatusError as error:
        code = error.response.status_code
        if code == 429:
            text = "O Spotify atingiu o limite de consultas. Tente novamente mais tarde."
        elif code in (400, 401, 403):
            text = "O Spotify recusou a consulta. A equipe deve conferir as credenciais e o acesso do aplicativo."
        else:
            text = "O Spotify está indisponível no momento. Tente novamente depois."
        await message.reply_text(text)
        return
    except httpx.RequestError:
        await message.reply_text("Não consegui conectar ao Spotify. Tente novamente depois.")
        return
    if not items:
        await message.reply_text("🔎 Nenhum resultado encontrado. Confira o nome e tente outra busca pelo menu.")
        return
    for item in items:
        text, keyboard = format_result(item, kind)
        await message.reply_text(text, parse_mode="HTML", reply_markup=keyboard,
                                 disable_web_page_preview=True)


async def on_error(update, context):
    # Evita registrar tokens ou URLs contendo credenciais.
    logging.error("Falha ao processar atualização: %s", type(context.error).__name__)


def main():
    load_dotenv()
    keys = ("TELEGRAM_BOT_TOKEN", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET")
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise SystemExit("Preencha o arquivo .env: " + ", ".join(missing))
    logging.basicConfig(level=logging.WARNING)
    app = Application.builder().token(os.environ[keys[0]]).post_init(setup_menu).build()
    app.bot_data["spotify"] = Spotify(os.environ[keys[1]], os.environ[keys[2]])
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ajuda", help_command))
    app.add_handler(CommandHandler(["musica", "artista", "album"], search_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_handler(MessageHandler(filters.COMMAND, help_command))
    app.add_error_handler(on_error)
    print("Bot iniciado. Pressione Ctrl+C para encerrar.")
    app.run_polling()


if __name__ == "__main__":
    main()
