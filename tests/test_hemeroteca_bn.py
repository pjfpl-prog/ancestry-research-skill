"""Testes do utilitario da Hemeroteca Digital Brasileira (BN).

Nenhum destes testes toca na rede. A resposta da lista de edicoes e uma CAPTURA
REAL do servidor (15/09/2026, bloco 103730_05 da Gazeta de Noticias, termo "Rui
Barbosa", figura publica morta em 1923, sem ligacao a familia alguma; o
CONTRIBUTING.md admite a excecao e pede o motivo, que e este: a fixture tem de
ser resposta real, e resposta real exige um termo que exista no acervo), reduzida
ao esqueleto de HTML que importa. Os PDFs de teste sao gerados em memoria.

O que estes testes NAO provam, dito aqui de proposito: que o servidor da BN
continua a servir a lista neste formato e o PDF neste endereco. Isso e o
tests/test_hemeroteca_bn_live.py, que corre a mao (HEMEROTECA_BN_LIVE=1).
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hemeroteca_bn as hb  # noqa: E402

try:
    import fitz
except ImportError:  # pragma: no cover - so os testes de PDF dependem dele
    fitz = None

precisa_fitz = pytest.mark.skipif(fitz is None, reason="PyMuPDF nao instalado")

# Esqueleto fiel da resposta real: cabecalho em dois <span>, uma <table> por
# edicao, o texto "ano AAAA\edicao NNNNN" fora da tag <a>, contagem num <span>.
# A terceira linha tem PREFIXO DE LETRA na edicao, como veio do servidor.
_CABECALHO = """
<input type="hidden" name="bibhid" id="bibhid" value="103730_05" />
<div id="listapastastitdiv"><div class="left"><span id="listapastastitnomelbl">PASTA</span></div>
<div class="right"><span id="listapastastitocorlbl">OCORR&#202;NCIAS</span></div></div>
<div id="listapastasconteudodiv">
"""
_LINHA = """<table id="listapastasitemdiv" width="100%%"><tr><td class="listapastasnome">
<a onclick='javascript:AbreDrd("ano %(ano)s\\\\edicao %(ed)s")'/>ano %(ano)s\\edicao %(ed)s
</td><td class="listapastasocor"><span>%(n)s</span></td></tr></table>
"""
_RODAPE = "</div>"

LINHAS_REAIS = [("1921", "00193", 1), ("1922", "00017", 1), ("1922", "a00165", 1),
                ("1923", "00082", 1), ("1924", "00239", 1), ("1925", "00260", 1),
                ("1925", "00274", 1), ("1926", "00123", 1), ("1928", "00146", 1)]


def html_lista(linhas=LINHAS_REAIS, com_cabecalho=True):
    corpo = "".join(_LINHA % {"ano": a, "ed": e, "n": n} for a, e, n in linhas)
    return (_CABECALHO if com_cabecalho else "") + corpo + _RODAPE


class _Resp:
    """Resposta falsa com o pouco que o cliente usa. Serve tambem como gestor de contexto."""

    def __init__(self, status=200, corpo=b"", ctype="text/html", headers=None):
        self.status_code = status
        self.ok = 200 <= status < 300
        self.headers = {"Content-Type": ctype}
        self.headers.update(headers or {})
        self._corpo = corpo
        self.fechada = False

    @property
    def text(self):
        return self._corpo.decode("utf-8", "replace")

    def iter_content(self, chunk_size=65536):
        for i in range(0, len(self._corpo), chunk_size):
            yield self._corpo[i:i + chunk_size]

    def close(self):
        self.fechada = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _resp_lista(linhas=LINHAS_REAIS):
    return _Resp(200, html_lista(linhas).encode("utf-8"))


# --------------------------------------------------------------------------- #
# Lista de edicoes
# --------------------------------------------------------------------------- #
def test_analisar_lista_le_as_nove_edicoes_reais():
    eds = hb.analisar_lista(html_lista())
    assert [(e["ano"], e["edicao"], e["ocorrencias"]) for e in eds] == LINHAS_REAIS


def test_edicao_com_prefixo_de_letra_nao_se_perde():
    """Um padrao so de digitos perderia a edicao `a00165` em silencio."""
    eds = hb.analisar_lista(html_lista([("1922", "a00165", 2)]))
    assert eds == [{"ano": "1922", "edicao": "a00165", "ocorrencias": 2}]


def test_lista_vazia_com_cabecalho_e_resultado_legitimo():
    assert hb.analisar_lista(html_lista([])) == []


def test_resposta_sem_cabecalho_e_erro_nao_lista_vazia():
    """Pagina de erro ou estrutura nova nao pode virar 'sem ocorrencias'."""
    with pytest.raises(hb.HemerotecaError):
        hb.analisar_lista(html_lista([("1921", "00193", 1)], com_cabecalho=False))
    with pytest.raises(hb.HemerotecaError):
        hb.analisar_lista("<html><body>Erro do servidor</body></html>")


def test_linha_que_o_padrao_nao_interpreta_e_erro_nao_lista_parcial():
    """
    Duas celulas de edicao, uma num formato novo: devolver so a outra passaria
    lista parcial por completa. Tem de levantar.
    """
    # concatena ANTES do rodape em vez de .replace(_RODAPE, ...): o cabecalho tambem
    # tem </div>, e substitui-los todos meteria a celula nova entre PASTA e OCORRENCIAS
    base = html_lista([("1921", "00193", 1)])
    extra = ('<table><tr><td class="listapastasnome">volume 1922 / n. 17</td>'
             '<td class="listapastasocor"><span>1</span></td></tr></table>')
    html = base[:-len(_RODAPE)] + extra + _RODAPE
    with pytest.raises(hb.HemerotecaError) as exc:
        hb.analisar_lista(html)
    assert "2 edicoes" in str(exc.value) and "interpretou 1" in str(exc.value)


def test_listar_edicoes_monta_urls_e_nota(monkeypatch):
    pedidos = []

    def fake_get(session, url, delay=0, stream=False, referer=None):
        pedidos.append(url)
        return _resp_lista()

    monkeypatch.setattr(hb, "_get", fake_get)
    eds, nota = hb.listar_edicoes(None, "103730_05", "Rui Barbosa", delay=0)
    assert nota == ""
    assert len(eds) == 9
    assert eds[2]["url_pdf"] == "https://hemeroteca-pdf.bn.gov.br/103730/per103730_1922_a00165.pdf"
    assert eds[0]["bib"] == "103730_05"
    assert "DocReader.aspx?bib=103730_05" in eds[0]["url_leitor"]
    assert "pasta=ano%201921%5Cedicao%2000193" in eds[0]["url_leitor"]
    assert pedidos == [hb.url_lista("103730_05", "Rui Barbosa")]


def test_listar_edicoes_vazia_explica_a_ambiguidade(monkeypatch):
    monkeypatch.setattr(hb, "_get", lambda *a, **k: _resp_lista([]))
    eds, nota = hb.listar_edicoes(None, "103730_99", "TERMO", delay=0)
    assert eds == []
    assert "nao existe" in nota and "nao ocorre" in nota


def test_url_lista_codifica_o_espaco_como_pct20_e_nao_mais():
    """
    Verificado em 15/09/2026: com `+` no lugar do espaco (o que `urlencode` faz), a
    BN deixa de procurar a FRASE e devolve toda pagina com as duas palavras
    (9 edicoes viraram 1451). O erro e silencioso; este teste e a unica trava.
    """
    url = hb.url_lista("103730_05", "Rui Barbosa")
    assert url == ("https://memoria.bn.gov.br/docreader/ListaPastaOcor.aspx"
                   "?bib=103730_05&pesq=%22Rui%20Barbosa%22")
    assert "+" not in url


@pytest.mark.parametrize("bib", ["089842", "089842_05", "1234567_1"])
def test_bib_valido(bib):
    assert hb.validar_bib(bib) == bib
    assert hb.bib_base(bib) == bib.split("_")[0]


@pytest.mark.parametrize("bib", ["", "abc", "089842_", "089842-05", "1234", "089842_005"])
def test_bib_invalido_e_recusado_antes_da_rede(bib):
    with pytest.raises(hb.HemerotecaError):
        hb.validar_bib(bib)


def test_url_pdf_usa_o_bib_sem_sufixo_e_preserva_o_prefixo_da_edicao():
    assert hb.url_pdf("089842_05", "1940", "13904") == \
        "https://hemeroteca-pdf.bn.gov.br/089842/per089842_1940_13904.pdf"
    assert hb.url_pdf("103730_05", 1922, "A00165").endswith("per103730_1922_a00165.pdf")
    with pytest.raises(hb.HemerotecaError):
        hb.url_pdf("103730", "22", "00001")
    with pytest.raises(hb.HemerotecaError):
        hb.url_pdf("103730", "1922", "00 1")


# --------------------------------------------------------------------------- #
# _get: ritmo, retentativa, TLS
# --------------------------------------------------------------------------- #
class _SessaoFalsa:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []
        self.hemeroteca_pedidos = 0
        self.hemeroteca_truststore = True

    def get(self, url, timeout=None, stream=False, headers=None):
        self.chamadas.append((url, timeout, stream, headers))
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def relogio(monkeypatch):
    """Regista as pausas em vez de dormir; o sorteio devolve sempre o minimo."""
    pausas = []
    monkeypatch.setattr(hb.time, "sleep", lambda s: pausas.append(round(s, 3)))
    monkeypatch.setattr(hb.random, "uniform", lambda a, b: a)
    return pausas


def test_pausa_so_a_partir_do_segundo_pedido_da_sessao(relogio):
    """
    A primeira versao definia `_pausar` e nunca a chamava: `--delay` era decorativo.
    O primeiro pedido sai sem espera; do segundo em diante espera entre delay e 2x.
    """
    s = _SessaoFalsa([_Resp(200, b"a"), _Resp(200, b"b"), _Resp(200, b"c")])
    for _ in range(3):
        hb._get(s, "https://x/", delay=4.0)
    assert relogio == [4.0, 4.0]
    assert s.hemeroteca_pedidos == 3


def test_delay_zero_nao_dorme(relogio):
    s = _SessaoFalsa([_Resp(200, b"a"), _Resp(200, b"b")])
    hb._get(s, "https://x/", delay=0)
    hb._get(s, "https://x/", delay=0)
    assert relogio == []


def test_429_respeita_retry_after_em_segundos_e_fecha_a_resposta(relogio):
    r429 = _Resp(429, b"", headers={"Retry-After": "7"})
    s = _SessaoFalsa([r429, _Resp(200, b"ok")])
    resp = hb._get(s, "https://x/", delay=1.0)
    assert resp.status_code == 200
    assert r429.fechada, "resposta descartada tem de ser fechada"
    assert 7.0 in relogio


def test_retry_after_em_data_http_e_respeitado(monkeypatch):
    """
    So `float()` tratava a data HTTP como ausente e voltava antes do prazo
    pedido pelo servidor (RFC 9110, 10.2.3).
    """
    import email.utils
    agora = 1_700_000_000.0
    monkeypatch.setattr(hb.time, "time", lambda: agora)
    quando = email.utils.formatdate(agora + 30, usegmt=True)
    r = _Resp(429, b"", headers={"Retry-After": quando})
    assert 29.0 <= hb._sleep_from_retry_after(r, 1.0) <= 30.0
    assert hb._sleep_from_retry_after(_Resp(429, b"", headers={"Retry-After": "lixo"}), 2.5) == 2.5


def test_esgota_as_tentativas_e_levanta(relogio):
    s = _SessaoFalsa([_Resp(503, b"")] * hb.MAX_RETRIES)
    with pytest.raises(hb.HemerotecaError) as exc:
        hb._get(s, "https://x/", delay=1.0)
    assert "HTTP 503" in str(exc.value)
    assert len(s.chamadas) == hb.MAX_RETRIES


def test_erro_tls_sem_truststore_diz_o_que_falta(relogio):
    s = _SessaoFalsa([requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED")])
    s.hemeroteca_truststore = False
    with pytest.raises(hb.HemerotecaError) as exc:
        hb._get(s, "https://x/", delay=0)
    assert "truststore" in str(exc.value)


def test_get_manda_referer_e_timeout(relogio):
    s = _SessaoFalsa([_Resp(200, b"a")])
    hb._get(s, "https://x/", delay=0, referer="https://r/")
    url, timeout, stream, headers = s.chamadas[0]
    assert timeout == hb.DEFAULT_TIMEOUT and headers == {"Referer": "https://r/"}


# --------------------------------------------------------------------------- #
# Download do PDF
# --------------------------------------------------------------------------- #
def pdf_bytes(paginas=("uma pagina",)):
    """PDF valido gerado em memoria: nada vem de arquivo real."""
    if fitz is None:
        pytest.skip("PyMuPDF nao instalado")
    doc = fitz.open()
    for texto in paginas:
        pg = doc.new_page(width=400, height=300)
        pg.insert_text((40, 60), texto, fontsize=12)
    dados = doc.tobytes()
    doc.close()
    return dados


def _baixar(monkeypatch, tmp_path, resp, force=False, nome="ed.pdf"):
    monkeypatch.setattr(hb, "_get", lambda *a, **k: resp)
    destino = tmp_path / nome
    r = hb.baixar_edicao(None, "103730_05", "1921", "00193", str(destino), delay=0, force=force)
    return destino, r


def _sem_restos(tmp_path):
    return [p.name for p in tmp_path.iterdir() if ".part" in p.name] == []


@precisa_fitz
def test_baixar_grava_pdf_valido_e_devolve_sha256(monkeypatch, tmp_path):
    corpo = pdf_bytes()
    resp = _Resp(200, corpo, "application/pdf")
    destino, r = _baixar(monkeypatch, tmp_path, resp)
    assert destino.read_bytes() == corpo
    assert r["bytes"] == len(corpo)
    assert r["sha256"] == hashlib.sha256(corpo).hexdigest()
    assert r["url"].endswith("/103730/per103730_1921_00193.pdf")
    assert resp.fechada and _sem_restos(tmp_path)


@precisa_fitz
def test_baixar_recusa_pdf_truncado(monkeypatch, tmp_path):
    """
    `%PDF-` no inicio nao basta: um download cortado a meio tem o prefixo certo e
    nao abre. Nada pode chegar ao destino.
    """
    corpo = pdf_bytes()[:-200]
    with pytest.raises(hb.HemerotecaError) as exc:
        _baixar(monkeypatch, tmp_path, _Resp(200, corpo, "application/pdf"))
    assert "incompleto" in str(exc.value)
    assert not (tmp_path / "ed.pdf").exists() and _sem_restos(tmp_path)


def test_baixar_recusa_content_type_html_mesmo_com_prefixo_pdf(monkeypatch, tmp_path):
    """Cada guarda sozinha: aqui o MIME e HTML, mas o corpo comeca por %PDF-."""
    corpo = b"%PDF-1.4\n%%EOF"
    with pytest.raises(hb.HemerotecaError):
        _baixar(monkeypatch, tmp_path, _Resp(200, corpo, "text/html"))
    assert not (tmp_path / "ed.pdf").exists() and _sem_restos(tmp_path)


def test_baixar_recusa_corpo_sem_assinatura_mesmo_com_mime_pdf(monkeypatch, tmp_path):
    """E aqui o MIME diz PDF, mas o corpo e uma pagina de erro."""
    with pytest.raises(hb.HemerotecaError):
        _baixar(monkeypatch, tmp_path, _Resp(200, b"<html>erro</html>", "application/pdf"))
    assert not (tmp_path / "ed.pdf").exists() and _sem_restos(tmp_path)


def test_assinatura_dividida_entre_dois_pedacos_e_aceite(monkeypatch, tmp_path):
    """A rede entrega em pedacos arbitrarios; `%PD` num e `F-...` no outro e PDF."""
    corpo = b"%PDF-1.4\n" + b"x" * 100 + b"\n%%EOF\n"
    monkeypatch.setattr(hb, "_pdf_integro", lambda caminho: True)

    class _Picada(_Resp):
        def iter_content(self, chunk_size=65536):
            yield self._corpo[:3]
            yield self._corpo[3:]

    destino, r = _baixar(monkeypatch, tmp_path, _Picada(200, corpo, "application/pdf"))
    assert destino.read_bytes() == corpo


@precisa_fitz
def test_force_com_download_mau_preserva_o_ficheiro_bom(monkeypatch, tmp_path):
    """
    O temporario exclusivo e a publicacao no fim existem para isto: `--force` nao
    pode trocar um PDF bom por lixo.
    """
    bom = pdf_bytes(("boa",))
    destino = tmp_path / "ed.pdf"
    destino.write_bytes(bom)
    with pytest.raises(hb.HemerotecaError):
        _baixar(monkeypatch, tmp_path, _Resp(200, b"<html>erro</html>", "application/pdf"),
                force=True)
    assert destino.read_bytes() == bom and _sem_restos(tmp_path)


@precisa_fitz
def test_force_com_download_bom_substitui(monkeypatch, tmp_path):
    destino = tmp_path / "ed.pdf"
    destino.write_bytes(b"%PDF-antigo")
    novo = pdf_bytes(("nova",))
    _baixar(monkeypatch, tmp_path, _Resp(200, novo, "application/pdf"), force=True)
    assert destino.read_bytes() == novo


def test_baixar_recusa_sobrescrever_sem_force_antes_de_ir_a_rede(monkeypatch, tmp_path):
    destino = tmp_path / "ed.pdf"
    destino.write_bytes(b"%PDF-bom")
    chamadas = []
    monkeypatch.setattr(hb, "_get", lambda *a, **k: chamadas.append(1))
    with pytest.raises(hb.HemerotecaError):
        hb.baixar_edicao(None, "103730", "1921", "00193", str(destino), delay=0)
    assert chamadas == [] and destino.read_bytes() == b"%PDF-bom"


def test_baixar_404_diz_que_nao_prova_ausencia(monkeypatch, tmp_path):
    resp = _Resp(404, b"", "text/html")
    with pytest.raises(hb.HemerotecaError) as exc:
        _baixar(monkeypatch, tmp_path, resp)
    assert "404" in str(exc.value) and "visualizador" in str(exc.value)
    assert resp.fechada


def test_baixar_abandona_acima_do_teto_de_bytes(monkeypatch, tmp_path):
    corpo = b"%PDF-1.4\n" + b"x" * 5000
    monkeypatch.setattr(hb, "_get", lambda *a, **k: _Resp(200, corpo, "application/pdf"))
    with pytest.raises(hb.HemerotecaError) as exc:
        hb.baixar_edicao(None, "103730", "1921", "00193", str(tmp_path / "ed.pdf"), delay=0,
                         max_bytes=1000)
    assert "passou de 1000" in str(exc.value)
    assert not (tmp_path / "ed.pdf").exists() and _sem_restos(tmp_path)


def test_erro_de_rede_a_meio_nao_deixa_nada(monkeypatch, tmp_path):
    class _Cai(_Resp):
        def iter_content(self, chunk_size=65536):
            yield b"%PDF-1.4\n"
            raise requests.exceptions.ConnectionError("caiu")

    with pytest.raises(hb.HemerotecaError) as exc:
        _baixar(monkeypatch, tmp_path, _Cai(200, b"", "application/pdf"))
    assert "erro de rede" in str(exc.value)
    assert not (tmp_path / "ed.pdf").exists() and _sem_restos(tmp_path)


# --------------------------------------------------------------------------- #
# Texto e paginas
# --------------------------------------------------------------------------- #
def test_normalizar_junta_hifenizacao_tira_acento_e_baixa_caixa():
    entrada = "João de Sou-\nza foi\na Lisboa, Coimbra e Braçaão ÉVORA"
    assert hb.normalizar(entrada) == "joao de souza foi a lisboa, coimbra e bracaao evora"


def test_padrao_do_termo_tolera_hifen_e_espaco_e_exige_fronteira():
    p = hb.padrao_do_termo("Maria Souza")
    assert p.search("... maria-souza ...") and p.search("maria   souza")
    assert not p.search("mariasouza")
    assert not p.search("amaria souza"), "fronteira no inicio"
    assert not p.search("maria souzas"), "fronteira no fim"
    assert hb.padrao_do_termo("termo").search("o termo dado") is not None
    assert hb.padrao_do_termo("termo").search("termonuclear") is None


def test_apelido_composto_com_hifen_casa_partido_no_fim_da_linha():
    """
    "Sa-\nCarneiro" normaliza para "sacarneiro"; a primeira versao exigia um
    separador entre as duas partes e nunca casava (falso negativo em silencio,
    numa classe de apelidos comum). Entre partes unidas por hifen o separador e
    opcional; entre palavras separadas por espaco continua obrigatorio.
    """
    p = hb.padrao_do_termo("Sa-Carneiro")
    assert p.search(hb.normalizar("o sr. Sa-\nCarneiro disse"))
    assert p.search("o sr. sa-carneiro disse") and p.search("o sr. sa carneiro disse")
    assert not p.search("asacarneiro")
    assert hb.palavra_distintiva("Sa-Carneiro") == "carneiro"
    assert not hb.padrao_do_termo("Maria Souza").search("mariasouza"), "espaco continua a exigir"


def test_palavra_distintiva_e_a_mais_longa_e_em_empate_a_ultima():
    assert hb.palavra_distintiva("Rui Barbosa") == "barbosa"
    # "maria" e "souza" empatam em comprimento: tem de sair a ultima, nao a primeira
    assert hb.palavra_distintiva("Maria Souza") == "souza"
    # nao e "o sobrenome": a mais longa pode ser o prenome, e a documentacao diz isso
    assert hb.palavra_distintiva("Alexandre Reis") == "alexandre"
    assert hb.palavra_distintiva("Barbosa") is None


def pdf_de_teste(tmp_path, paginas, nome="teste.pdf"):
    """PDF com uma pagina por texto (lista = varias linhas), gerado em memoria."""
    doc = fitz.open()
    for texto in paginas:
        pg = doc.new_page(width=400, height=300)
        linhas = texto if isinstance(texto, (list, tuple)) else [texto]
        for k, linha in enumerate(linhas):
            pg.insert_text((40, 60 + 20 * k), linha, fontsize=12)
    caminho = tmp_path / nome
    doc.save(str(caminho))
    doc.close()
    return str(caminho)


@precisa_fitz
def test_paginas_com_termo_acha_a_pagina_certa_e_so_ela(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["nada aqui", "a casa de Maria Souza em Braga", "outra"])
    r = hb.paginas_com_termo(pdf, "Maria Souza")
    assert r["termo_usado"] == "Maria Souza"
    assert [p["pagina"] for p in r["paginas"]] == [2]
    assert r["paginas"][0]["ocorrencias"] == 1
    assert "maria souza" in r["paginas"][0]["trecho"]
    assert r["total_paginas"] == 3


@precisa_fitz
def test_paginas_com_termo_junta_a_hifenizacao_de_fim_de_linha(tmp_path):
    pdf = pdf_de_teste(tmp_path, [["a casa de Maria Sou-", "za em Braga"]])
    r = hb.paginas_com_termo(pdf, "Maria Souza")
    assert [p["pagina"] for p in r["paginas"]] == [1]


@precisa_fitz
def test_paginas_com_termo_cai_para_a_palavra_distintiva_e_diz_que_caiu(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["nada", "chegou a senhora Souza ontem"])
    r = hb.paginas_com_termo(pdf, "Maria Souza")
    assert r["termo_usado"] == "souza"
    assert [p["pagina"] for p in r["paginas"]] == [2]
    r2 = hb.paginas_com_termo(pdf, "Maria Souza", tentar_distintiva=False)
    assert r2["paginas"] == [] and r2["termo_usado"] == "Maria Souza"


@precisa_fitz
def test_alternativa_explicita_vence_a_heuristica(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["chegou o senhor Reis ontem"])
    assert hb.paginas_com_termo(pdf, "Alexandre Reis")["paginas"] == []
    r = hb.paginas_com_termo(pdf, "Alexandre Reis", alternativa="Reis")
    assert r["termo_usado"] == "Reis" and [p["pagina"] for p in r["paginas"]] == [1]


@precisa_fitz
def test_paginas_vazias_sao_resultado_nao_erro(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["texto sem o nome"])
    r = hb.paginas_com_termo(pdf, "Maria Souza")
    assert r["paginas"] == [] and r["total_paginas"] == 1


@precisa_fitz
def test_extrair_pagina_grava_com_o_nome_da_origem_e_conta_recortes(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["primeira", "a casa de Maria Souza em Braga"], "ed1.pdf")
    saida = tmp_path / "saida"
    r = hb.extrair_pagina(pdf, 2, str(saida), termo="Maria Souza")
    nomes = sorted(Path(g).name for g in r["gravados"])
    assert nomes == ["ed1_p02.pdf", "ed1_p02.png", "ed1_p02.txt", "ed1_p02_recorte1.png"]
    assert r["ocorrencias"] == 1 and r["recortes"] == 1 and r["truncado"] is False
    assert (saida / "ed1_p02.png").stat().st_size > 0
    assert "Maria Souza" in (saida / "ed1_p02.txt").read_text(encoding="utf-8")
    with fitz.open(str(saida / "ed1_p02.pdf")) as um:
        assert len(um) == 1


@precisa_fitz
def test_extrair_duas_edicoes_na_mesma_pasta_nao_se_sobrepoe(tmp_path):
    a = pdf_de_teste(tmp_path, ["edicao A"], "edA.pdf")
    b = pdf_de_teste(tmp_path, ["edicao B"], "edB.pdf")
    saida = tmp_path / "saida"
    hb.extrair_pagina(a, 1, str(saida))
    hb.extrair_pagina(b, 1, str(saida))
    assert "edicao A" in (saida / "edA_p01.txt").read_text(encoding="utf-8")
    assert "edicao B" in (saida / "edB_p01.txt").read_text(encoding="utf-8")


@precisa_fitz
def test_extrair_recusa_sobrescrever_sem_force(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["so uma"])
    saida = tmp_path / "saida"
    hb.extrair_pagina(pdf, 1, str(saida))
    with pytest.raises(hb.HemerotecaError):
        hb.extrair_pagina(pdf, 1, str(saida))
    hb.extrair_pagina(pdf, 1, str(saida), force=True)


@precisa_fitz
def test_apelido_com_hifen_partido_acha_pagina_e_recorte(tmp_path):
    pdf = pdf_de_teste(tmp_path, [["falou o deputado Sa-", "Carneiro na sessao"]])
    r = hb.paginas_com_termo(pdf, "Sa-Carneiro")
    assert r["termo_usado"] == "Sa-Carneiro" and [p["pagina"] for p in r["paginas"]] == [1]
    with fitz.open(pdf) as doc:
        assert len(hb._caixas_do_termo(doc[0], hb.padrao_do_termo("Sa-Carneiro"), fitz)) == 1


@precisa_fitz
def test_force_apaga_recortes_da_extracao_anterior(tmp_path):
    """Segunda passagem com menos ocorrencias nao pode deixar recorte2/recorte3 velhos."""
    pdf = pdf_de_teste(tmp_path, [["Souza um", "Souza dois", "Souza tres"]])
    saida = tmp_path / "s"
    hb.extrair_pagina(pdf, 1, str(saida), termo="Souza")
    assert len(list(saida.glob("*_recorte*.png"))) == 3
    with pytest.raises(hb.HemerotecaError):
        hb.extrair_pagina(pdf, 1, str(saida), termo="dois"), "recorte existente conta"
    r = hb.extrair_pagina(pdf, 1, str(saida), termo="dois", force=True)
    assert r["recortes"] == 1
    assert sorted(p.name for p in saida.glob("*_recorte*.png")) == ["teste_p01_recorte1.png"]


@precisa_fitz
def test_pdf_inexistente_ou_corrompido_e_erro_de_uso(tmp_path):
    with pytest.raises(hb.HemerotecaError):
        hb.paginas_com_termo(str(tmp_path / "nao_existe.pdf"), "x")
    lixo = tmp_path / "lixo.pdf"
    lixo.write_bytes(b"isto nao e um pdf")
    with pytest.raises(hb.HemerotecaError):
        hb.medir_dpi(str(lixo))


@precisa_fitz
def test_medir_dpi_pagina_zero_e_erro_nao_todas(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["a", "b"])
    with pytest.raises(hb.HemerotecaError):
        hb.medir_dpi(pdf, 0)
    assert len(hb.medir_dpi(pdf)) == 2


@precisa_fitz
def test_extrair_declara_truncamento_dos_recortes(tmp_path):
    pdf = pdf_de_teste(tmp_path, [["Souza um", "Souza dois", "Souza tres"]])
    r = hb.extrair_pagina(pdf, 1, str(tmp_path / "s"), termo="Souza", max_recortes=2)
    assert r["ocorrencias"] == 3 and r["recortes"] == 2 and r["truncado"] is True
    assert sum(1 for g in r["gravados"] if "recorte" in g) == 2


@precisa_fitz
def test_recorte_junta_hifen_so_entre_linhas_diferentes(tmp_path):
    """
    "Sou-" no fim de uma linha e "za" na seguinte e UMA palavra; "alfa- beta" na
    mesma linha sao duas. A primeira versao colava as duas situacoes.
    """
    pdf = pdf_de_teste(tmp_path, [["a casa de Maria Sou-", "za em Braga e alfa- beta"]])
    with fitz.open(pdf) as doc:
        pg = doc[0]
        assert len(hb._caixas_do_termo(pg, hb.padrao_do_termo("Maria Souza"), fitz)) == 1
        assert hb._caixas_do_termo(pg, hb.padrao_do_termo("alfabeta"), fitz) == []
        assert len(hb._caixas_do_termo(pg, hb.padrao_do_termo("alfa beta"), fitz)) == 1


@precisa_fitz
def test_extrair_pagina_fora_do_pdf_e_erro(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["so uma"])
    with pytest.raises(hb.HemerotecaError):
        hb.extrair_pagina(pdf, 2, str(tmp_path / "s"))


@precisa_fitz
def test_medir_dpi_sem_imagem_embutida_devolve_none(tmp_path):
    pdf = pdf_de_teste(tmp_path, ["texto vetorial, sem imagem"])
    assert hb.medir_dpi(pdf) == [{"pagina": 1, "largura_px": None, "dpi": None}]


@precisa_fitz
def test_medir_dpi_usa_a_caixa_da_imagem_e_nao_a_pagina(tmp_path):
    """
    Imagem de 200 px desenhada numa caixa de 100 pt (1,39 pol) = 144 dpi. Pela
    largura da pagina (400 pt) sairiam 36 dpi, um numero absurdo.
    """
    doc = fitz.open()
    pg = doc.new_page(width=400, height=300)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 100))
    pix.clear_with(200)
    pg.insert_image(fitz.Rect(50, 50, 150, 100), pixmap=pix)
    caminho = tmp_path / "img.pdf"
    doc.save(str(caminho))
    doc.close()
    [m] = hb.medir_dpi(str(caminho))
    assert m["largura_px"] == 200 and m["dpi"] == 144


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_devolve_1_em_erro_de_uso(capsys):
    assert hb.main(["pdf", "bib-invalido", "1921", "00193"]) == 1
    assert "ERRO" in capsys.readouterr().err


def test_cli_edicoes_json(monkeypatch, capsys):
    monkeypatch.setattr(hb, "_get", lambda *a, **k: _resp_lista())
    monkeypatch.setattr(hb, "_sessao", lambda: None)
    assert hb.main(["edicoes", "103730_05", "Rui Barbosa", "--json", "--delay", "0"]) == 0
    saida = json.loads(capsys.readouterr().out)
    assert saida["bib"] == "103730_05" and len(saida["edicoes"]) == 9 and saida["nota"] == ""


@precisa_fitz
def test_cli_extrair_avisa_truncamento(tmp_path, capsys):
    pdf = pdf_de_teste(tmp_path, [["Souza um", "Souza dois"]])
    rc = hb.main(["extrair", pdf, "1", str(tmp_path / "s"), "--termo", "Souza",
                  "--max-recortes", "1"])
    assert rc == 0
    assert "TRUNCADO" in capsys.readouterr().err
