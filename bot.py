"""Spotify Finder: funções, dicionários, repetições e requisições HTTP."""
import os
import time
import unicodedata
from html import escape

import requests
from dotenv import load_dotenv

# Reutiliza as conexões, como no exemplo de requests.Session dos slides.
telegram = requests.Session()
spotify = requests.Session()

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
TIPOS = {"musica": "track", "artista": "artist", "album": "album"}
PERGUNTAS = {
    "musica": "🎵 Qual música você quer encontrar?",
    "artista": "🎤 Qual artista você quer encontrar?",
    "album": "💿 Qual álbum você quer encontrar?",
}


def enviar_mensagem(url_telegram, chat_id, texto, botao=None):
    dados = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML",
             "disable_web_page_preview": True}
    if botao:
        dados["reply_markup"] = botao
    inicio = time.monotonic()
    resposta = telegram.post(url_telegram + "/sendMessage", json=dados, timeout=(5, 10))
    resposta.raise_for_status()
    print("Envio ao Telegram:", round(time.monotonic() - inicio, 1), "segundos", flush=True)


def configurar_menu(url_telegram):
    comandos = [
        {"command": "start", "description": "🎧 Conheça o Spotify Finder"},
        {"command": "musica", "description": "🎵 Buscar música"},
        {"command": "artista", "description": "🎤 Buscar artista"},
        {"command": "album", "description": "💿 Buscar álbum"},
        {"command": "ajuda", "description": "💡 Ajuda"},
    ]
    resposta = telegram.post(url_telegram + "/setMyCommands",
                             json={"commands": comandos}, timeout=20)
    resposta.raise_for_status()


def normalizar(texto):
    # Retira os acentos e troca pontuação por espaços para comparar nomes.
    texto = unicodedata.normalize("NFKD", texto.lower())
    resultado = ""
    for letra in texto:
        if not unicodedata.combining(letra):
            if letra.isalnum():
                resultado += letra
            else:
                resultado += " "
    return " ".join(resultado.split())


def filtrar_resultados(itens, pesquisa, tipo):
    pesquisa = normalizar(pesquisa)
    if not pesquisa:
        return []
    exatos = []
    encontrados = []
    for item in itens:
        nome = normalizar(item.get("name", ""))
        if nome == pesquisa:
            exatos.append(item)
        texto = item.get("name", "")
        if tipo == "track":
            for artista in item.get("artists", []):
                texto += " " + artista.get("name", "")
            texto += " " + item.get("album", {}).get("name", "")
        palavras = normalizar(texto).split()
        corresponde = True
        for palavra in pesquisa.split():
            if palavra not in palavras:
                corresponde = False
        if corresponde:
            encontrados.append(item)
    if exatos:
        return exatos
    return encontrados


def buscar_spotify(pesquisa, tipo, acesso):
    inicio = time.monotonic()
    # O Spotify exige um token de aplicativo antes de consultar o catálogo.
    for tentativa in range(2):
        if time.time() >= acesso["expira"]:
            resposta = spotify.post(
                "https://accounts.spotify.com/api/token",
                auth=(os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")),
                data={"grant_type": "client_credentials"}, timeout=(5, 10),
            )
            resposta.raise_for_status()
            dados = resposta.json()
            acesso["token"] = dados["access_token"]
            acesso["expira"] = time.time() + max(0, dados["expires_in"] - 60)
        resposta = spotify.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": "Bearer " + acesso["token"]},
            params={"q": pesquisa, "type": tipo, "market": "BR", "limit": 3},
            timeout=(5, 10),
        )
        if resposta.status_code == 401 and tentativa == 0:
            acesso["expira"] = 0
            continue
        resposta.raise_for_status()
        itens = resposta.json().get(tipo + "s", {}).get("items", [])
        print("Consulta ao Spotify:", round(time.monotonic() - inicio, 1), "segundos", flush=True)
        return filtrar_resultados(itens, pesquisa, tipo)


def montar_resultado(item, tipo):
    icones = {"track": "🎵", "artist": "🎤", "album": "💿"}
    texto = icones[tipo] + " <b>" + escape(item.get("name", "Sem título")) + "</b>"
    if tipo != "artist":
        artistas = []
        for artista in item.get("artists", []):
            artistas.append(artista.get("name", ""))
        nomes = ", ".join(artistas) or "Artista não informado"
        texto += "\n🎤 <b>Artista:</b> " + escape(nomes)
    if tipo == "track":
        album = item.get("album", {}).get("name", "Álbum não informado")
        texto += "\n💿 <b>Álbum:</b> " + escape(album)
    texto += "\n\n<i>Encontrado no Spotify</i>"
    link = item.get("external_urls", {}).get("spotify")
    botao = None
    if link:
        botao = {"inline_keyboard": [[{"text": "🎧 Abrir no Spotify", "url": link}]]}
    return texto, botao


def pesquisar_e_responder(url_telegram, chat_id, comando, pesquisa, acesso):
    if len(pesquisa) > 200:
        enviar_mensagem(url_telegram, chat_id, "Use uma busca com até 200 caracteres.")
        return
    try:
        itens = buscar_spotify(pesquisa, TIPOS[comando], acesso)
    except requests.HTTPError as erro:
        codigo = erro.response.status_code
        if codigo == 429:
            texto = "O Spotify atingiu o limite de consultas. Tente novamente mais tarde."
        elif codigo in (400, 401, 403):
            texto = "O Spotify recusou a consulta. A equipe deve conferir as credenciais e o acesso do aplicativo."
        else:
            texto = "O Spotify está indisponível no momento. Tente novamente depois."
        enviar_mensagem(url_telegram, chat_id, texto)
        return
    except (requests.RequestException, ValueError):
        enviar_mensagem(url_telegram, chat_id, "Não consegui conectar ao Spotify. Tente novamente depois.")
        return
    if not itens:
        enviar_mensagem(url_telegram, chat_id,
                        "🔎 Nenhum resultado encontrado. Confira o nome e tente outra busca pelo menu.")
    for item in itens:
        texto, botao = montar_resultado(item, TIPOS[comando])
        enviar_mensagem(url_telegram, chat_id, texto, botao)


def tratar_mensagem(mensagem, url_telegram, buscas, acesso):
    texto = mensagem.get("text", "").strip()
    if not texto or "from" not in mensagem:
        return
    chat_id = mensagem["chat"]["id"]
    # Cada pessoa tem sua própria escolha de busca, inclusive em grupos.
    chave = (chat_id, mensagem["from"]["id"])
    if texto.startswith("/"):
        partes = texto.split(maxsplit=1)
        comando = partes[0].split("@")[0][1:]
        if comando == "start":
            buscas.pop(chave, None)
            enviar_mensagem(url_telegram, chat_id, WELCOME)
        elif comando in TIPOS:
            buscas.pop(chave, None)
            if len(partes) == 1:
                buscas[chave] = comando
                enviar_mensagem(url_telegram, chat_id, PERGUNTAS[comando])
            else:
                pesquisar_e_responder(url_telegram, chat_id, comando, partes[1], acesso)
        else:
            enviar_mensagem(url_telegram, chat_id, HELP)
    elif chave in buscas:
        if len(texto) > 200:
            enviar_mensagem(url_telegram, chat_id, "Envie um nome com até 200 caracteres.")
            return
        comando = buscas.pop(chave)
        pesquisar_e_responder(url_telegram, chat_id, comando, texto, acesso)
    else:
        enviar_mensagem(url_telegram, chat_id, HELP)


def main():
    load_dotenv()
    for campo in ("TELEGRAM_BOT_TOKEN", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"):
        if not os.getenv(campo):
            print("Preencha o arquivo .env: " + campo)
            return
    url_telegram = "https://api.telegram.org/bot" + os.getenv("TELEGRAM_BOT_TOKEN")
    buscas = {}
    acesso = {"token": "", "expira": 0}
    offset = 0
    try:
        configurar_menu(url_telegram)
    except requests.RequestException:
        print("Não foi possível atualizar o menu. Os comandos continuam disponíveis.")
    print("Bot iniciado. Pressione Ctrl+C para encerrar.")
    while True:
        try:
            resposta = telegram.get(
                url_telegram + "/getUpdates",
                params={"offset": offset, "timeout": 25, "allowed_updates": '["message"]'},
                timeout=(5, 35),
            )
            resposta.raise_for_status()
            dados = resposta.json()
            for atualizacao in dados["result"]:
                # O próximo pedido não deve receber novamente esta mensagem.
                offset = atualizacao["update_id"] + 1
                mensagem = atualizacao.get("message")
                if mensagem:
                    print("Mensagem recebida; preparando resposta.", flush=True)
                    tratar_mensagem(mensagem, url_telegram, buscas, acesso)
        except KeyboardInterrupt:
            print("Bot encerrado.")
            break
        except requests.HTTPError as erro:
            codigo = erro.response.status_code
            print("Falha na comunicação com o Telegram. Código:", codigo)
            if codigo in (401, 409):
                print("Confira o token e mantenha apenas uma execução deste bot aberta.")
                break
            time.sleep(3)
        except (requests.RequestException, ValueError, KeyError):
            # Não imprime a URL da requisição, pois ela contém o token secreto.
            print("Falha ao processar uma mensagem. Tentando novamente...")
            time.sleep(3)


if __name__ == "__main__":
    main()
