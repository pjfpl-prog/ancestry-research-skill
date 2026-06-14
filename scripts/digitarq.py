#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
digitarq.py - Utilitario CLI para o DigitArq (Arquivo Nacional Torre do Tombo, Portugal).

O DigitArq e o portal publico do ANTT. Nao exige login para pesquisa, leitura de
fichas descritivas, listagem de imagens nem download das imagens em alta resolucao.

Este utilitario fala diretamente com a API JSON do DigitArq e expoe quatro
subcomandos:

  search   Pesquisa documentos por termo livre.
           Imprime: referenceCode | datas | hasImages | GUID | titulo
           Ex.:  python digitarq.py search "TERMO"
                 python digitarq.py search "PT/TT/PRQ" --max 50 --json

  details  Mostra a ficha descritiva de um documento (descricao, filiacao,
           datas, codigo de referencia, GUID do pai). Para a Inquisicao traz o
           campo "Estatuto social".
           Ex.:  python digitarq.py details {GUID}

  images   Lista as imagens (fileId + nome) de um documento.
           Ex.:  python digitarq.py images {GUID}
                 python digitarq.py images {GUID} --max 500

  download Baixa uma imagem em alta resolucao por fileId.
           Ex.:  python digitarq.py download {fileId}
                 python digitarq.py download {fileId} folio_007.jpg

Notas sobre codigos de referencia de paroquias:
  PT/TT/PRQ/<cod-paroquia>/<serie>/<livro>
  serie 001 = baptismos, 002 = casamentos, 003 = obitos, 004 = mistos.

Dependencia: requests  ->  pip install requests

Sem credenciais, sem dados pessoais e sem GUIDs reais embutidos: todos os
identificadores sao fornecidos pelo utilizador na linha de comandos.
"""

import argparse
import json
import sys

import requests


BASE = "https://digitarq.arquivos.pt"
SEARCH_URL = BASE + "/api/docs/search"
DETAILS_URL = BASE + "/api/docs/details/{guid}"
IMAGES_URL = BASE + "/rdigital/{guid}"
DISSEMINATION_URL = BASE + "/rdigital/dissemination"
THUMB_URL = BASE + "/rdigital/thumb"

DEFAULT_TIMEOUT = 30  # segundos
USER_AGENT = "digitarq-cli/1.0 (+ancestry-research-skill)"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _session():
    """Cria uma sessao HTTP com cabecalho de User-Agent."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def _get_json(session, url, params=None):
    """GET que devolve JSON, com tratamento de erros e timeout."""
    try:
        resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise SystemExit("Erro: tempo esgotado (timeout) ao contactar %s" % url)
    except requests.exceptions.HTTPError as exc:
        raise SystemExit("Erro HTTP %s ao contactar %s" % (exc, url))
    except requests.exceptions.RequestException as exc:
        raise SystemExit("Erro de rede ao contactar %s: %s" % (url, exc))
    try:
        return resp.json()
    except ValueError:
        raise SystemExit("Erro: resposta nao e JSON valido de %s" % url)


def _flatten_date(value):
    """
    Normaliza um campo de data. A API ora devolve uma string, ora um dict
    {"value": "1700-01-01", ...}. Devolve sempre uma string (ou "").
    """
    if value is None:
        return ""
    if isinstance(value, dict):
        # tenta varias chaves comuns
        for key in ("value", "date", "text", "displayValue"):
            if key in value and value[key]:
                return str(value[key])
        # ultimo recurso: serializa o dict
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _flatten_text(value):
    """
    Normaliza campos de texto que podem vir como string, lista de strings,
    ou lista/dict aninhado. Devolve uma string legivel.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_flatten_text(item) for item in value]
        return " / ".join(p for p in parts if p)
    if isinstance(value, dict):
        for key in ("value", "text", "displayValue", "title", "name"):
            if key in value and value[key]:
                return _flatten_text(value[key])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _first_present(d, keys, default=""):
    """Devolve o primeiro valor nao-vazio entre varias chaves possiveis."""
    if not isinstance(d, dict):
        return default
    for key in keys:
        if key in d and d[key] not in (None, "", [], {}):
            return d[key]
    return default


def _bool_str(value):
    """Converte um valor 'truthy' em 'sim'/'nao'."""
    if isinstance(value, bool):
        return "sim" if value else "nao"
    if isinstance(value, str):
        return "sim" if value.strip().lower() in ("true", "1", "yes", "sim") else "nao"
    return "sim" if value else "nao"


# --------------------------------------------------------------------------- #
# Subcomando: search
# --------------------------------------------------------------------------- #
def cmd_search(args):
    session = _session()
    params = {
        "query": args.termo,
        "objType": args.obj_type,
    }
    data = _get_json(session, SEARCH_URL, params=params)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    total = _first_present(data, ["total", "totalResults", "count"], default=0)
    results = _first_present(data, ["results", "items", "docs"], default=[])
    if not isinstance(results, list):
        results = []

    print("Total de resultados: %s" % total)
    if args.max and len(results) > args.max:
        results = results[: args.max]

    if not results:
        print("(sem resultados)")
        return

    print("-" * 78)
    for item in results:
        guid = _flatten_text(_first_present(item, ["id", "guid", "objectId"]))
        ref = _flatten_text(_first_present(item, ["referenceCode", "reference"]))
        title = _flatten_text(_first_present(item, ["titles", "title", "name"]))
        d_ini = _flatten_date(_first_present(item, ["dateInitial", "startDate"]))
        d_fim = _flatten_date(_first_present(item, ["dateFinal", "endDate"]))
        has_img = _bool_str(_first_present(item, ["hasImages", "hasImage"], default=False))

        datas = d_ini
        if d_fim and d_fim != d_ini:
            datas = "%s a %s" % (d_ini, d_fim)
        datas = datas or "s/data"

        print("%s | %s | imagens=%s | %s" % (ref or "s/ref", datas, has_img, guid))
        if title:
            print("    %s" % title)
    print("-" * 78)
    print("Mostrados %d de %s." % (len(results), total))


# --------------------------------------------------------------------------- #
# Subcomando: details
# --------------------------------------------------------------------------- #
def cmd_details(args):
    session = _session()
    url = DETAILS_URL.format(guid=args.guid)
    data = _get_json(session, url)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    guid = _flatten_text(_first_present(data, ["id", "guid", "objectId"])) or args.guid
    ref = _flatten_text(_first_present(data, ["referenceCode", "reference"]))
    title = _flatten_text(_first_present(data, ["titles", "title", "name"]))
    d_ini = _flatten_date(_first_present(data, ["dateInitial", "startDate"]))
    d_fim = _flatten_date(_first_present(data, ["dateFinal", "endDate"]))
    parent = _flatten_text(
        _first_present(data, ["parentId", "parent", "parentGuid"])
    )
    descricao = _flatten_text(
        _first_present(data, ["scopeContent", "description", "scopeAndContent"])
    )
    filiacao = _flatten_text(_first_present(data, ["filiacao", "filiation"]))
    estatuto = _flatten_text(
        _first_present(data, ["estatutoSocial", "socialStatus", "estatuto"])
    )
    has_img = _bool_str(_first_present(data, ["hasImages", "hasImage"], default=False))

    print("=" * 78)
    print("GUID:            %s" % guid)
    if ref:
        print("Cod. referencia: %s" % ref)
    if title:
        print("Titulo:          %s" % title)
    datas = d_ini
    if d_fim and d_fim != d_ini:
        datas = "%s a %s" % (d_ini, d_fim)
    if datas:
        print("Datas:           %s" % datas)
    print("Tem imagens:     %s" % has_img)
    if parent:
        print("Pai (parent):    %s" % parent)
    if filiacao:
        print("Filiacao:        %s" % filiacao)
    if estatuto:
        print("Estatuto social: %s" % estatuto)
    if descricao:
        print("-" * 78)
        print("Descricao:")
        print(descricao)
    print("=" * 78)


# --------------------------------------------------------------------------- #
# Subcomando: images
# --------------------------------------------------------------------------- #
def cmd_images(args):
    session = _session()
    url = IMAGES_URL.format(guid=args.guid)
    params = {"from": args.start, "max": args.max}
    data = _get_json(session, url, params=params)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    results = _first_present(data, ["results", "items", "images"], default=[])
    if not isinstance(results, list):
        results = []

    if not results:
        print("(sem imagens para este documento)")
        return

    print("Imagens do documento %s: %d" % (args.guid, len(results)))
    print("-" * 78)
    for item in results:
        file_id = _flatten_text(_first_present(item, ["id", "fileId"]))
        name = _flatten_text(_first_present(item, ["name", "title", "label"]))
        print("fileId=%s\t%s" % (file_id or "?", name or ""))
    print("-" * 78)
    print("Para baixar:  python digitarq.py download <fileId> [saida.jpg]")


# --------------------------------------------------------------------------- #
# Subcomando: download
# --------------------------------------------------------------------------- #
def cmd_download(args):
    session = _session()
    base = THUMB_URL if args.thumb else DISSEMINATION_URL
    params = {"fileId": args.file_id}

    out = args.saida or ("thumb_%s.jpg" % args.file_id if args.thumb else "%s.jpg" % args.file_id)

    try:
        resp = session.get(base, params=params, timeout=DEFAULT_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise SystemExit("Erro: tempo esgotado (timeout) ao baixar fileId=%s" % args.file_id)
    except requests.exceptions.HTTPError as exc:
        raise SystemExit("Erro HTTP %s ao baixar fileId=%s" % (exc, args.file_id))
    except requests.exceptions.RequestException as exc:
        raise SystemExit("Erro de rede ao baixar fileId=%s: %s" % (args.file_id, exc))

    ctype = resp.headers.get("Content-Type", "")
    if "json" in ctype.lower() or "html" in ctype.lower():
        # Provavelmente uma pagina de erro em vez da imagem
        sys.stderr.write(
            "Aviso: a resposta nao parece ser uma imagem (Content-Type: %s). "
            "Verifique o fileId.\n" % ctype
        )

    total = 0
    try:
        with open(out, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
                    total += len(chunk)
    except OSError as exc:
        raise SystemExit("Erro ao gravar '%s': %s" % (out, exc))

    print("Gravado: %s (%d bytes)" % (out, total))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        prog="digitarq.py",
        description="Utilitario CLI para o DigitArq (Torre do Tombo, Portugal). "
        "Pesquisa, fichas, listagem de imagens e download em alta resolucao.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="comando", metavar="<comando>")
    sub.required = True

    # search
    p_search = sub.add_parser("search", help="Pesquisa documentos por termo livre.")
    p_search.add_argument("termo", help="Termo de pesquisa (ex.: \"PT/TT/PRQ\" ou um lugar).")
    p_search.add_argument(
        "--obj-type",
        default="DOCUMENT",
        help="objType da pesquisa (padrao: DOCUMENT).",
    )
    p_search.add_argument(
        "--max",
        type=int,
        default=30,
        help="Numero maximo de resultados a imprimir (padrao: 30).",
    )
    p_search.add_argument("--json", action="store_true", help="Imprime o JSON bruto.")
    p_search.set_defaults(func=cmd_search)

    # details
    p_details = sub.add_parser("details", help="Mostra a ficha descritiva de um documento.")
    p_details.add_argument("guid", help="GUID do documento.")
    p_details.add_argument("--json", action="store_true", help="Imprime o JSON bruto.")
    p_details.set_defaults(func=cmd_details)

    # images
    p_images = sub.add_parser("images", help="Lista fileIds e nomes das imagens de um documento.")
    p_images.add_argument("guid", help="GUID do documento.")
    p_images.add_argument("--start", type=int, default=0, help="Indice inicial (from). Padrao: 0.")
    p_images.add_argument("--max", type=int, default=500, help="Maximo de imagens. Padrao: 500.")
    p_images.add_argument("--json", action="store_true", help="Imprime o JSON bruto.")
    p_images.set_defaults(func=cmd_images)

    # download
    p_download = sub.add_parser("download", help="Baixa uma imagem por fileId.")
    p_download.add_argument("file_id", help="fileId da imagem (numero).")
    p_download.add_argument(
        "saida",
        nargs="?",
        default=None,
        help="Caminho de saida (padrao: <fileId>.jpg).",
    )
    p_download.add_argument(
        "--thumb",
        action="store_true",
        help="Baixa a miniatura (/rdigital/thumb) em vez da alta resolucao.",
    )
    p_download.set_defaults(func=cmd_download)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        raise SystemExit("\nInterrompido pelo utilizador.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
