# 🎧 Spotify Finder

Bot para Telegram desenvolvido em Python que pesquisa músicas, artistas e álbuns usando a Web API do Spotify.

**Acesse:** [@finder_musical_unasp_bot](https://t.me/finder_musical_unasp_bot)

## Objetivo

Facilitar a busca de informações musicais pelo Telegram, integrando programação e consumo de uma API externa. O usuário pesquisa com as informações que conhece e recebe os resultados com um botão para abrir no Spotify.

## Funcionalidades

- Busca de músicas por título, com artista e/ou álbum opcionais.
- Busca de artistas e álbuns pelo nome.
- Menu de comandos: selecione uma busca e envie o nome na mensagem seguinte.
- Resultados com título, artista e álbum, quando aplicável.
- Botão para abrir cada resultado no Spotify.
- Filtragem por palavras, ignorando maiúsculas e acentos.
- Tratamento de falhas de conexão, limite de consultas e buscas sem resultados.

## Como usar

Abra o bot, toque em **Iniciar**, escolha uma busca no menu e envie o nome.

| Comando | Função |
| --- | --- |
| `/start` | Apresentação do bot |
| `/musica` | Buscar música |
| `/artista` | Buscar artista |
| `/album` | Buscar álbum |
| `/ajuda` | Instruções breves |

Também é possível enviar tudo junto, como `/musica Yellow Coldplay`, `/artista Coldplay` ou `/album Parachutes`.

## Tecnologias e API externa

- **Python 3.10 ou superior**.
- **python-telegram-bot:** comunicação com o Telegram.
- **httpx:** requisições à API do Spotify.
- **python-dotenv:** leitura das credenciais locais.

O programa recebe a mensagem do Telegram, autentica o aplicativo no Spotify pelo fluxo **Client Credentials** e consulta **GET /v1/search**. Depois, filtra os resultados e envia a resposta. O token do Spotify é reutilizado até próximo de expirar.

A busca depende da API externa, sem uma lista local de músicas. Os usuários não precisam fazer login no Spotify para pesquisar pelo bot.

## Instalação e execução

### 1. Credenciais

Crie um bot no [BotFather](https://t.me/BotFather) e obtenha seu token. Crie também um aplicativo para **Web API** no [painel do Spotify](https://developer.spotify.com/dashboard), conforme os requisitos de acesso exibidos, e obtenha o **Client ID** e o **Client Secret**.

### 2. Ambiente

Baixe ou clone este repositório. No Windows, abra o PowerShell na pasta que contém `bot.py` e execute:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Copie `.env.example` para um arquivo chamado `.env`, caso ainda não exista, e preencha:

```dotenv
TELEGRAM_BOT_TOKEN=seu_token_do_telegram
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
```

**Não publique o `.env`.** Ele contém credenciais privadas e está listado no `.gitignore`. O `.env.example` deve permanecer sem valores reais.

### 3. Iniciar o bot

```powershell
.venv\Scripts\python bot.py
```

Mantenha o computador conectado à internet e o programa aberto para receber mensagens. Encerre com **Ctrl+C** e reinicie após alterações no código.

## Arquivos do projeto

| Arquivo | Conteúdo |
| --- | --- |
| `bot.py` | Comandos, integração com o Spotify, filtros e respostas |
| `requirements.txt` | Dependências |
| `.env.example` | Modelo de configuração sem credenciais |
| `.gitignore` | Exclusões do versionamento |
| `README.md` | Descrição e instruções |

## Validação e limitações

Durante o desenvolvimento, foram realizados testes manuais de músicas, artistas e álbuns no Telegram. O link de uma música foi aberto e reproduzido pelo Spotify no celular. As combinações de título, artista e álbum e a filtragem de resultados também foram verificadas localmente.

Para conferir a instalação, teste `/start`, uma busca de cada tipo e o fluxo de selecionar uma busca no menu e enviar o nome na mensagem seguinte.

- A busca consulta até três candidatos e pode apresentar menos após a filtragem; não é uma pesquisa exaustiva do catálogo.
- O filtro compara palavras dos nomes. Não reconhece trechos de letras nem corrige automaticamente erros de digitação.
- A reprodução ocorre no Spotify, não no bot, e depende da disponibilidade do conteúdo e do serviço.
- O bot pode ser acessado no Telegram para Android, iOS ou navegador. Ele responde somente enquanto o programa estiver em execução.
- O acesso à API depende das regras e dos limites do Spotify.

## Integrantes

- Gabrielly Alves de Oliveira
- Julia de Souza Martins
- Pietro Leandro Bernardo Silva

## Referências

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)
- [Client Credentials](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)
- [Busca no Spotify](https://developer.spotify.com/documentation/web-api/reference/search)
- [python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/)
