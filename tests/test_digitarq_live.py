"""Teste LIVE contra a API real do DigitArq. Desligado por omissao.

Existe porque o resto da suite nao pode provar a unica coisa que realmente
importa aqui: que o servidor do ANTT continua a aceitar `fromIndex`, `sortField`
e `hasImages`, e que `filesCount` continua a ser a contagem de ficheiros. Os
testes com substitutos pressupoem esse contrato; se ele mudar, eles ficam verdes
e a producao quebra em silencio.

Nao corre no CI, de proposito: um servico publico nao deve levar pedidos a cada
push, e um teste que depende de rede transforma falha do ANTT em build vermelho.
Corra-o a mao antes de mexer no digitarq.py e antes de uma release:

    DIGITARQ_LIVE=1 pytest -q -m live

Custo: cerca de 8 pedidos, com pausa entre eles.

Contrato verificado a mao em 07/09/2026. Se este teste falhar, a API mudou:
actualize o codigo E a data em references/01-portugal-torre-do-tombo-digitarq.md.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import digitarq  # noqa: E402

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("DIGITARQ_LIVE") != "1",
                       reason="teste live: defina DIGITARQ_LIVE=1 para o correr"),
]

# Cota pequena e estavel, usada so como amostra. Nao tem ligacao a familia alguma.
COTA = "PT/TT/PRQ/PLSB01/004"


@pytest.fixture(scope="module")
def sessao():
    return digitarq._session()


def test_paginacao_ordenada_e_integra(sessao):
    """Com ordem estavel, a uniao das paginas tem de dar o total, sem repetidos."""
    res, total, notas = digitarq.search(sessao, COTA, limit=digitarq.HARD_CAP,
                                        sort="reference_code", order="asc", delay=1.0)
    assert total is not None and total > digitarq.SEARCH_PAGE, "cota pequena demais para o teste"
    ids = [r["id"] for r in res]
    assert len(ids) == len(set(ids)), "paginacao ordenada nao pode repetir"
    assert len(ids) == total, "paginacao ordenada tem de trazer o total"
    assert notas == []


def test_sortfield_invalido_e_recusado_pelo_servidor(sessao):
    """Se isto deixar de dar erro, o servidor passou a ignorar o parametro."""
    with pytest.raises(digitarq.DigitarqError):
        digitarq._get_json(sessao, digitarq.SEARCH_URL,
                           params={"query": COTA, "objType": "DOCUMENT",
                                   "sortField": "campo_que_nao_existe"}, delay=1.0)


def test_hasimages_filtra_do_lado_do_servidor(sessao):
    """O filtro tem de reduzir o total, senao esta a ser ignorado."""
    _, total_todos, _ = digitarq.search(sessao, COTA, limit=1,
                                        sort="reference_code", delay=1.0)
    _, total_com_img, _ = digitarq.search(sessao, COTA, limit=1, sort="reference_code",
                                          with_images=True, delay=1.0)
    assert total_com_img is not None and total_todos is not None
    assert total_com_img < total_todos, "hasImages=true nao esta a filtrar"


def test_filescount_bate_com_o_numero_real_de_imagens(sessao):
    """A ponte entre o que a busca DIZ e o que o endpoint de imagens ENTREGA.

    E a suposicao mais fragil do cliente: `filesCount` e usado como sinal de
    "ha digitalizacao". Aqui confirma-se contra a contagem real e contra o
    `hasImages` do details, que e a chave autoritativa.
    """
    res, _, _ = digitarq.search(sessao, COTA, limit=10, sort="reference_code",
                                with_images=True, delay=1.0)
    alvo = next((r for r in res if (r.get("filesCount") or 0) > 0), None)
    assert alvo is not None, "nenhum resultado com filesCount > 0"

    imagens, total_imgs = digitarq.list_images(sessao, alvo["id"], delay=1.0)
    assert total_imgs == alvo["filesCount"], (
        "filesCount (%s) nao bate com o total de imagens (%s)"
        % (alvo["filesCount"], total_imgs))
    assert len(imagens) == total_imgs, "list_images nao trouxe tudo"

    detalhe = digitarq._get_json(sessao, digitarq.DETAILS_URL.format(guid=alvo["id"]),
                                 delay=1.0)
    assert detalhe.get("hasImages") is True, "details discorda da busca"
