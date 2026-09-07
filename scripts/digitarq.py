#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
digitarq.py - Utilitario CLI para o DigitArq (Arquivo Nacional Torre do Tombo, Portugal).

O DigitArq e o portal publico do ANTT. Nao exige login para pesquisa, leitura de
fichas descritivas, listagem de imagens nem download das imagens em alta resolucao.

Este utilitario fala diretamente com a API JSON do DigitArq e expoe quatro
subcomandos:

  search   Pesquisa documentos por termo livre, paginando ate ao limite pedido.
           Imprime: referenceCode | datas | ficheiros | GUID | titulo
           Ex.:  python digitarq.py search "TERMO"
                 python digitarq.py search "PT/TT/PRQ" --max 50 --sort reference_code
                 python digitarq.py search "TERMO" --with-images --json

  details  Mostra a ficha descritiva de um documento (descricao, filiacao,
           datas, codigo de referencia, GUID do pai). Para a Inquisicao traz o
           campo "Estatuto social".
           Ex.:  python digitarq.py details {GUID}

  images   Lista TODAS as imagens (fileId + nome) de um documento, paginando.
           Ex.:  python digitarq.py images {GUID}
                 python digitarq.py images {GUID} --max 100

  download Baixa uma imagem em alta resolucao por fileId.
           Ex.:  python digitarq.py download {fileId}
                 python digitarq.py download {fileId} folio_007.jpg

Notas sobre codigos de referencia de paroquias:
  PT/TT/PRQ/<cod-paroquia>/<serie>/<livro>
  serie 001 = baptismos, 002 = casamentos, 003 = obitos, 004 = mistos.

--- PAGINACAO, LEIA ANTES DE CONFIAR NO RESULTADO ---------------------------
A API devolve 10 resultados por pedido e ignora pedidos de pagina maior. Para
ver alem dos 10 primeiros e preciso repetir o pedido movendo `fromIndex`.

A ordenacao PADRAO do portal e por RELEVANCIA, e relevancia NAO da ordem total
estavel: empates trocam de posicao entre pedidos, de modo que paginar por
relevancia repete alguns resultados e pode saltar outros. Verificado em
07/09/2026: com a ordenacao padrao, `fromIndex=10` devolveu 3 itens que ja
tinham vindo na primeira pagina.

Por isso:
  * `--sort relevance` (padrao) preserva a ordem do portal, que e a que serve
    para procurar um NOME. Ao passar da primeira pagina, este script avisa no
    stderr, remove repetidos pelo GUID e diz quantos removeu. Mesmo assim NAO
    ha garantia de completude.
  * `--sort reference_code` (ou outro campo) da ordem estavel e paginacao
    integra, e e o que serve para varrer uma COTA. Verificado: 5 paginas de uma
    query de 43 resultados devolveram 43 unicos, sem sobreposicao.
Escolha conforme a pergunta. Nao existe cursor/snapshot do lado do servidor: se
o acervo mudar durante a paginacao, resultado pode escapar em qualquer modo.

Dependencia: requests  ->  pip install requests

Sem credenciais, sem dados pessoais e sem GUIDs reais embutidos: todos os
identificadores sao fornecidos pelo utilizador na linha de comandos.
"""

import argparse
import json
import os
import sys
import time

import requests

BASE = "https://digitarq.arquivos.pt"
SEARCH_URL = BASE + "/api/docs/search"
DETAILS_URL = BASE + "/api/docs/details/{guid}"
IMAGES_URL = BASE + "/rdigital/{guid}"
DISSEMINATION_URL = BASE + "/rdigital/dissemination"
THUMB_URL = BASE + "/rdigital/thumb"

DEFAULT_TIMEOUT = 30  # segundos
USER_AGENT = "digitarq-cli/2.0 (+ancestry-research-skill)"

# O servidor fixa a pagina em 10; pedir mais nao aumenta (verificado 07/09/2026).
SEARCH_PAGE = 10
# Teto de resultados por execucao. 500 = 50 pedidos. Acima disto o caminho certo
# nao e a busca: e localizar o livro e varrer as imagens com `images`.
HARD_CAP = 500
# Campos de ordenacao aceites. Nome errado devolve HTTP 400.
SORT_FIELDS = ("relevance", "reference_code", "title", "dateInitial", "dateFinal")
# Pausa entre pedidos: o DigitArq e servico publico, nao o martele.
DEFAULT_DELAY = 0.5
MAX_RETRIES = 3

# Assinaturas de ficheiro de imagem (JPEG, PNG, TIFF LE/BE, GIF, BMP, WEBP=RIFF).
IMAGE_MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"II*\x00", b"MM\x00*",
               b"GIF87a", b"GIF89a", b"BM", b"RIFF")


class DigitarqError(Exception):
    """Falha de rede, de contrato da API ou de conteudo inesperado."""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _safe_stdout():
    """
    Consolas Windows em cp1252 rebentam com UnicodeEncodeError ao imprimir nomes
    fora do latim (verificado). Trocar o erro por '?' e melhor que abortar a
    pesquisa; a informacao completa continua disponivel com --json.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover
            pass


def _session():
    """Cria uma sessao HTTP com cabecalho de User-Agent."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def _sleep_from_retry_after(resp, fallback):
    """Respeita Retry-After quando o servidor o envia; senao usa o fallback."""
    valor = resp.headers.get("Retry-After", "")
    try:
        return max(float(valor), fallback)
    except (TypeError, ValueError):
        return fallback


def _get_json(session, url, params=None, delay=DEFAULT_DELAY):
    """
    GET que devolve JSON, com timeout e uma retentativa educada em 429/5xx.
    Levanta DigitarqError (nunca SystemExit: o modulo tem de ser importavel).
    """
    espera = delay
    ultimo = ""
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.exceptions.Timeout:
            ultimo = "tempo esgotado (timeout)"
        except requests.exceptions.RequestException as exc:
            ultimo = "erro de rede: %s" % exc
        else:
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                ultimo = "HTTP %s" % resp.status_code
                if tentativa < MAX_RETRIES:
                    time.sleep(_sleep_from_retry_after(resp, espera))
                    espera *= 2
                    continue
            elif not resp.ok:
                raise DigitarqError("HTTP %s ao contactar %s" % (resp.status_code, url))
            else:
                try:
                    return resp.json()
                except ValueError:
                    raise DigitarqError("resposta nao e JSON valido de %s" % url) from None
        if tentativa < MAX_RETRIES:
            time.sleep(espera)
            espera *= 2
    raise DigitarqError("falhou %d vezes ao contactar %s (%s)" % (MAX_RETRIES, url, ultimo))


def _flatten_date(value):
    """
    Normaliza um campo de data. A API ora devolve uma string, ora um dict
    {"value": "1700-01-01", ...}, ora um dict com TODOS os campos a null.
    Devolve sempre uma string; string vazia quando nao ha data utilizavel.
    NUNCA devolve JSON cru: um dict vazio na tela e ruido, nao informacao.
    """
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("value", "date", "text", "displayValue"):
            if value.get(key):
                return str(value[key])
        return ""
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
            if value.get(key):
                return _flatten_text(value[key])
        return ""
    return str(value)


def _first_present(d, keys, default=""):
    """Devolve o primeiro valor nao-vazio entre varias chaves possiveis."""
    if not isinstance(d, dict):
        return default
    for key in keys:
        if key in d and d[key] not in (None, "", [], {}):
            return d[key]
    return default


def _files_label(item):
    """
    Quantos ficheiros digitais o resultado declara.

    ATENCAO: o resultado da BUSCA nao traz `hasImages` (a chave simplesmente nao
    existe ali; quem a tem e o `details`). O que existe e `filesCount`. A versao
    anterior deste script procurava `hasImages` na busca, nao encontrava, e por
    isso imprimia SEMPRE "imagens=nao", inclusive para livros digitalizados.

    Rotulamos "ficheiros", nao "imagens", de proposito: `filesCount` conta os
    objetos digitais associados a ficha. Num livro paroquial conferido em
    07/09/2026 os 284 ficheiros eram 284 JPEG, mas o contrato da API nao promete
    que todo ficheiro seja imagem. Use `details` para confirmar `hasImages`.
    """
    valor = item.get("filesCount")
    if valor is None:
        return "?"
    try:
        return str(int(valor))
    except (TypeError, ValueError):
        return "?"


def _guid_of(item):
    return _flatten_text(_first_present(item, ["id", "guid", "objectId"]))


def _datas_of(item):
    d_ini = _flatten_date(_first_present(item, ["dateInitial", "startDate"]))
    d_fim = _flatten_date(_first_present(item, ["dateFinal", "endDate"]))
    if d_fim and d_fim != d_ini:
        return "%s a %s" % (d_ini or "s/data", d_fim)
    return d_ini or "s/data"


# --------------------------------------------------------------------------- #
# Busca com paginacao
# --------------------------------------------------------------------------- #
def search(session, termo, obj_type="DOCUMENT", limit=30, sort="relevance",
           order="asc", with_images=False, delay=DEFAULT_DELAY, avisar=None):
    """
    Pagina a busca ate reunir `limit` resultados ou esgotar o total.

    Devolve (resultados, total, notas). `notas` e uma lista de avisos em texto:
    repetidos removidos, paginacao interrompida, contrato inesperado. O chamador
    decide o que mostrar; nada e escondido.
    """
    if sort not in SORT_FIELDS:
        raise DigitarqError("sort invalido: %r. Aceites: %s" % (sort, ", ".join(SORT_FIELDS)))
    if limit is None or limit < 1:
        raise DigitarqError("--max tem de ser >= 1")
    teto = min(limit, HARD_CAP)
    notas = []
    if limit > HARD_CAP:
        notas.append("pedido de %d cortado no teto de %d resultados por execucao "
                     "(acima disto, localize o livro e use o subcomando images)"
                     % (limit, HARD_CAP))
    if avisar is None:
        avisar = lambda _m: None  # noqa: E731

    resultados, vistos, total, offset = [], set(), None, 0
    repetidos = 0
    while True:
        params = {"query": termo, "objType": obj_type,
                  "fromIndex": offset, "max": SEARCH_PAGE, "sortField": sort}
        if sort != "relevance":
            params["sortOrder"] = order
        if with_images:
            params["hasImages"] = "true"

        data = _get_json(session, SEARCH_URL, params=params, delay=delay)
        pagina = data.get("results")
        if not isinstance(pagina, list):
            notas.append("a API devolveu 'results' fora do formato esperado; "
                         "paginacao interrompida")
            break

        # O total e relido a cada pagina: se o acervo mudar durante a varredura,
        # e melhor saber do que continuar com um numero congelado.
        novo_total = data.get("total")
        try:
            novo_total = int(novo_total)
        except (TypeError, ValueError):
            novo_total = None
        if novo_total is not None:
            if total is not None and novo_total != total:
                notas.append("o total mudou durante a paginacao (%d -> %d): o acervo "
                             "foi alterado, o resultado pode estar incompleto"
                             % (total, novo_total))
            total = novo_total

        if not pagina:
            break

        antes = len(resultados)
        for item in pagina:
            guid = _guid_of(item)
            chave = guid or json.dumps(item, sort_keys=True)[:200]
            if chave in vistos:
                repetidos += 1
                continue
            vistos.add(chave)
            resultados.append(item)

        if len(resultados) == antes:
            # A pagina inteira era repetida: sem progresso, parar em vez de
            # rodar em circulos gastando pedidos do servico publico.
            notas.append("pagina em fromIndex=%d nao trouxe nenhum resultado novo; "
                         "paginacao interrompida" % offset)
            break

        offset += len(pagina)
        if len(resultados) >= teto:
            break
        if total is not None and offset >= total:
            break
        if len(pagina) < SEARCH_PAGE and total is not None and offset < total:
            notas.append("o servidor devolveu %d resultados (menos que a pagina de %d) "
                         "antes de esgotar o total; paginacao interrompida"
                         % (len(pagina), SEARCH_PAGE))
            break
        time.sleep(delay)

    if repetidos:
        notas.append("%d resultado(s) repetido(s) removido(s) por GUID%s"
                     % (repetidos,
                        " (efeito da ordenacao por relevancia; use --sort reference_code "
                        "para paginacao integra)" if sort == "relevance" else ""))
    return resultados[:teto], total, notas


def cmd_search(args):
    session = _session()
    if args.sort == "relevance" and args.max > SEARCH_PAGE:
        sys.stderr.write(
            "Aviso: --sort relevance nao da ordem estavel; alem da primeira pagina pode\n"
            "       repetir e saltar resultados. Para varrer uma cota de forma integra\n"
            "       use --sort reference_code.\n")

    resultados, total, notas = search(
        session, args.termo, obj_type=args.obj_type, limit=args.max,
        sort=args.sort, order=args.order, with_images=args.with_images,
        delay=args.delay)

    if args.json:
        print(json.dumps({"total": total, "returned": len(resultados),
                          "notes": notas, "results": resultados},
                         ensure_ascii=False, indent=2))
        return

    print("Total de resultados: %s" % (total if total is not None else "?"))
    if not resultados:
        print("(sem resultados)")
        for n in notas:
            sys.stderr.write("Aviso: %s\n" % n)
        return

    print("-" * 78)
    for item in resultados:
        ref = _flatten_text(_first_present(item, ["referenceCode", "reference"]))
        title = _flatten_text(_first_present(item, ["titles", "title", "name"]))
        print("%s | %s | ficheiros=%s | %s"
              % (ref or "s/ref", _datas_of(item), _files_label(item), _guid_of(item)))
        if title:
            print("    %s" % title)
    print("-" * 78)
    print("Mostrados %d de %s." % (len(resultados), total if total is not None else "?"))
    if total is not None and len(resultados) < total:
        print("Faltam %d: repita com --max maior (teto %d) ou refine o termo."
              % (total - len(resultados), HARD_CAP))
    for n in notas:
        sys.stderr.write("Aviso: %s\n" % n)


# --------------------------------------------------------------------------- #
# Subcomando: details
# --------------------------------------------------------------------------- #
def cmd_details(args):
    session = _session()
    data = _get_json(session, DETAILS_URL.format(guid=args.guid))

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    guid = _guid_of(data) or args.guid
    ref = _flatten_text(_first_present(data, ["referenceCode", "reference"]))
    title = _flatten_text(_first_present(data, ["titles", "title", "name"]))
    parent = _flatten_text(_first_present(data, ["parentId", "parent", "parentGuid"]))
    descricao = _flatten_text(
        _first_present(data, ["scopeContent", "description", "scopeAndContent"]))
    filiacao = _flatten_text(_first_present(data, ["filiacao", "filiation"]))
    estatuto = _flatten_text(
        _first_present(data, ["estatutoSocial", "socialStatus", "estatuto"]))
    # Aqui a chave EXISTE: e o details, nao a busca.
    tem_img = data.get("hasImages")
    tem_img = "sim" if tem_img is True else ("nao" if tem_img is False else "?")

    print("=" * 78)
    print("GUID:            %s" % guid)
    if ref:
        print("Cod. referencia: %s" % ref)
    if title:
        print("Titulo:          %s" % title)
    datas = _datas_of(data)
    if datas and datas != "s/data":
        print("Datas:           %s" % datas)
    print("Tem imagens:     %s" % tem_img)
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
def _image_integer(value, field):
    # bool e float passam em int(), mas nao sao posicoes inteiras do contrato.
    if isinstance(value, bool) or not (
        isinstance(value, int) or
        (isinstance(value, str) and value.isascii() and value.isdigit())
    ):
        raise DigitarqError("campo de imagens %s ausente ou invalido" % field)
    result = int(value)
    if result < 0:
        raise DigitarqError("campo de imagens %s negativo" % field)
    return result


def list_images(session, guid, limit=None, delay=DEFAULT_DELAY, start=0):
    """
    Enumera imagens a partir de start (base zero), validando cada pagina.
    'from' era ignorado pelo servidor e repetia o inicio; fromIndex e o
    deslocamento verificado em 07/09/2026. Uma lista repetida nao e cobertura.
    """
    start = _image_integer(start, "start")
    if limit is not None:
        limit = _image_integer(limit, "max")
        if limit == 0:
            raise DigitarqError("--max tem de ser >= 1")
    imagens, vistos, total, offset = [], set(), None, start
    while True:
        pedido = 500 if limit is None else min(500, limit - len(imagens))
        data = _get_json(session, IMAGES_URL.format(guid=guid),
                         params={"fromIndex": offset, "max": pedido}, delay=delay)
        if not isinstance(data, dict):
            raise DigitarqError("resposta de imagens fora do formato esperado")
        recebido = _image_integer(data.get("fromIndex"), "fromIndex")
        if recebido != offset:
            raise DigitarqError("fromIndex devolvido %d difere do pedido %d" % (recebido, offset))
        novo_total = _image_integer(data.get("total"), "total")
        if total is not None and novo_total != total:
            raise DigitarqError("total de imagens mudou durante a paginacao; repita a consulta")
        total = novo_total
        pagina = data.get("results")
        if not isinstance(pagina, list):
            raise DigitarqError("results de imagens fora do formato esperado")
        if not pagina:
            if offset < total:
                raise DigitarqError("pagina vazia antes do total de imagens; cobertura incompleta")
            break
        if offset + len(pagina) > total:
            raise DigitarqError("pagina excede o total declarado de imagens")
        for item in pagina:
            ident = item.get("id") if isinstance(item, dict) else None
            if isinstance(ident, bool) or not isinstance(ident, (str, int)) or ident == "":
                raise DigitarqError("imagem sem id valido; cobertura nao verificavel")
            chave = str(ident)
            if chave in vistos:
                raise DigitarqError("id de imagem repetido; cobertura nao verificavel")
            vistos.add(chave)
        imagens.extend(pagina)
        offset = recebido + len(pagina)
        if limit is not None and len(imagens) >= limit:
            break
        if offset >= total:
            break
        time.sleep(delay)
    if limit is not None:
        imagens = imagens[:limit]
    return imagens, total


def cmd_images(args):
    session = _session()
    imagens, total = list_images(session, args.guid, limit=args.max, delay=args.delay,
                                 start=args.start)

    if args.json:
        print(json.dumps({"fromIndex": args.start, "total": total,
                          "returned": len(imagens), "results": imagens},
                         ensure_ascii=False, indent=2))
        return

    if not imagens:
        print("(sem imagens no intervalo solicitado)")
        return

    print("Imagens do documento %s: %d de %s"
          % (args.guid, len(imagens), total if total is not None else "?"))
    print("-" * 78)
    for item in imagens:
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
    out = args.saida or ("thumb_%s.jpg" % args.file_id if args.thumb else "%s.jpg" % args.file_id)
    out = os.path.abspath(out)

    if os.path.exists(out) and not args.force:
        raise DigitarqError("'%s' ja existe. Use --force para sobrescrever ou indique "
                            "outro nome de saida." % out)

    try:
        resp = session.get(base, params={"fileId": args.file_id},
                           timeout=DEFAULT_TIMEOUT, stream=True)
    except requests.exceptions.Timeout:
        raise DigitarqError("tempo esgotado (timeout) ao baixar fileId=%s" % args.file_id) from None
    except requests.exceptions.RequestException as exc:
        raise DigitarqError("erro de rede ao baixar fileId=%s: %s" % (args.file_id, exc)) from None

    if not resp.ok:
        raise DigitarqError("HTTP %s ao baixar fileId=%s" % (resp.status_code, args.file_id))

    # DECIDIR ANTES DE GRAVAR. A versao anterior avisava no stderr e gravava a
    # pagina de erro como .jpg, saindo com codigo 0; se o destino ja existisse,
    # destruia o ficheiro bom. Aqui nada e escrito enquanto nao se confirma que
    # o inicio do corpo tem assinatura de imagem.
    ctype = (resp.headers.get("Content-Type") or "").lower()
    chunks = resp.iter_content(chunk_size=65536)
    primeiro = b""
    for pedaco in chunks:
        if pedaco:
            primeiro = pedaco
            break

    if "html" in ctype or "json" in ctype or not primeiro.startswith(IMAGE_MAGIC):
        raise DigitarqError(
            "a resposta para fileId=%s nao e uma imagem (Content-Type: %s). "
            "Nada foi gravado; confirme o fileId." % (args.file_id, ctype or "?"))

    # Grava em ficheiro temporario e so no fim substitui o destino: um download
    # interrompido nao deixa .jpg truncado no lugar de um bom.
    parcial = out + ".part"
    total = 0
    try:
        os.makedirs(os.path.dirname(parcial) or ".", exist_ok=True)
        with open(parcial, "wb") as fh:
            fh.write(primeiro)
            total += len(primeiro)
            for pedaco in chunks:
                if pedaco:
                    fh.write(pedaco)
                    total += len(pedaco)
        os.replace(parcial, out)
    except OSError as exc:
        try:
            os.remove(parcial)
        except OSError:
            pass
        raise DigitarqError("erro ao gravar '%s': %s" % (out, exc)) from None

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

    p_search = sub.add_parser("search", help="Pesquisa documentos por termo livre.")
    p_search.add_argument("termo", help="Termo de pesquisa (ex.: \"PT/TT/PRQ\" ou um lugar).")
    p_search.add_argument("--obj-type", default="DOCUMENT",
                          help="objType da pesquisa (padrao: DOCUMENT).")
    p_search.add_argument("--max", type=int, default=30,
                          help="Quantos resultados reunir, paginando (padrao: 30, teto %d)."
                               % HARD_CAP)
    p_search.add_argument("--sort", default="relevance", choices=list(SORT_FIELDS),
                          help="Campo de ordenacao. 'relevance' (padrao) e a ordem do portal "
                               "e serve para procurar NOME, mas NAO pagina de forma fiavel. "
                               "'reference_code' da paginacao integra e serve para varrer COTA.")
    p_search.add_argument("--order", default="asc", choices=["asc", "desc"],
                          help="Sentido da ordenacao (ignorado com --sort relevance).")
    p_search.add_argument("--with-images", action="store_true",
                          help="Filtra no SERVIDOR so documentos com imagens (hasImages=true).")
    p_search.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                          help="Pausa em segundos entre pedidos (padrao: %.1f)." % DEFAULT_DELAY)
    p_search.add_argument("--json", action="store_true",
                          help="Imprime um objeto JSON unico com total, notas e resultados.")
    p_search.set_defaults(func=cmd_search)

    p_details = sub.add_parser("details", help="Mostra a ficha descritiva de um documento.")
    p_details.add_argument("guid", help="GUID do documento.")
    p_details.add_argument("--json", action="store_true", help="Imprime o JSON bruto.")
    p_details.set_defaults(func=cmd_details)

    p_images = sub.add_parser("images", help="Lista fileIds e nomes das imagens de um documento.")
    p_images.add_argument("guid", help="GUID do documento.")
    p_images.add_argument("--start", type=int, default=0,
                          help="Indice inicial de base zero (padrao: 0).")
    p_images.add_argument("--max", type=int, default=None,
                          help="Teto de imagens a listar (padrao: todas).")
    p_images.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                          help="Pausa em segundos entre pedidos (padrao: %.1f)." % DEFAULT_DELAY)
    p_images.add_argument("--json", action="store_true", help="Imprime o JSON bruto.")
    p_images.set_defaults(func=cmd_images)

    p_download = sub.add_parser("download", help="Baixa uma imagem por fileId.")
    p_download.add_argument("file_id", help="fileId da imagem (numero).")
    p_download.add_argument("saida", nargs="?", default=None,
                            help="Caminho de saida (padrao: <fileId>.jpg).")
    p_download.add_argument("--thumb", action="store_true",
                            help="Baixa a miniatura (/rdigital/thumb) em vez da alta resolucao.")
    p_download.add_argument("--force", action="store_true",
                            help="Sobrescreve o ficheiro de saida se ja existir.")
    p_download.set_defaults(func=cmd_download)

    return parser


def main(argv=None):
    _safe_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except DigitarqError as exc:
        sys.stderr.write("Erro: %s\n" % exc)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrompido pelo utilizador.\n")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
