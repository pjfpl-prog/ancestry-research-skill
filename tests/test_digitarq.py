"""Testes do cliente do DigitArq.

Nenhum destes testes toca na rede: `_get_json` e substituido por uma funcao que
devolve paginas sinteticas e REGISTA os parametros enviados. Isso verifica o que
o cliente FAZ (que parametros manda, como agrega, quando para), nao o que o
servidor responde.

O que estes testes NAO provam, e convem ser explicito: que o servidor do ANTT
aceita `fromIndex`/`sortField`. Isso foi verificado a mao contra a API real em
07/09/2026 e esta documentado em references/01. Se o ANTT mudar o contrato, estes
testes continuam verdes e a producao quebra. O aviso vive aqui de proposito.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import digitarq  # noqa: E402


def fabricar_api(total, page_size=digitarq.SEARCH_PAGE, registo=None, repetir=False):
    """Devolve um substituto de _get_json que pagina por `fromIndex`."""
    def fake(session, url, params=None, delay=0):
        if registo is not None:
            registo.append(dict(params or {}))
        inicio = 0 if repetir else int((params or {}).get("fromIndex", 0))
        fim = min(inicio + page_size, total)
        return {
            "total": total,
            "results": [
                {"id": "guid%03d" % i,
                 "referenceCode": {"id": None, "value": "PT/TT/X/%03d" % i,
                                   "class": "E42_Identifier"},
                 "titles": "Titulo %d" % i,
                 "dateInitial": {"id": None, "value": None, "class": "E62_String"},
                 "dateFinal": None,
                 "filesCount": 284 if i == 0 else 0}
                for i in range(inicio, fim)
            ],
        }
    return fake


def test_pagina_ate_ao_total(monkeypatch):
    registo = []
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(43, registo=registo))
    res, total, notas = digitarq.search(None, "X", limit=100, sort="reference_code", delay=0)
    assert total == 43
    assert len(res) == 43
    assert len({r["id"] for r in res}) == 43, "sem repetidos"
    assert [p["fromIndex"] for p in registo] == [0, 10, 20, 30, 40]
    assert notas == []


def test_respeita_o_max_pedido(monkeypatch):
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(1000))
    res, total, _ = digitarq.search(None, "X", limit=25, sort="reference_code", delay=0)
    assert len(res) == 25 and total == 1000


def test_envia_sortfield_e_nao_envia_from_nem_page(monkeypatch):
    registo = []
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(5, registo=registo))
    digitarq.search(None, "X", sort="reference_code", order="asc", delay=0)
    p = registo[0]
    assert p["sortField"] == "reference_code" and p["sortOrder"] == "asc"
    assert p["fromIndex"] == 0 and p["max"] == digitarq.SEARCH_PAGE
    # `from`, `page` e `size` sao ignorados pelo servidor: mandar induz em erro.
    assert "from" not in p and "page" not in p and "size" not in p


def test_relevance_nao_manda_sortorder(monkeypatch):
    registo = []
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(5, registo=registo))
    digitarq.search(None, "X", sort="relevance", delay=0)
    assert "sortOrder" not in registo[0]


def test_with_images_e_filtro_no_servidor(monkeypatch):
    registo = []
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(5, registo=registo))
    digitarq.search(None, "X", with_images=True, delay=0)
    assert registo[0]["hasImages"] == "true"


def test_pagina_toda_repetida_para_em_vez_de_rodar_em_circulos(monkeypatch):
    """Ordenacao por relevancia pode devolver a mesma pagina; nao gastar pedidos."""
    registo = []
    monkeypatch.setattr(digitarq, "_get_json",
                        fabricar_api(100, registo=registo, repetir=True))
    res, total, notas = digitarq.search(None, "X", limit=100, sort="relevance", delay=0)
    assert len(res) == 10, "so os 10 unicos entram"
    assert len(registo) == 2, "para na segunda pagina, ao ver que nao progrediu"
    assert any("nao trouxe nenhum resultado novo" in n for n in notas)


def test_total_que_muda_a_meio_e_denunciado(monkeypatch):
    chamadas = {"n": 0}

    def fake(session, url, params=None, delay=0):
        chamadas["n"] += 1
        total = 20 if chamadas["n"] == 1 else 30
        inicio = int((params or {}).get("fromIndex", 0))
        return {"total": total,
                "results": [{"id": "g%d" % i, "filesCount": 0}
                            for i in range(inicio, min(inicio + 10, 30))]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    _, total, notas = digitarq.search(None, "X", limit=100, sort="reference_code", delay=0)
    assert total == 30
    assert any("total mudou durante a paginacao" in n for n in notas)


def test_teto_duro(monkeypatch):
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(10000))
    res, _, notas = digitarq.search(None, "X", limit=99999, sort="reference_code", delay=0)
    assert len(res) == digitarq.HARD_CAP
    assert any("teto" in n for n in notas)


def test_sort_invalido_e_recusado(monkeypatch):
    monkeypatch.setattr(digitarq, "_get_json", fabricar_api(1))
    with pytest.raises(digitarq.DigitarqError):
        digitarq.search(None, "X", sort="inventado", delay=0)


# --------------------------------------------------------------------------- #
# Formatacao dos campos
# --------------------------------------------------------------------------- #
def test_filescount_e_a_contagem_e_nao_um_sim_nao():
    """A busca nao devolve `hasImages`; procurar por ela imprimia sempre "nao"."""
    assert digitarq._files_label({"filesCount": 284}) == "284"
    assert digitarq._files_label({"filesCount": 0}) == "0"
    assert digitarq._files_label({}) == "?", "campo ausente e desconhecido, nao zero"


def test_data_toda_nula_nao_despeja_json():
    nula = {"id": None, "value": None, "class": "E62_String"}
    assert digitarq._flatten_date(nula) == ""
    assert "{" not in digitarq._datas_of({"dateInitial": nula, "dateFinal": nula})
    assert digitarq._datas_of({"dateInitial": nula, "dateFinal": nula}) == "s/data"


def test_flatten_date_mantem_displayvalue():
    """Campo que a versao anterior ja tratava e que nao pode regredir."""
    assert digitarq._flatten_date({"displayValue": "1700"}) == "1700"
    assert digitarq._flatten_date({"value": "1701"}) == "1701"


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
class RespostaFalsa:
    ok = True
    status_code = 200

    def __init__(self, corpo, ctype):
        self._corpo = corpo
        self.headers = {"Content-Type": ctype}

    def iter_content(self, chunk_size=65536):
        for i in range(0, len(self._corpo), chunk_size):
            yield self._corpo[i:i + chunk_size]


def preparar_download(monkeypatch, corpo, ctype):
    class SessaoFalsa:
        def get(self, *a, **k):
            return RespostaFalsa(corpo, ctype)
    monkeypatch.setattr(digitarq, "_session", lambda: SessaoFalsa())


class Args:
    def __init__(self, **kw):
        self.file_id = "1"
        self.thumb = False
        self.force = False
        self.saida = None
        self.__dict__.update(kw)


def test_html_de_erro_nao_e_gravado(monkeypatch, tmp_path):
    destino = tmp_path / "folio.jpg"
    preparar_download(monkeypatch, b"<html>manutencao</html>", "text/html")
    with pytest.raises(digitarq.DigitarqError) as e:
        digitarq.cmd_download(Args(saida=str(destino)))
    assert "nao e uma imagem" in str(e.value)
    assert not destino.exists(), "nada pode ser escrito quando a resposta nao e imagem"


def test_corpo_sem_assinatura_de_imagem_com_http_200(monkeypatch, tmp_path):
    """Portal cativo devolve 200 com corpo qualquer; raise_for_status nao apanha."""
    destino = tmp_path / "folio.jpg"
    preparar_download(monkeypatch, b"nao sou uma imagem", "application/octet-stream")
    with pytest.raises(digitarq.DigitarqError):
        digitarq.cmd_download(Args(saida=str(destino)))
    assert not destino.exists()


def test_ficheiro_bom_existente_nao_e_destruido(monkeypatch, tmp_path):
    destino = tmp_path / "folio.jpg"
    destino.write_bytes(b"\xff\xd8\xff" + b"imagem boa que ja estava aqui")
    antes = destino.read_bytes()
    preparar_download(monkeypatch, b"<html>erro</html>", "text/html")
    with pytest.raises(digitarq.DigitarqError):
        digitarq.cmd_download(Args(saida=str(destino), force=True))
    assert destino.read_bytes() == antes, "o ficheiro anterior tem de sobreviver"


def test_nao_sobrescreve_sem_force(monkeypatch, tmp_path):
    destino = tmp_path / "folio.jpg"
    destino.write_bytes(b"\xff\xd8\xffja existo")
    preparar_download(monkeypatch, b"\xff\xd8\xffnovo", "image/jpeg")
    with pytest.raises(digitarq.DigitarqError) as e:
        digitarq.cmd_download(Args(saida=str(destino)))
    assert "ja existe" in str(e.value)


def test_jpeg_valido_e_gravado(monkeypatch, tmp_path, capsys):
    destino = tmp_path / "folio.jpg"
    corpo = b"\xff\xd8\xff" + b"\x00" * 1000
    preparar_download(monkeypatch, corpo, "image/jpeg")
    digitarq.cmd_download(Args(saida=str(destino)))
    assert destino.read_bytes() == corpo
    assert not (tmp_path / "folio.jpg.part").exists(), "temporario tem de sumir"


# --------------------------------------------------------------------------- #
# images
# --------------------------------------------------------------------------- #
def test_images_pagina_alem_de_500(monkeypatch):
    def fake(session, url, params=None, delay=0):
        inicio = int((params or {}).get("fromIndex", 0))
        fim = min(inicio + 500, 1200)
        return {"fromIndex": inicio, "total": 1200,
                "results": [{"id": i, "name": "m%04d.jpg" % i} for i in range(inicio, fim)]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    imgs, total = digitarq.list_images(None, "guid", delay=0)
    assert total == 1200 and len(imgs) == 1200, "livro grande nao pode perder o fim"



@pytest.mark.parametrize("offset", [None, -1, True, 1.5, "incerto", 0])
def test_images_recusa_offset_ausente_invalido_ou_ignorado(monkeypatch, offset):
    def fake(*args, **kwargs):
        return {"fromIndex": offset, "total": 10, "results": [{"id": "x"}]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    with pytest.raises(digitarq.DigitarqError):
        digitarq.list_images(None, "guid", start=5, limit=1, delay=0)


def test_images_lote_parcial_avanca_pela_quantidade_recebida(monkeypatch):
    pedidos = []

    def fake(session, url, params=None, delay=0):
        pedidos.append(params)
        inicio = params["fromIndex"]
        quantidade = min(2, params["max"], 10 - inicio)
        return {"fromIndex": inicio, "total": 10,
                "results": [{"id": i} for i in range(inicio, inicio + quantidade)]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    imgs, total = digitarq.list_images(None, "guid", start=3, limit=5, delay=0)
    assert [i["id"] for i in imgs] == [3, 4, 5, 6, 7]
    assert total == 10
    assert [p["fromIndex"] for p in pedidos] == [3, 5, 7]
    assert [p["max"] for p in pedidos] == [5, 3, 1]
    assert all("from" not in p for p in pedidos)


@pytest.mark.parametrize("modo", ["repetidos", "vazia", "total_alterado", "sem_id"])
def test_images_contrato_incompleto_nao_vira_cobertura(monkeypatch, modo):
    chamadas = []

    def fake(session, url, params=None, delay=0):
        offset = params["fromIndex"]
        chamadas.append(offset)
        if offset == 0:
            return {"fromIndex": 0, "total": 4, "results": [{"id": "a"}, {"id": "b"}]}
        results = [{"id": "a"}] if modo == "repetidos" else (
            [] if modo == "vazia" else [{"name": "sem id"}] if modo == "sem_id"
            else [{"id": "c"}])
        return {"fromIndex": offset, "total": 5 if modo == "total_alterado" else 4,
                "results": results}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    with pytest.raises(digitarq.DigitarqError):
        digitarq.list_images(None, "guid", delay=0)
    assert chamadas == [0, 2]


def test_images_cli_nao_emite_json_parcial_em_erro(monkeypatch, capsys):
    def fake(session, url, params=None, delay=0):
        return {"fromIndex": 0, "total": 2, "results": [{"id": 1}]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    assert digitarq.main(["images", "guid", "--json", "--delay", "0"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "fromIndex" in output.err


def test_images_cli_preserva_inicio_do_lote(monkeypatch, capsys):
    import json

    def fake(session, url, params=None, delay=0):
        return {"fromIndex": 5, "total": 10, "results": [{"id": 6}]}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    assert digitarq.main(["images", "guid", "--start", "5", "--max", "1", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {"fromIndex": 5, "total": 10, "returned": 1, "results": [{"id": 6}]}


@pytest.mark.parametrize("start, limit", [(-1, 1), (0, 0), (0, -1)])
def test_images_valida_limites_antes_de_contactar_rede(monkeypatch, start, limit):
    def fake(*args, **kwargs):
        pytest.fail("nao deve contactar rede")
    monkeypatch.setattr(digitarq, "_get_json", fake)
    with pytest.raises(digitarq.DigitarqError):
        digitarq.list_images(None, "guid", start=start, limit=limit)


def test_images_lote_vazio_apos_fim_preserva_total(monkeypatch):
    def fake(*args, **kwargs):
        return {"fromIndex": 8, "total": 5, "results": []}
    monkeypatch.setattr(digitarq, "_get_json", fake)
    assert digitarq.list_images(None, "guid", start=8, delay=0) == ([], 5)
