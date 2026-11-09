# Spotify Finder

Bot em Python para pesquisar músicas, artistas e álbuns no Telegram usando a API do Spotify.

**Bot:** [@finder_musical_unasp_bot](https://t.me/finder_musical_unasp_bot)

## Funcionalidades

- Busca de músicas pelo título, com artista e/ou álbum opcionais.
- Busca de artistas e álbuns pelo nome.
- Menu para escolher a busca e enviar o nome na mensagem seguinte.
- Resultados com informações e botão para abrir no Spotify.

| Comando | Função |
| --- | --- |
| `/start` | Apresentação |
| `/musica` | Buscar música |
| `/artista` | Buscar artista |
| `/album` | Buscar álbum |
| `/ajuda` | Instruções de uso |

Também é possível pesquisar diretamente: `/musica Yellow Coldplay`.

## Funcionamento

O programa consulta as mensagens do Telegram com `getUpdates`, identifica o comando e pesquisa no endpoint `/v1/search` do Spotify. Os resultados são filtrados e enviados por `sendMessage`.

A autenticação do Spotify usa Client Credentials. O token é reutilizado até próximo de expirar. Um dicionário guarda a opção de busca de cada usuário, e o identificador das atualizações evita processar repetidamente a mesma mensagem durante a execução.

## Executar

Requisitos: Python 3.10 ou superior, um bot criado no [BotFather](https://t.me/BotFather) e um aplicativo com acesso à Web API no [Spotify for Developers](https://developer.spotify.com/dashboard).

Na pasta do projeto, execute no Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha:

```dotenv
TELEGRAM_BOT_TOKEN=seu_token_do_telegram
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
```

Inicie o bot:

```powershell
.venv\Scripts\python bot.py
```

Mantenha apenas uma execução aberta e conectada à internet. Para encerrar, pressione **Ctrl+C**. O `.env` contém credenciais e não deve ser publicado.

## Arquivos e dependências

- `bot.py`: funções, consultas às APIs e processamento das mensagens.
- `requirements.txt`: dependências `requests` e `python-dotenv`.
- `.env.example`: modelo de configuração sem credenciais.
- `.gitignore`: exclui credenciais, ambiente virtual e arquivos temporários.

## Limitações

O bot consulta até três candidatos por busca e pode mostrar menos após a filtragem. Compara palavras dos nomes, sem reconhecer letras de músicas ou corrigir erros de digitação. A reprodução ocorre no Spotify e depende da disponibilidade do serviço e do conteúdo.

O bot funciona no Telegram para Android, iOS e navegador enquanto o programa estiver em execução. O acesso à API está sujeito aos limites do Spotify.

## Integrantes

- Gabrielly Alves de Oliveira
- Julia de Souza Martins
- Pietro Leandro Bernardo Silva

## Referências

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [Requests](https://requests.readthedocs.io/en/latest/)
