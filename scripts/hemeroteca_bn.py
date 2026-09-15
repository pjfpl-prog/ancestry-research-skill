#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hemeroteca_bn.py - Utilitario CLI para a Hemeroteca Digital Brasileira (Biblioteca
Nacional, memoria.bn.gov.br).

A Hemeroteca e um acervo publico de jornais e revistas com busca por OCR. O
visualizador oficial (DocReader) exige CAPTCHA desde 2025 e NAO serve para
automacao; este utilitario usa os dois caminhos publicos que respondem a frio,
sem sessao e sem CAPTCHA (contrato conferido em 15/09/2026, ver
references/18-hemeroteca-bn.md):

  1. a lista de edicoes de UM periodico que contem um termo
     (docreader/ListaPastaOcor.aspx);
  2. o PDF estatico de UMA edicao inteira (hemeroteca-pdf.bn.gov.br), com a camada
     de texto do OCR da BN.

Subcomandos:

  edicoes   Lista as edicoes de um periodico (bib) em que o termo ocorre.
            Ex.:  python hemeroteca_bn.py edicoes 103730_05 "TERMO"
                  python hemeroteca_bn.py edicoes 103730_05 "TERMO" --json

  pdf       Baixa o PDF publico de uma edicao. So publica no destino um PDF que
            chegou inteiro e abre.
            Ex.:  python hemeroteca_bn.py pdf 103730 1921 00193 edicao.pdf

  paginas   Acha, pelo texto OCR embutido, as paginas de um PDF que citam o termo.
            Ex.:  python hemeroteca_bn.py paginas edicao.pdf "TERMO" --json

  extrair   Grava uma pagina isolada (PDF sem perda), a imagem da pagina (PNG), o
            texto OCR e, se pedido, recortes em volta do termo. Os nomes levam o
            nome do PDF de origem, para duas edicoes nao se misturarem na pasta.
            Ex.:  python hemeroteca_bn.py extrair edicao.pdf 2 saida/ --termo "TERMO"

  dpi       Mede a resolucao real das imagens embutidas: decide se vale tentar OCR.
            Ex.:  python hemeroteca_bn.py dpi edicao.pdf

O que e o "bib": o identificador do periodico na BN, 5 a 7 digitos, quase sempre
com um sufixo de bloco de decada na lista (`089842_05`). A lista de edicoes usa o
bib COM sufixo; o PDF usa o bib SEM sufixo. O script trata isso sozinho.

O que este utilitario nao faz, de proposito:
  * nao descobre em que periodicos um termo aparece (a busca global da BN so roda
    no navegador; o bib vem de la, ou do catalogo);
  * nao resolve nem contorna CAPTCHA;
  * nao faz pedidos em paralelo DENTRO de um processo e pausa, com intervalo
    sorteado, entre pedidos da mesma sessao. A coordenacao entre processos
    concorrentes (varios scripts contra o mesmo servidor) e responsabilidade de
    quem os lanca: a carga que o servidor sente e a soma.

--- COBERTURA, LEIA ANTES DE CONFIAR NO RESULTADO -----------------------------
  * A lista de edicoes vem inteira numa resposta (nao ha paginacao). Zero linhas
    COM a tabela presente significa "sem ocorrencia neste bloco" OU "bloco (sufixo)
    inexistente": o servidor responde igual nos dois casos (conferido em
    15/09/2026). Este script diz isso em vez de afirmar ausencia.
  * A busca da BN indexa com um OCR melhor do que o texto embutido no PDF. A lista
    pode apontar uma edicao cujo PDF nao traz o termo em pagina nenhuma; isso e
    resultado, nao erro, e sai como `paginas: []`.
  * OCR nunca e prova. O que for citado tem de ser lido na imagem (o PNG ou o
    recorte que `extrair` grava).

Dependencias:
  pip install -r scripts/requirements.txt -r scripts/requirements-hemeroteca.txt
`requests` (base), `truststore` (obrigatorio para a BN e so existe para Python
3.10+: sem ele o Python nao valida o certificado dos servidores) e PyMuPDF (so
para `paginas`, `extrair` e `dpi`).

Sem credenciais, sem dados pessoais e sem identificadores de familia embutidos:
bib, termo e edicao sao sempre fornecidos na linha de comandos.
"""

import argparse
import email.utils
import glob
import hashlib
import html as _html
import json
import os
import random
import re
import sys
import tempfile
import time
import unicodedata

import requests

LISTA_URL = "https://memoria.bn.gov.br/docreader/ListaPastaOcor.aspx"
LEITOR_URL = "https://memoria.bn.gov.br/DocReader/DocReader.aspx"
PDF_URL = "https://hemeroteca-pdf.bn.gov.br/{bib}/per{bib}_{ano}_{edicao}.pdf"

DEFAULT_TIMEOUT = 120      # segundos SEM DADOS antes de desistir (nao e prazo total)
DEFAULT_DELAY = 4.0        # base da pausa sorteada entre pedidos (ver _pausar)
MAX_RETRIES = 3
# Uma edicao tem 5 a 30 MB. O teto existe porque o timeout do requests mede espera
# por dados, nao duracao: um servidor que nunca pare de mandar bytes ocuparia o
# disco sem nunca disparar o timeout.
MAX_PDF_BYTES = 300 * 1024 * 1024
# Cabecalhos de navegador. O servidor da BN e um ASP.NET antigo; identificar-se
# como navegador e o que ele espera de quem le a lista.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

# Uma linha da tabela de ocorrencias, depois de tirar as tags:
#   "ano 1922\edicao a00165 1"
# A edicao pode ter PREFIXO DE LETRA (edicao extra/vespertina). Um padrao que so
# aceite digitos perde essas edicoes em silencio, e o ficheiro PDF usa o prefixo.
LINHA_RE = re.compile(r"ano\s*(\d{4})\\edicao\s*([a-z]?\d+)\s+(\d+)", re.I)
# Cada edicao vem numa celula com esta classe. Contar as celulas e o que permite
# saber se alguma linha ficou por interpretar, em vez de a descartar em silencio.
CELULA_RE = re.compile(r'class=["\']?listapastasnome', re.I)
# A tabela vem com este cabecalho mesmo quando esta vazia. Sem ele, a resposta
# nao e a pagina esperada (mudanca de estrutura, erro do servidor, bloqueio).
CABECALHO_RE = re.compile(r"PASTA\s+OCORR", re.I)
BIB_RE = re.compile(r"^(\d{5,7})(?:_(\d{1,2}))?$")
EDICAO_RE = re.compile(r"^[a-z]?\d+$", re.I)
PDF_MAGIC = b"%PDF-"


class HemerotecaError(Exception):
    """Erro de uso ou de contrato. Nunca SystemExit: o modulo tem de ser importavel."""


# --------------------------------------------------------------------------- #
# TLS, sessao e ritmo
# --------------------------------------------------------------------------- #
def _ativar_truststore():
    """
    O pacote de certificados que o Python traz (certifi) nao tem a cadeia dos
    servidores da BN: `requests` falha com CERTIFICATE_VERIFY_FAILED nos DOIS
    hosts (verificado em 15/09/2026). O repositorio de certificados do sistema
    operativo tem a cadeia, e `truststore` faz o Python usa-lo. Devolve False se
    o pacote nao estiver instalado (ou o Python for anterior a 3.10, que ele nao
    suporta), para a mensagem de erro dizer o que falta.

    O efeito e GLOBAL ao processo: `inject_into_ssl` substitui o SSLContext padrao,
    e quem importar este modulo como biblioteca passa a validar TLS de todos os
    hosts pelo repositorio do sistema operativo.
    """
    try:
        import truststore
    except ImportError:
        return False
    truststore.inject_into_ssl()
    return True


def _sessao():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT,
                      "Accept": "text/html,application/pdf,*/*;q=0.8",
                      "Accept-Language": "pt-BR,pt;q=0.9"})
    s.hemeroteca_truststore = _ativar_truststore()
    s.hemeroteca_pedidos = 0
    return s


def _pausar(delay):
    """
    Pausa SORTEADA entre pedidos da mesma sessao, entre `delay` e o dobro. Existe
    para reduzir a carga sobre um servidor publico; o sorteio evita o padrao
    regular que os filtros anti-robo procuram. `delay=0` desliga (testes).
    """
    if delay and delay > 0:
        time.sleep(random.uniform(delay, delay * 2))


def _sleep_from_retry_after(resp, fallback):
    """
    Respeita Retry-After em segundos OU em data HTTP (RFC 9110, 10.2.3); a versao
    so com float tratava a data como ausente e voltava antes do prazo pedido.
    """
    valor = (resp.headers.get("Retry-After") or "").strip()
    if not valor:
        return fallback
    try:
        return max(float(valor), fallback)
    except ValueError:
        pass
    try:
        quando = email.utils.parsedate_to_datetime(valor)
        return max(quando.timestamp() - time.time(), fallback)
    except (TypeError, ValueError, OverflowError):
        return fallback


def _get(session, url, delay=DEFAULT_DELAY, stream=False, referer=None):
    """
    GET com pausa entre pedidos da sessao, timeout e retentativa educada em
    429/5xx. Levanta HemerotecaError. Quem chama e responsavel por fechar a
    resposta (`with resp:`), em especial em modo `stream`.
    """
    espera = max(delay, 1.0)
    ultimo = ""
    headers = {"Referer": referer} if referer else None
    for tentativa in range(1, MAX_RETRIES + 1):
        # A primeira versao definia a pausa e nunca a chamava: `--delay` nao
        # fazia nada. A pausa vale a partir do SEGUNDO pedido da sessao.
        if getattr(session, "hemeroteca_pedidos", 0):
            _pausar(delay)
        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT, stream=stream, headers=headers)
        except requests.exceptions.SSLError as exc:
            dica = ("" if getattr(session, "hemeroteca_truststore", True)
                    else " (instale `truststore`, Python 3.10+: o certificado da BN nao e "
                         "validado pelo pacote de certificados do Python)")
            raise HemerotecaError("erro TLS ao contactar %s: %s%s" % (url, exc, dica)) from None
        except requests.exceptions.Timeout:
            ultimo = "tempo esgotado (timeout)"
        except requests.exceptions.RequestException as exc:
            ultimo = "erro de rede: %s" % exc
        else:
            try:
                session.hemeroteca_pedidos += 1
            except (AttributeError, TypeError):
                session.hemeroteca_pedidos = 1
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                ultimo = "HTTP %s" % resp.status_code
                pausa = _sleep_from_retry_after(resp, espera)
                resp.close()
                if tentativa < MAX_RETRIES:
                    time.sleep(pausa)
                    espera *= 2
                    continue
            else:
                return resp
        if tentativa < MAX_RETRIES:
            time.sleep(espera)
            espera *= 2
    raise HemerotecaError("falhou %d vezes ao contactar %s (%s)" % (MAX_RETRIES, url, ultimo))


# --------------------------------------------------------------------------- #
# Identificadores e URLs
# --------------------------------------------------------------------------- #
def validar_bib(bib):
    """Aceita `089842` ou `089842_05`; recusa qualquer outra coisa antes de ir a rede."""
    m = BIB_RE.match(str(bib).strip())
    if not m:
        raise HemerotecaError("bib invalido: %r (esperado 5 a 7 digitos, com ou sem "
                              "sufixo de decada, ex. 089842_05)" % bib)
    return m.group(0)


def bib_base(bib):
    """O bib SEM o sufixo de decada: e o que o servidor de PDF usa."""
    return validar_bib(bib).split("_")[0]


def validar_edicao(edicao):
    e = str(edicao).strip().lower()
    if not EDICAO_RE.match(e):
        raise HemerotecaError("edicao invalida: %r (esperado digitos, com prefixo de "
                              "letra opcional, ex. 00193 ou a00165)" % edicao)
    return e


def url_lista(bib, termo):
    """
    URL da lista de edicoes. O termo vai entre aspas, com o espaco codificado como
    %20, e isso NAO e detalhe: a busca so e por frase exacta com %20. Verificado em
    15/09/2026 no mesmo bloco e termo: `pesq=%22A%20B%22` devolveu 9 edicoes;
    `pesq=%22A+B%22` (que e o que `urlencode` produz) e `pesq=A%20B` (sem aspas)
    devolveram 1451, isto e, qualquer pagina com as duas palavras em qualquer
    lugar. O erro e silencioso: a lista vem maior e parece melhor.
    """
    from urllib.parse import quote
    return "%s?bib=%s&pesq=%%22%s%%22" % (LISTA_URL, validar_bib(bib), quote(termo, safe=""))


def url_pdf(bib, ano, edicao):
    ano = str(ano).strip()
    if not re.match(r"^\d{4}$", ano):
        raise HemerotecaError("ano invalido: %r" % ano)
    return PDF_URL.format(bib=bib_base(bib), ano=ano, edicao=validar_edicao(edicao))


def url_leitor(bib, termo, ano, edicao):
    """
    Link para um HUMANO abrir a edicao no visualizador oficial (com CAPTCHA), no
    formato que a propria pagina da lista monta (`DocReader.aspx?bib=&pesq=&pasta=`).
    Serve para citar a fonte e para conferir na imagem o que o OCR disse.
    """
    from urllib.parse import quote
    pasta = "ano %s\\edicao %s" % (str(ano).strip(), validar_edicao(edicao))
    return "%s?bib=%s&pesq=%s&pasta=%s" % (LEITOR_URL, validar_bib(bib), quote(termo, safe=""),
                                            quote(pasta, safe=""))


# --------------------------------------------------------------------------- #
# Lista de edicoes
# --------------------------------------------------------------------------- #
def analisar_lista(html_bruto):
    """
    HTML da ListaPastaOcor -> lista de {ano, edicao, ocorrencias}, na ordem servida.

    Levanta HemerotecaError se a resposta nao traz a tabela (cabecalho ausente):
    devolver [] nesse caso faria quem chamou concluir "sem ocorrencias" a partir de
    uma pagina de erro. Levanta tambem se ha celulas de edicao que o padrao nao
    interpretou: uma lista parcial devolvida em silencio e o defeito que mais
    custa numa pesquisa. Zero linhas COM cabecalho e um resultado legitimo, mas
    ambiguo (ver `listar_edicoes`).
    """
    bruto = html_bruto or ""
    texto = re.sub(r"<[^>]+>", " ", bruto)
    texto = re.sub(r"\s+", " ", _html.unescape(texto))
    if not CABECALHO_RE.search(texto):
        raise HemerotecaError("a resposta nao traz a tabela de ocorrencias esperada "
                              "(estrutura mudou, bloqueio ou erro do servidor)")
    linhas = LINHA_RE.findall(texto)
    celulas = len(CELULA_RE.findall(bruto))
    if celulas != len(linhas):
        raise HemerotecaError("a tabela tem %d edicoes e o padrao interpretou %d: o formato "
                              "das linhas mudou; nada foi devolvido para nao passar lista "
                              "parcial por completa" % (celulas, len(linhas)))
    return [{"ano": ano, "edicao": ed.lower(), "ocorrencias": int(n)}
            for ano, ed, n in linhas]


def listar_edicoes(session, bib, termo, delay=DEFAULT_DELAY):
    """
    Devolve (edicoes, nota). `nota` e "" quando ha linhas; quando nao ha, explica
    que o servidor nao distingue "termo sem ocorrencia" de "bloco inexistente".
    """
    bib = validar_bib(bib)
    if not str(termo).strip():
        raise HemerotecaError("termo vazio")
    with _get(session, url_lista(bib, termo), delay=delay) as resp:
        if not resp.ok:
            raise HemerotecaError("HTTP %s ao pedir a lista de %s" % (resp.status_code, bib))
        edicoes = analisar_lista(resp.text)
    for e in edicoes:
        e["bib"] = bib
        e["url_pdf"] = url_pdf(bib, e["ano"], e["edicao"])
        e["url_leitor"] = url_leitor(bib, termo, e["ano"], e["edicao"])
    nota = ""
    if not edicoes:
        nota = ("nenhuma edicao: ou o termo nao ocorre neste bloco, ou o bloco %s nao "
                "existe; o servidor responde igual nos dois casos" % bib)
    return edicoes, nota


# --------------------------------------------------------------------------- #
# PDF da edicao
# --------------------------------------------------------------------------- #
def _pdf_integro(caminho):
    """
    Um PDF que chegou inteiro termina em %%EOF (nos ultimos bytes) e, se o PyMuPDF
    estiver instalado, abre com pelo menos uma pagina. `%PDF-` no inicio nao
    basta: um download truncado ou uma pagina de erro com esse prefixo passaria.
    """
    try:
        with open(caminho, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            tamanho = fh.tell()
            fh.seek(max(0, tamanho - 2048))
            cauda = fh.read()
    except OSError:
        return False
    if b"%%EOF" not in cauda:
        return False
    try:
        import fitz
    except ImportError:
        return True
    try:
        with fitz.open(caminho) as doc:
            return len(doc) > 0
    except Exception:  # noqa: BLE001 - qualquer falha de abertura e "nao integro"
        return False


def baixar_edicao(session, bib, ano, edicao, destino, delay=DEFAULT_DELAY, force=False,
                  max_bytes=MAX_PDF_BYTES):
    """
    Baixa o PDF publico de uma edicao para `destino`. Devolve {caminho, bytes, sha256, url}.

    Ordem das defesas, e o que cada uma impede:
      * nada e escrito no destino antes de o corpo comecar por %PDF- E de o ficheiro
        inteiro passar em `_pdf_integro`: o servidor responde 200 com HTML em alguns
        erros, e um corte no meio deixaria um .pdf que nao abre;
      * o download vai para um temporario EXCLUSIVO desta execucao (mkstemp) e so no
        fim e movido para o destino: nem processos concorrentes se atropelam, nem um
        ficheiro bom ja existente e destruido por um download mau, mesmo com `force`;
      * `max_bytes` fecha a porta a um servidor que nao pare de mandar dados.
    Um 404 aqui NAO prova que a edicao nao existe: alguns titulos nao tem PDF
    estatico e so existem no visualizador.
    """
    url = url_pdf(bib, ano, edicao)
    destino = os.path.abspath(destino)
    if os.path.exists(destino) and not force:
        raise HemerotecaError("'%s' ja existe. Use --force para sobrescrever." % destino)

    referer = LEITOR_URL + "?bib=" + validar_bib(bib)
    resp = _get(session, url, delay=delay, stream=True, referer=referer)
    fd = None
    parcial = None
    try:
        if resp.status_code == 404:
            raise HemerotecaError("HTTP 404 em %s: esta edicao nao tem PDF publico (o titulo "
                                  "pode existir so no visualizador com CAPTCHA)" % url)
        if not resp.ok:
            raise HemerotecaError("HTTP %s ao baixar %s" % (resp.status_code, url))
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "html" in ctype:
            raise HemerotecaError("a resposta de %s e HTML, nao PDF. Nada foi gravado." % url)

        pasta = os.path.dirname(destino) or "."
        os.makedirs(pasta, exist_ok=True)
        fd, parcial = tempfile.mkstemp(dir=pasta, prefix=os.path.basename(destino) + ".",
                                       suffix=".part")
        h = hashlib.sha256()
        total = 0
        inicio = b""
        try:
            with os.fdopen(fd, "wb") as fh:
                fd = None
                for pedaco in resp.iter_content(chunk_size=65536):
                    if not pedaco:
                        continue
                    if len(inicio) < len(PDF_MAGIC):
                        # a assinatura pode chegar dividida entre dois pedacos
                        inicio += pedaco[:len(PDF_MAGIC) - len(inicio)]
                        if len(inicio) >= len(PDF_MAGIC) and not inicio.startswith(PDF_MAGIC):
                            raise HemerotecaError(
                                "a resposta de %s nao e um PDF (Content-Type: %s). Nada foi "
                                "gravado no destino." % (url, ctype or "?"))
                    total += len(pedaco)
                    if total > max_bytes:
                        raise HemerotecaError("%s passou de %d bytes; download abandonado"
                                              % (url, max_bytes))
                    fh.write(pedaco)
                    h.update(pedaco)
        except requests.exceptions.RequestException as exc:
            raise HemerotecaError("erro de rede a meio de %s: %s. Nada foi gravado no destino."
                                  % (url, exc)) from None
        if total < len(PDF_MAGIC) or not inicio.startswith(PDF_MAGIC):
            raise HemerotecaError("a resposta de %s veio vazia ou nao e um PDF. Nada foi "
                                  "gravado no destino." % url)
        if not _pdf_integro(parcial):
            raise HemerotecaError("o PDF de %s chegou incompleto ou nao abre (%d bytes). "
                                  "Nada foi gravado no destino." % (url, total))
        if os.path.exists(destino) and not force:
            # apareceu entre a verificacao inicial e agora (outro processo)
            raise HemerotecaError("'%s' passou a existir durante o download; nada foi "
                                  "sobrescrito." % destino)
        try:
            os.replace(parcial, destino)
        except OSError as exc:
            raise HemerotecaError("erro ao gravar '%s': %s" % (destino, exc)) from None
        parcial = None
        return {"caminho": destino, "bytes": total, "sha256": h.hexdigest(), "url": url}
    finally:
        resp.close()
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if parcial and os.path.exists(parcial):
            try:
                os.remove(parcial)
            except OSError:
                pass


# --------------------------------------------------------------------------- #
# Texto: normalizacao e busca dentro do PDF
# --------------------------------------------------------------------------- #
def normalizar(texto):
    """
    Minusculas, sem acento, hifenizacao de fim de linha juntada e quebras viradas
    em espaco. Jornal parte palavra no fim da linha o tempo todo: "Sou-\\nza" tem
    de casar com "souza", e o OCR da BN e insensivel a acento.
    """
    t = (texto or "").replace("-\n", "").replace("\n", " ")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", t.lower())


def _partes_do_termo(termo):
    """Lista de listas: palavras separadas por espaco, cada uma partida nos hifens."""
    return [[p for p in tok.split("-") if p] for tok in normalizar(termo).split()]


def padrao_do_termo(termo):
    """
    Regex que casa o termo no texto normalizado, com espaco ou hifen entre as
    palavras e fronteira de palavra nas pontas: "TERMO" nao casa dentro de
    "termonuclear". OCR que cola letras ao nome escapa a esta busca; e um custo
    aceite, porque a alternativa (substring) enche a lista de falsos.

    Apelido composto com hifen ("Sa-Carneiro") e caso a parte: quando o jornal o
    parte no fim da linha, `normalizar` junta as metades ("sacarneiro"), e a
    primeira versao exigia um separador entre elas e nunca casava. Entre partes
    unidas por hifen no termo o separador e OPCIONAL; entre palavras separadas por
    espaco continua obrigatorio.
    """
    grupos = [r"[\s\-]*".join(re.escape(p) for p in partes)
              for partes in _partes_do_termo(termo) if partes]
    if not grupos:
        raise HemerotecaError("termo vazio")
    return re.compile(r"(?<![a-z0-9])" + r"[\s\-]+".join(grupos) + r"(?![a-z0-9])")


def palavra_distintiva(termo):
    """
    A palavra mais longa do termo, para a segunda tentativa quando o termo inteiro
    nao casa: o OCR quebra nomes ("fra nklin"), e a palavra sozinha ainda acha a
    pagina. Em empate de comprimento vence a ULTIMA, porque num nome o sobrenome
    distingue mais do que o prenome. Nao e sinonimo de "sobrenome": num termo como
    "Alexandre Reis" sai "alexandre". Devolve None com uma palavra so.
    """
    # parte tambem no hifen: "Sa-Carneiro" tem duas palavras, e a segunda e a
    # que serve de plano B
    palavras = [p for partes in _partes_do_termo(termo) for p in partes]
    if len(palavras) < 2:
        return None
    return max(reversed(palavras), key=len)


def _abrir_fitz():
    try:
        import fitz
    except ImportError:
        raise HemerotecaError("PyMuPDF nao instalado: pip install -r "
                              "scripts/requirements-hemeroteca.txt") from None
    return fitz


def _abrir_pdf(fitz, caminho):
    """PDF inexistente ou corrompido e erro de uso (ERRO: ... e exit 1), nao traceback."""
    try:
        return fitz.open(caminho)
    except FileNotFoundError:
        raise HemerotecaError("PDF nao encontrado: %s" % caminho) from None
    except RuntimeError as exc:
        raise HemerotecaError("nao foi possivel abrir %s como PDF: %s" % (caminho, exc)) from None


def paginas_com_termo(caminho_pdf, termo, tentar_distintiva=True, alternativa=None,
                      contexto=200):
    """
    Devolve {termo_usado, paginas:[{pagina, ocorrencias, trecho}], total_paginas}
    usando a camada de texto do PDF (OCR da BN). Se o termo inteiro nao casa em
    pagina nenhuma, repete com `alternativa` (se dada) ou com a palavra mais longa
    (se `tentar_distintiva`), e diz que o fez em `termo_usado`.

    Lista vazia e resultado, nao erro: a busca da BN usa um OCR melhor do que o
    embutido no PDF, e ha edicoes em que o texto embutido nem sequer corresponde a
    imagem. Registe como pendente e confira no visualizador.
    """
    fitz = _abrir_fitz()
    tentativas = [(termo, padrao_do_termo(termo))]
    segunda = alternativa or (palavra_distintiva(termo) if tentar_distintiva else None)
    if segunda and normalizar(segunda) != normalizar(termo):
        tentativas.append((segunda, padrao_do_termo(segunda)))

    with _abrir_pdf(fitz, caminho_pdf) as doc:
        planos = [normalizar(pg.get_text()) for pg in doc]
    for usado, padrao in tentativas:
        achadas = []
        for i, plano in enumerate(planos, 1):
            ms = list(padrao.finditer(plano))
            if not ms:
                continue
            m = ms[0]
            achadas.append({"pagina": i, "ocorrencias": len(ms),
                            "trecho": plano[max(0, m.start() - contexto): m.end() + contexto]})
        if achadas:
            return {"termo_usado": usado, "paginas": achadas, "total_paginas": len(planos)}
    return {"termo_usado": termo, "paginas": [], "total_paginas": len(planos)}


def _caixas_do_termo(pagina, padrao, fitz):
    """
    Uniao das caixas das palavras que formam cada ocorrencia.

    O OCR hifeniza na quebra de LINHA ("Sou-" no fim de uma linha, "za" no inicio
    da seguinte), e `page.search_for` nao junta as duas metades. Aqui a pagina
    vira um fio continuo de palavras, em que uma palavra terminada em hifen so e
    colada a seguinte se a seguinte esta noutra linha (o PyMuPDF da bloco e
    linha de cada palavra); "alfa- beta" na mesma linha continua a ser duas
    palavras. Cada caractere lembra a caixa da palavra de origem.
    """
    fio, donos = "", []
    anterior = None
    for w in pagina.get_text("words"):
        txt = normalizar(w[4])
        if not txt:
            continue
        linha = (w[5], w[6])
        if fio.endswith("-") and anterior is not None and linha != anterior:
            fio, donos = fio[:-1], donos[:-1]
        elif fio:
            fio += " "
            donos.append(None)
        caixa = fitz.Rect(w[:4])
        donos.extend([caixa] * len(txt))
        fio += txt
        anterior = linha
    caixas = []
    for m in padrao.finditer(fio):
        rects = [r for r in donos[m.start():m.end()] if r is not None]
        if rects:
            u = rects[0]
            for r in rects[1:]:
                u = u | r
            caixas.append(u)
    return caixas


def extrair_pagina(caminho_pdf, pagina, pasta, termo=None, largura_png=1700,
                   max_recortes=6, force=False):
    """
    Grava <origem>_pNN.pdf (a pagina, sem perda), <origem>_pNN.png (pagina inteira),
    <origem>_pNN.txt (texto OCR embutido) e, com `termo`, <origem>_pNN_recorteK.png
    em volta de cada ocorrencia. <origem> e o nome do PDF de entrada, para que duas
    edicoes extraidas para a mesma pasta nao se sobreponham. Recusa sobrescrever
    sem `force`.

    Devolve {gravados, ocorrencias, recortes, truncado}: `truncado` e True quando
    havia mais ocorrencias do que `max_recortes`, para a cobertura dos recortes nao
    passar por completa. A imagem e derivado para LEITURA; a afirmacao que sair
    dela tem de citar titulo, data, edicao e pagina.
    """
    fitz = _abrir_fitz()
    n = int(pagina)
    origem = os.path.splitext(os.path.basename(caminho_pdf))[0]
    base = os.path.join(pasta, "%s_p%02d" % (origem, n))
    alvos = [base + ".pdf", base + ".png", base + ".txt"]
    recortes_velhos = sorted(glob.glob(glob.escape(base) + "_recorte*.png"))
    existentes = [a for a in alvos if os.path.exists(a)] + recortes_velhos
    if existentes and not force:
        raise HemerotecaError("ja existe %s; use --force para sobrescrever" % existentes[0])
    # Com force, os recortes da extracao anterior saem ANTES de gravar: senao uma
    # segunda passagem com menos ocorrencias deixava recorte2/recorte3 velhos na
    # pasta, e o "recortes=1" devolvido contradizia os ficheiros.
    for velho in recortes_velhos:
        try:
            os.remove(velho)
        except OSError as exc:
            raise HemerotecaError("nao consegui apagar %s: %s" % (velho, exc)) from None

    gravados = []
    ocorrencias = 0
    with _abrir_pdf(fitz, caminho_pdf) as doc:
        if n < 1 or n > len(doc):
            raise HemerotecaError("pagina %d fora do PDF (1 a %d)" % (n, len(doc)))
        pg = doc[n - 1]
        os.makedirs(pasta, exist_ok=True)

        uma = fitz.open()
        uma.insert_pdf(doc, from_page=n - 1, to_page=n - 1)
        uma.save(base + ".pdf", garbage=3, deflate=True)
        uma.close()
        gravados.append(base + ".pdf")

        # ~100 dpi numa pagina de jornal: legivel e cabe no disco. Pagina de revista
        # muito grande estoura o limite interno do MuPDF; o teto de zoom protege.
        zoom = min(1.5, float(largura_png) / max(pg.rect.width, 1))
        pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(base + ".png")
        gravados.append(base + ".png")

        with open(base + ".txt", "w", encoding="utf-8") as fh:
            fh.write(pg.get_text())
        gravados.append(base + ".txt")

        if termo:
            caixas = _caixas_do_termo(pg, padrao_do_termo(termo), fitz)
            ocorrencias = len(caixas)
            w_, h_ = pg.rect.width, pg.rect.height
            for k, rc in enumerate(caixas[:max_recortes], 1):
                clip = fitz.Rect(rc.x0 - 0.16 * w_, rc.y0 - 0.12 * h_,
                                 rc.x1 + 0.16 * w_, rc.y1 + 0.16 * h_) & pg.rect
                z = min(3.0, 1800.0 / max(clip.width, 1))
                saida = "%s_recorte%d.png" % (base, k)
                pg.get_pixmap(matrix=fitz.Matrix(z, z), clip=clip).save(saida)
                gravados.append(saida)
    recortes = min(ocorrencias, max_recortes)
    return {"gravados": gravados, "ocorrencias": ocorrencias, "recortes": recortes,
            "truncado": ocorrencias > recortes}


def medir_dpi(caminho_pdf, pagina=None):
    """
    Resolucao real das imagens embutidas, por pagina: [{pagina, largura_px, dpi}].
    O dpi sai da largura em pixels da imagem dividida pela largura em polegadas da
    CAIXA em que ela e desenhada na pagina (nao da pagina inteira: uma imagem
    pequena numa pagina grande daria um numero absurdo). Com varias imagens, a
    maior. E o que decide se vale tentar OCR proprio: abaixo de ~200 dpi o OCR
    erra digito e ampliar nao recupera o que nao foi capturado.
    """
    fitz = _abrir_fitz()
    saida = []
    with _abrir_pdf(fitz, caminho_pdf) as doc:
        # `is not None`, nao truthiness: `--pagina 0` tem de cair na validacao de
        # intervalo e falhar, nao medir todas as paginas em silencio
        indices = [int(pagina) - 1] if pagina is not None else range(len(doc))
        for i in indices:
            if i < 0 or i >= len(doc):
                raise HemerotecaError("pagina %d fora do PDF (1 a %d)" % (i + 1, len(doc)))
            pg = doc[i]
            melhor = None
            for img in pg.get_images(full=True):
                rects = pg.get_image_rects(img[0])
                if not rects:
                    continue
                info = doc.extract_image(img[0])
                caixa = max(rects, key=lambda r: r.width * r.height)
                dpi = info["width"] / (max(caixa.width, 1) / 72.0)
                if melhor is None or caixa.width * caixa.height > melhor[2]:
                    melhor = (info["width"], round(dpi), caixa.width * caixa.height)
            if melhor is None:
                saida.append({"pagina": i + 1, "largura_px": None, "dpi": None})
            else:
                saida.append({"pagina": i + 1, "largura_px": melhor[0], "dpi": melhor[1]})
    return saida


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _safe_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover
            pass


def cmd_edicoes(args):
    edicoes, nota = listar_edicoes(_sessao(), args.bib, args.termo, delay=args.delay)
    if args.json:
        print(json.dumps({"bib": validar_bib(args.bib), "termo": args.termo,
                          "edicoes": edicoes, "nota": nota}, ensure_ascii=False, indent=1))
        return
    for e in edicoes:
        print("%s | edicao %-8s | %3d ocorr. | %s" % (e["ano"], e["edicao"], e["ocorrencias"],
                                                     e["url_pdf"]))
    print("%d edicoes com ocorrencia em %s" % (len(edicoes), validar_bib(args.bib)),
          file=sys.stderr)
    if nota:
        print("Nota: " + nota, file=sys.stderr)


def cmd_pdf(args):
    destino = args.saida or "per%s_%s_%s.pdf" % (bib_base(args.bib), args.ano,
                                                validar_edicao(args.edicao))
    r = baixar_edicao(_sessao(), args.bib, args.ano, args.edicao, destino,
                      delay=args.delay, force=args.force)
    print("Gravado: %s (%d bytes, sha256 %s)" % (r["caminho"], r["bytes"], r["sha256"]))


def cmd_paginas(args):
    r = paginas_com_termo(args.pdf, args.termo, tentar_distintiva=not args.so_termo_inteiro,
                          alternativa=args.alternativa)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    if r["termo_usado"] != args.termo:
        print("Termo inteiro nao casou; usada a palavra '%s'." % r["termo_usado"],
              file=sys.stderr)
    for p in r["paginas"]:
        print("pagina %d (%d ocorr.): ...%s..." % (p["pagina"], p["ocorrencias"], p["trecho"]))
    if not r["paginas"]:
        print("Nenhuma pagina com o termo no texto OCR embutido (%d paginas). Isto nao prova "
              "ausencia: confira no visualizador." % r["total_paginas"], file=sys.stderr)


def cmd_extrair(args):
    r = extrair_pagina(args.pdf, args.pagina, args.pasta, termo=args.termo, force=args.force,
                       max_recortes=args.max_recortes)
    for caminho in r["gravados"]:
        print("Gravado: %s" % caminho)
    if args.termo:
        aviso = " (TRUNCADO: ha mais ocorrencias do que recortes)" if r["truncado"] else ""
        print("%d ocorrencia(s) do termo na pagina, %d recorte(s)%s"
              % (r["ocorrencias"], r["recortes"], aviso), file=sys.stderr)


def cmd_dpi(args):
    for m in medir_dpi(args.pdf, args.pagina):
        if m["dpi"] is None:
            print("pagina %d: sem imagem embutida" % m["pagina"])
        else:
            print("pagina %d: %d px de largura, ~%d dpi" % (m["pagina"], m["largura_px"],
                                                            m["dpi"]))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="hemeroteca_bn.py",
        description="Hemeroteca Digital Brasileira (BN): edicoes por termo, PDF da edicao, "
                    "paginas e recortes. Ver o cabecalho do ficheiro para os detalhes.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("edicoes", help="Lista as edicoes de um periodico em que o termo ocorre.")
    p.add_argument("bib", help="Identificador do periodico, com sufixo de decada (ex. 089842_05).")
    p.add_argument("termo", help="Termo de busca (frase exacta; a BN ignora acentos).")
    p.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                   help="Base da pausa sorteada entre pedidos, em segundos (padrao %.1f)."
                        % DEFAULT_DELAY)
    p.add_argument("--json", action="store_true", help="Imprime JSON.")
    p.set_defaults(func=cmd_edicoes)

    p = sub.add_parser("pdf", help="Baixa o PDF publico de uma edicao.")
    p.add_argument("bib", help="Identificador do periodico (com ou sem sufixo).")
    p.add_argument("ano", help="Ano da edicao (AAAA).")
    p.add_argument("edicao", help="Numero da edicao como a lista o da (ex. 00193, a00165).")
    p.add_argument("saida", nargs="?", default=None, help="Ficheiro de saida (.pdf).")
    p.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    p.add_argument("--force", action="store_true", help="Sobrescreve se ja existir.")
    p.set_defaults(func=cmd_pdf)

    p = sub.add_parser("paginas", help="Acha as paginas de um PDF que citam o termo.")
    p.add_argument("pdf", help="PDF da edicao.")
    p.add_argument("termo", help="Termo a procurar.")
    p.add_argument("--alternativa", default=None,
                   help="Palavra a tentar quando o termo inteiro nao casa (em vez da mais longa).")
    p.add_argument("--so-termo-inteiro", action="store_true",
                   help="Nao tentar segunda palavra quando o termo inteiro nao casa.")
    p.add_argument("--json", action="store_true", help="Imprime JSON.")
    p.set_defaults(func=cmd_paginas)

    p = sub.add_parser("extrair", help="Grava pagina isolada, PNG, texto e recortes.")
    p.add_argument("pdf", help="PDF da edicao.")
    p.add_argument("pagina", type=int, help="Numero da pagina (1 = primeira).")
    p.add_argument("pasta", help="Pasta de saida.")
    p.add_argument("--termo", default=None, help="Termo para os recortes em volta.")
    p.add_argument("--max-recortes", type=int, default=6, help="Teto de recortes (padrao 6).")
    p.add_argument("--force", action="store_true", help="Sobrescreve ficheiros existentes.")
    p.set_defaults(func=cmd_extrair)

    p = sub.add_parser("dpi", help="Mede a resolucao real das imagens embutidas.")
    p.add_argument("pdf", help="PDF da edicao.")
    p.add_argument("--pagina", type=int, default=None, help="So esta pagina.")
    p.set_defaults(func=cmd_dpi)
    return parser


def main(argv=None):
    _safe_stdout()
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except HemerotecaError as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        print("Interrompido.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
