#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify.py - Envio de notificacoes/resultados por Telegram.

Parte da skill generica de pesquisa de ancestralidade/genealogia.
Util para um agente avisar o usuario quando termina uma varredura,
ou para entregar um achado (transcricao, recorte de imagem, GEDCOM, PDF).

CREDENCIAIS: lidas EXCLUSIVAMENTE de variaveis de ambiente. Nunca hardcode.
    NOTIFY_TELEGRAM_TOKEN  -> token do bot (BotFather), ex.: 123456:ABC-DEF...
    NOTIFY_TELEGRAM_CHAT   -> chat_id de destino (numero ou @canal)

Exemplos de uso (CLI):
    python notify.py msg "Varredura do livro {GUID} concluida: 3 achados"
    python notify.py file ./recorte_folio_12.jpg --caption "Casamento [?] folio 12"
    python notify.py file ./arvore.ged --caption "GEDCOM extraido (getmyancestors)"

Como definir as variaveis (sem deixar segredo no codigo/historico):
    # Linux/macOS (bash)
    export NOTIFY_TELEGRAM_TOKEN="..."   # NAO comitar
    export NOTIFY_TELEGRAM_CHAT="..."
    # Windows PowerShell
    $env:NOTIFY_TELEGRAM_TOKEN = "..."
    $env:NOTIFY_TELEGRAM_CHAT  = "..."

Dependencias: requests  (ver requirements.txt).

NOTA SOBRE EMOJIS / CARACTERES PROBLEMATICOS:
    O Telegram aceita UTF-8, mas terminais/consoles (especialmente Windows
    cp1252) podem quebrar ao imprimir emojis ou simbolos como a seta "->".
    Para mensagens de status geradas por agente, prefira texto ASCII simples.
    O parametro --no-emoji (ou strip_emoji=True) remove emojis e alguns
    simbolos nao-ASCII problematicos ANTES do envio, evitando UnicodeError
    no log local e ruido na mensagem.
"""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "ERRO: o pacote 'requests' nao esta instalado.\n"
        "      Instale com: pip install -r requirements.txt\n"
    )
    raise

# Tempo maximo (segundos) de espera por resposta da API do Telegram.
HTTP_TIMEOUT = 60

# Limite de tamanho de um documento via Bot API (50 MB).
TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024

# Nomes das variaveis de ambiente (centralizados para facil leitura/erro).
ENV_TOKEN = "NOTIFY_TELEGRAM_TOKEN"
ENV_CHAT = "NOTIFY_TELEGRAM_CHAT"


class NotifyError(RuntimeError):
    """Erro de configuracao ou de envio."""


# --------------------------------------------------------------------------- #
# Credenciais / configuracao
# --------------------------------------------------------------------------- #
def _get_credentials() -> tuple[str, str]:
    """Le token e chat das variaveis de ambiente. Nunca hardcoded."""
    token = os.environ.get(ENV_TOKEN, "").strip()
    chat = os.environ.get(ENV_CHAT, "").strip()
    faltando = []
    if not token:
        faltando.append(ENV_TOKEN)
    if not chat:
        faltando.append(ENV_CHAT)
    if faltando:
        raise NotifyError(
            "Variavel(eis) de ambiente ausente(s): "
            + ", ".join(faltando)
            + ".\nDefina-as antes de usar (veja o cabecalho de notify.py). "
            "NUNCA coloque o token no codigo."
        )
    return token, chat


def _api_url(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


# --------------------------------------------------------------------------- #
# Higienizacao de texto (emojis / caracteres problematicos)
# --------------------------------------------------------------------------- #
# Mapeamento de simbolos nao-ASCII comuns para equivalentes seguros.
_REPLACEMENTS = {
    "→": "->",   # seta direita
    "←": "<-",   # seta esquerda
    "—": "-",    # travessao em
    "–": "-",    # travessao en
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "…": "...",  # reticencias
    " ": " ",    # espaco nao separavel
    "•": "*",    # bullet
}


def strip_emoji(text: str) -> str:
    """
    Remove emojis e troca simbolos nao-ASCII problematicos por equivalentes
    seguros. Acentos latinos (a, c-cedilha, etc.) sao PRESERVADOS porque o
    Telegram os exibe bem; o alvo sao emojis e pictogramas que quebram
    consoles e poluem mensagens de status.
    """
    if not text:
        return text
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        # So = Symbol, other (emojis, pictogramas); Cs = surrogate.
        if cat in ("So", "Cs"):
            continue
        # Emojis em blocos altos (variation selectors, supplementary planes).
        if ord(ch) >= 0x1F000 or ch in ("️", "‍"):
            continue
        out.append(ch)
    return "".join(out)


# --------------------------------------------------------------------------- #
# Tratamento de resposta HTTP
# --------------------------------------------------------------------------- #
def _handle_response(resp: "requests.Response") -> dict:
    """Valida a resposta da API e devolve o JSON, levantando NotifyError."""
    try:
        data = resp.json()
    except ValueError:
        data = None

    if resp.status_code != 200 or not (data and data.get("ok")):
        descr = ""
        if isinstance(data, dict):
            descr = data.get("description", "")
        raise NotifyError(
            f"Telegram respondeu HTTP {resp.status_code}"
            + (f": {descr}" if descr else f": {resp.text[:300]}")
        )
    return data


# --------------------------------------------------------------------------- #
# API publica
# --------------------------------------------------------------------------- #
def send_message(text: str, no_emoji: bool = True) -> dict:
    """
    Envia uma mensagem de texto.

    text     : conteudo da mensagem.
    no_emoji : se True (padrao), higieniza emojis/simbolos problematicos.
    """
    if not text:
        raise NotifyError("Texto vazio: nada a enviar.")
    token, chat = _get_credentials()
    if no_emoji:
        text = strip_emoji(text)

    # Telegram limita mensagens a ~4096 caracteres.
    if len(text) > 4096:
        text = text[:4093] + "..."

    try:
        resp = requests.post(
            _api_url(token, "sendMessage"),
            data={"chat_id": chat, "text": text, "disable_web_page_preview": True},
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise NotifyError(f"Falha de rede ao enviar mensagem: {exc}") from exc

    return _handle_response(resp)


def send_document(path: str, caption: str = "", no_emoji: bool = True) -> dict:
    """
    Envia um arquivo (documento) com legenda opcional.

    path     : caminho do arquivo a enviar.
    caption  : legenda (max ~1024 caracteres; truncada se exceder).
    no_emoji : se True (padrao), higieniza a legenda.
    """
    if not path or not os.path.isfile(path):
        raise NotifyError(f"Arquivo nao encontrado: {path!r}")

    size = os.path.getsize(path)
    if size > TELEGRAM_FILE_LIMIT:
        raise NotifyError(
            f"Arquivo de {size / (1024*1024):.1f} MB excede o limite de "
            f"50 MB da Bot API. Compacte, divida ou envie por outro meio."
        )

    token, chat = _get_credentials()
    if caption and no_emoji:
        caption = strip_emoji(caption)
    if caption and len(caption) > 1024:
        caption = caption[:1021] + "..."

    data = {"chat_id": chat}
    if caption:
        data["caption"] = caption

    try:
        with open(path, "rb") as fh:
            files = {"document": (os.path.basename(path), fh)}
            resp = requests.post(
                _api_url(token, "sendDocument"),
                data=data,
                files=files,
                timeout=HTTP_TIMEOUT,
            )
    except requests.RequestException as exc:
        raise NotifyError(f"Falha de rede ao enviar documento: {exc}") from exc
    except OSError as exc:
        raise NotifyError(f"Falha ao abrir arquivo {path!r}: {exc}") from exc

    return _handle_response(resp)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notify.py",
        description="Envia notificacao/resultado por Telegram "
        "(token e chat vem de variaveis de ambiente).",
    )
    parser.add_argument(
        "--keep-emoji",
        action="store_true",
        help="NAO higienizar emojis/simbolos (por padrao sao removidos).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_msg = sub.add_parser("msg", help="Enviar uma mensagem de texto.")
    p_msg.add_argument("text", help="Texto da mensagem.")

    p_file = sub.add_parser("file", help="Enviar um arquivo com legenda.")
    p_file.add_argument("path", help="Caminho do arquivo.")
    p_file.add_argument("--caption", default="", help="Legenda do arquivo.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    no_emoji = not args.keep_emoji

    try:
        if args.cmd == "msg":
            send_message(args.text, no_emoji=no_emoji)
            print("OK: mensagem enviada.")
        elif args.cmd == "file":
            send_document(args.path, caption=args.caption, no_emoji=no_emoji)
            print(f"OK: arquivo enviado ({args.path}).")
        else:  # pragma: no cover
            parser.error("comando desconhecido")
    except NotifyError as exc:
        sys.stderr.write(f"ERRO: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
